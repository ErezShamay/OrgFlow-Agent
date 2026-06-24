from __future__ import annotations

import base64
import logging
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import resend

from app.config.settings import settings
from app.lib.email_validation import is_valid_email, normalize_email
from app.repositories.project_apartment_repository import (
    ProjectApartmentRepository,
    build_apartment_group_key,
)
from app.schemas.field_report_finalize import FinalizeEmailStatus
from app.services.field_report_project_prefill import stakeholders_from_project
from app.services.field_visit_report_pdf_service import FieldVisitReportPdfService

logger = logging.getLogger(__name__)

DEFAULT_FROM_ADDRESS = "OrgFlow <onboarding@resend.dev>"
EMAIL_FINALIZE_STEP_ORDER: tuple[str, ...] = (
    "E01",
    "E02",
    "E03",
    "E04",
    "E05",
)
MAX_EMAIL_ATTEMPTS = 3
EMAIL_RETRY_DELAY_SECONDS = 0.5

_STAKEHOLDER_EMAIL_FIELDS: tuple[tuple[str, str], ...] = (
    ("developer", "developer_email"),
    ("project_manager", "developer_pm_email"),
    ("site_manager", "site_manager_email"),
    ("contractor", "contractor_email"),
    ("lawyer_tenants", "lawyer_email"),
    ("lawyer_accompanying", "accompanying_lawyer_email"),
    ("architect", "architect_email"),
)


@dataclass(frozen=True)
class FinalizeEmailRecipient:
    email: str
    source: str
    label: str | None = None


@dataclass(frozen=True)
class FinalizeEmailDispatchResult:
    email_status: FinalizeEmailStatus
    email_sent_at: str | None
    steps_completed: list[str]
    step_summaries: dict[str, dict[str, Any]]
    recipients: list[dict[str, Any]]
    attempts: int
    error_message: str | None = None


class FieldReportFinalizeEmailService:
    def __init__(
        self,
        *,
        apartment_repository: ProjectApartmentRepository | None = None,
        pdf_service: FieldVisitReportPdfService | None = None,
        resend_sender: Any | None = None,
    ) -> None:
        self.apartment_repository = (
            apartment_repository or ProjectApartmentRepository()
        )
        self.pdf_service = pdf_service or FieldVisitReportPdfService()
        self._resend_sender = resend_sender

    def dispatch_after_core_steps(
        self,
        *,
        organization_id: str,
        project_id: str,
        report_id: str,
        record: dict,
        source_content: bytes,
        source_filename: str,
        line_group_keys: set[str],
    ) -> FinalizeEmailDispatchResult:
        summaries: dict[str, dict[str, Any]] = {}
        completed_steps: list[str] = []

        if organization_id != str(record.get("organization_id") or ""):
            summaries["E04"] = {
                "scoped": False,
                "reason": "organization_mismatch",
            }
            return FinalizeEmailDispatchResult(
                email_status=FinalizeEmailStatus.FAILED,
                email_sent_at=None,
                steps_completed=completed_steps,
                step_summaries=summaries,
                recipients=[],
                attempts=0,
                error_message="organization scope mismatch",
            )

        if str(record.get("project_id") or "") != project_id:
            summaries["E04"] = {
                "scoped": False,
                "reason": "project_mismatch",
            }
            return FinalizeEmailDispatchResult(
                email_status=FinalizeEmailStatus.FAILED,
                email_sent_at=None,
                steps_completed=completed_steps,
                step_summaries=summaries,
                recipients=[],
                attempts=0,
                error_message="project scope mismatch",
            )

        summaries["E04"] = {
            "scoped": True,
            "organization_id": organization_id,
            "project_id": project_id,
        }
        completed_steps.append("E04")

        feature_enabled = settings.FEATURE_FLAGS.enable_email_delivery
        summaries["E05"] = {
            "feature_email_delivery": feature_enabled,
        }
        completed_steps.append("E05")

        if not feature_enabled:
            summaries["E01"] = {"status": FinalizeEmailStatus.QUEUED.value}
            completed_steps.append("E01")
            return FinalizeEmailDispatchResult(
                email_status=FinalizeEmailStatus.QUEUED,
                email_sent_at=None,
                steps_completed=completed_steps,
                step_summaries=summaries,
                recipients=[],
                attempts=0,
            )

        project = record.get("_project") or {}
        residents = self._collect_resident_recipients(
            organization_id=organization_id,
            project_id=project_id,
            line_group_keys=line_group_keys,
        )
        summaries["E02"] = {
            "recipient_count": len(residents),
            "recipients": [item.email for item in residents],
        }
        completed_steps.append("E02")

        stakeholders = self._collect_stakeholder_recipients(
            project=project,
            header_fields=record.get("header_fields") or {},
        )
        summaries["E03"] = {
            "recipient_count": len(stakeholders),
            "recipients": [item.email for item in stakeholders],
        }
        completed_steps.append("E03")

        recipients = self._dedupe_recipients(residents + stakeholders)
        if not recipients:
            summaries["E01"] = {
                "status": FinalizeEmailStatus.FAILED.value,
                "reason": "no_recipients",
            }
            completed_steps.append("E01")
            return FinalizeEmailDispatchResult(
                email_status=FinalizeEmailStatus.FAILED,
                email_sent_at=None,
                steps_completed=completed_steps,
                step_summaries=summaries,
                recipients=[],
                attempts=0,
                error_message="no email recipients configured for project",
            )

        pdf_bytes, attachment_name = self._load_pdf_attachment(
            record=record,
            source_content=source_content,
            source_filename=source_filename,
        )
        subject, body = self._build_message(
            record=record,
            project=project,
            recipient_count=len(recipients),
        )

        last_error: str | None = None
        for attempt in range(1, MAX_EMAIL_ATTEMPTS + 1):
            try:
                self._send_with_attachment(
                    recipients=recipients,
                    subject=subject,
                    body=body,
                    pdf_bytes=pdf_bytes,
                    attachment_name=attachment_name,
                )
                sent_at = datetime.now(UTC).isoformat()
                summaries["E01"] = {
                    "status": FinalizeEmailStatus.SENT.value,
                    "attempts": attempt,
                    "recipient_count": len(recipients),
                    "attachment_filename": attachment_name,
                    "attachment_bytes": len(pdf_bytes),
                }
                completed_steps.append("E01")
                return FinalizeEmailDispatchResult(
                    email_status=FinalizeEmailStatus.SENT,
                    email_sent_at=sent_at,
                    steps_completed=completed_steps,
                    step_summaries=summaries,
                    recipients=[
                        {
                            "email": item.email,
                            "source": item.source,
                            "label": item.label,
                        }
                        for item in recipients
                    ],
                    attempts=attempt,
                )
            except Exception as error:
                last_error = str(error)
                logger.warning(
                    "Finalize email dispatch attempt failed",
                    extra={
                        "report_id": report_id,
                        "attempt": attempt,
                        "error": last_error,
                    },
                )
                if attempt < MAX_EMAIL_ATTEMPTS:
                    time.sleep(EMAIL_RETRY_DELAY_SECONDS)

        summaries["E01"] = {
            "status": FinalizeEmailStatus.FAILED.value,
            "attempts": MAX_EMAIL_ATTEMPTS,
            "error": last_error,
        }
        completed_steps.append("E01")
        return FinalizeEmailDispatchResult(
            email_status=FinalizeEmailStatus.FAILED,
            email_sent_at=None,
            steps_completed=completed_steps,
            step_summaries=summaries,
            recipients=[
                {
                    "email": item.email,
                    "source": item.source,
                    "label": item.label,
                }
                for item in recipients
            ],
            attempts=MAX_EMAIL_ATTEMPTS,
            error_message=last_error,
        )

    def _collect_resident_recipients(
        self,
        *,
        organization_id: str,
        project_id: str,
        line_group_keys: set[str],
    ) -> list[FinalizeEmailRecipient]:
        apartments = self.apartment_repository.list_by_project(project_id)
        apartment_keys = {
            key
            for key in line_group_keys
            if key.startswith("apartment:")
        }
        includes_shared = any(
            not key or not key.startswith("apartment:")
            for key in line_group_keys
        ) or not line_group_keys

        recipients: list[FinalizeEmailRecipient] = []
        for apartment in apartments:
            if str(apartment.get("organization_id") or "") != organization_id:
                continue

            email = self._normalize_email(apartment.get("email"))
            if not email:
                continue

            group_key = str(apartment.get("group_key") or "").strip()
            if not group_key:
                apartment_number = str(
                    apartment.get("apartment_number") or ""
                ).strip()
                if apartment_number:
                    group_key = build_apartment_group_key(apartment_number)

            if apartment_keys:
                if group_key not in apartment_keys:
                    if not (includes_shared and not group_key):
                        continue
            elif not includes_shared:
                continue

            recipients.append(
                FinalizeEmailRecipient(
                    email=email,
                    source="resident",
                    label=str(apartment.get("owner_name") or "").strip()
                    or None,
                )
            )

        return recipients

    def _collect_stakeholder_recipients(
        self,
        *,
        project: dict,
        header_fields: dict,
    ) -> list[FinalizeEmailRecipient]:
        recipients: list[FinalizeEmailRecipient] = []
        seen_roles: set[str] = set()

        for role, field_name in _STAKEHOLDER_EMAIL_FIELDS:
            email = self._normalize_email(project.get(field_name))
            if not email:
                continue
            seen_roles.add(role)
            recipients.append(
                FinalizeEmailRecipient(
                    email=email,
                    source="stakeholder",
                    label=role,
                )
            )

        stakeholder_emails = project.get("stakeholder_emails")
        if isinstance(stakeholder_emails, dict):
            for role, email_value in stakeholder_emails.items():
                role_key = str(role).strip()
                email = self._normalize_email(email_value)
                if not email or role_key in seen_roles:
                    continue
                seen_roles.add(role_key)
                recipients.append(
                    FinalizeEmailRecipient(
                        email=email,
                        source="stakeholder",
                        label=role_key,
                    )
                )

        header_stakeholders = header_fields.get("stakeholders")
        if isinstance(header_stakeholders, list):
            for item in header_stakeholders:
                if not isinstance(item, dict):
                    continue
                role = str(item.get("role") or "").strip()
                email = self._normalize_email(item.get("email"))
                if not email or role in seen_roles:
                    continue
                seen_roles.add(role)
                recipients.append(
                    FinalizeEmailRecipient(
                        email=email,
                        source="stakeholder",
                        label=role or str(item.get("name") or "").strip()
                        or None,
                    )
                )

        for stakeholder in stakeholders_from_project(project):
            role = str(stakeholder.get("role") or "").strip()
            if role in seen_roles:
                continue
            email = self._normalize_email(stakeholder.get("email"))
            if not email:
                continue
            seen_roles.add(role)
            recipients.append(
                FinalizeEmailRecipient(
                    email=email,
                    source="stakeholder",
                    label=role,
                )
            )

        return recipients

    @staticmethod
    def _dedupe_recipients(
        recipients: list[FinalizeEmailRecipient],
    ) -> list[FinalizeEmailRecipient]:
        deduped: list[FinalizeEmailRecipient] = []
        seen: set[str] = set()
        for recipient in recipients:
            key = recipient.email.casefold()
            if key in seen:
                continue
            seen.add(key)
            deduped.append(recipient)
        return deduped

    def _load_pdf_attachment(
        self,
        *,
        record: dict,
        source_content: bytes,
        source_filename: str,
    ) -> tuple[bytes, str]:
        storage_path = str(record.get("pdf_storage_path") or "").strip()
        filename = (
            str(record.get("pdf_filename") or "").strip()
            or source_filename
            or "field-report.pdf"
        )

        if storage_path:
            try:
                pdf_bytes, _ = self.pdf_service.read_pdf(storage_path)
                return pdf_bytes, filename
            except FileNotFoundError:
                pass

        if source_content:
            return source_content, filename

        raise FileNotFoundError("PDF attachment is not available for email")

    def _build_message(
        self,
        *,
        record: dict,
        project: dict,
        recipient_count: int,
    ) -> tuple[str, str]:
        project_name = str(
            project.get("project_name") or record.get("project_id") or "הפרויקט"
        ).strip()
        visit_date = str(record.get("visit_date") or "").strip()
        title = str(record.get("title") or "דוח ביקור שטח").strip()
        finding_count = int(record.get("_finding_count") or 0)

        subject = f"דוח ביקור — {project_name}"
        if visit_date:
            subject = f"{subject} ({visit_date})"

        body_lines = [
            "שלום,",
            "",
            f"מצורף דוח ביקור שטח עבור פרויקט {project_name}.",
            f"כותרת: {title}",
        ]
        if visit_date:
            body_lines.append(f"תאריך ביקור: {visit_date}")
        if finding_count:
            body_lines.append(f"מספר ממצאים: {finding_count}")
        body_lines.extend(
            [
                "",
                "הדוח מצורף למייל זה בפורמט PDF.",
                "ניתן לצפות בדוחות נוספים בפורטל הרוכש.",
                "",
                "בברכה,",
                "צוות OrgFlow",
            ]
        )
        if recipient_count > 1:
            body_lines.insert(
                3,
                f"הודעה זו נשלחה ל-{recipient_count} נמענים בפרויקט.",
            )

        return subject, "\n".join(body_lines)

    def _send_with_attachment(
        self,
        *,
        recipients: list[FinalizeEmailRecipient],
        subject: str,
        body: str,
        pdf_bytes: bytes,
        attachment_name: str,
    ) -> dict:
        if not settings.RESEND_API_KEY:
            raise RuntimeError("RESEND_API_KEY is not configured")

        sender = self._resend_sender
        if sender is None:
            resend.api_key = settings.RESEND_API_KEY
            sender = resend.Emails.send

        payload = {
            "from": DEFAULT_FROM_ADDRESS,
            "to": [recipient.email for recipient in recipients],
            "subject": subject,
            "text": body,
            "attachments": [
                {
                    "filename": attachment_name,
                    "content": base64.b64encode(pdf_bytes).decode("ascii"),
                }
            ],
        }
        return sender(payload)

    @staticmethod
    def _normalize_email(value: Any) -> str | None:
        if value is None:
            return None
        email = str(value).strip()
        if not email:
            return None
        if not is_valid_email(email):
            return None
        return normalize_email(email)
