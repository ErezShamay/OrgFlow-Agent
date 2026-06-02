from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from tempfile import NamedTemporaryFile

from app.config.field_report_visit_types import (
    allowed_top_families,
    is_valid_visit_type,
    list_visit_types,
)
from app.exceptions.exceptions import (
    ConflictError,
    NotFoundError,
    ValidationError,
)
from app.repositories.field_visit_report_line_repository import (
    FieldVisitReportLineRepository,
)
from app.repositories.field_visit_report_repository import (
    FieldVisitReportRepository,
)
from app.repositories.project_repository import (
    ProjectRepository,
)
from app.services.field_report_catalog_service import (
    FieldReportCatalogService,
)
from app.services.field_report_organization_profile_service import (
    FieldReportOrganizationProfileService,
)
from app.services.field_visit_report_photo_service import (
    FieldVisitReportPhotoService,
)
from app.services.report_processing_service import (
    ReportProcessingService,
)

VISIT_STATUS_LABELS_HE: dict[str, str] = {
    "IN_PROGRESS": "בעבודה",
    "CLOSED": "סגור",
    "PENDING_UPLOAD": "ממתין לשליחה",
    "LOCKED": "נעול",
}

EDITABLE_STATUSES = frozenset({"IN_PROGRESS"})
REOPENABLE_STATUSES = frozenset({"CLOSED"})
SENDABLE_STATUSES = frozenset({"CLOSED"})
OFFLINE_MAX_DAYS = 7


class FieldVisitReportService:
    def __init__(
        self,
        report_repository:
            FieldVisitReportRepository | None = None,
        line_repository:
            FieldVisitReportLineRepository | None = None,
        project_repository:
            ProjectRepository | None = None,
        organization_profile_service:
            FieldReportOrganizationProfileService | None = None,
        catalog_service:
            FieldReportCatalogService | None = None,
        photo_service:
            FieldVisitReportPhotoService | None = None,
        report_processing_service:
            ReportProcessingService | None = None,
    ) -> None:
        self.report_repository = (
            report_repository or FieldVisitReportRepository()
        )
        self.line_repository = (
            line_repository or FieldVisitReportLineRepository()
        )
        self.project_repository = (
            project_repository or ProjectRepository()
        )
        self.organization_profile_service = (
            organization_profile_service
            or FieldReportOrganizationProfileService()
        )
        self.catalog_service = (
            catalog_service or FieldReportCatalogService()
        )
        self.photo_service = (
            photo_service or FieldVisitReportPhotoService()
        )
        self.report_processing_service = (
            report_processing_service or ReportProcessingService()
        )

    def is_storage_available(self) -> bool:
        return self.report_repository.is_storage_available()

    def are_lines_available(self) -> bool:
        return self.line_repository.is_storage_available()

    def get_visit_types(self) -> dict:
        catalog = self.catalog_service.get_catalog_summary()
        return {
            "visit_types": list_visit_types(),
            "storage_available": self.is_storage_available(),
            "lines_storage_available": self.are_lines_available(),
            "catalog_version": catalog.get("catalog_version"),
            "catalog_issue_count": catalog.get("issue_count"),
            "catalog_errors": catalog.get("errors"),
        }

    def get_catalog(
        self,
        *,
        visit_type: str | None = None,
    ) -> dict:
        if visit_type:
            if not is_valid_visit_type(visit_type):
                raise ValidationError(
                    message="סוג ביקור לא תקין",
                    details={"visit_type": visit_type},
                )
            return self.catalog_service.get_catalog_for_visit_type(
                visit_type
            )
        return self.catalog_service.get_full_catalog()

    def build_offline_prep_bundle(
        self,
        organization_id: str,
    ) -> dict:
        if not self.is_storage_available():
            raise ValidationError(
                message=(
                    "טבלת דוחות ביקור אינה מוגדרת במסד הנתונים. "
                    "יש להריץ את המיגרציה "
                    "db/migrations/2026060102_field_visit_reports.sql"
                ),
            )

        projects = self.project_repository.get_projects_by_organization(
            organization_id
        )
        organization_profile = (
            self.organization_profile_service.get_profile(
                organization_id,
                require_module=False,
            )
        )
        catalog = self.catalog_service.get_full_catalog()

        return {
            "organization_id": organization_id,
            "offline_max_days": OFFLINE_MAX_DAYS,
            "catalog_version": catalog.get("catalog_version"),
            "catalog": catalog,
            "visit_types": list_visit_types(),
            "organization_profile": organization_profile,
            "projects": [
                {
                    "id": str(project["id"]),
                    "project_name": project.get("project_name"),
                    "city": project.get("city"),
                    "developer_name": project.get("developer_name"),
                    "contractor_name": project.get("contractor_name"),
                    "lawyer_name": project.get("lawyer_name"),
                    "project_type": project.get("project_type"),
                }
                for project in projects
            ],
            "reports": self.list_reports(organization_id)["reports"],
            "lines_storage_available": self.are_lines_available(),
        }

    def list_reports(
        self,
        organization_id: str,
        *,
        status: str | None = None,
        project_names: dict[str, str] | None = None,
    ) -> dict:
        if not self.is_storage_available():
            raise ValidationError(
                message=(
                    "טבלת דוחות ביקור אינה מוגדרת במסד הנתונים. "
                    "יש להריץ את המיגרציה "
                    "db/migrations/2026060102_field_visit_reports.sql"
                ),
            )

        records = self.report_repository.list_by_organization(
            organization_id,
            status=status,
        )

        return {
            "reports": [
                self._serialize_report(
                    record,
                    project_name=(
                        (project_names or {}).get(
                            str(record["project_id"])
                        )
                    ),
                    include_lines=False,
                )
                for record in records
            ],
            "total": len(records),
        }

    def get_report(
        self,
        *,
        organization_id: str,
        report_id: str,
        project_name: str | None = None,
        include_lines: bool = True,
    ) -> dict:
        record = self._get_org_report(
            organization_id=organization_id,
            report_id=report_id,
        )

        if project_name is None:
            project = self.project_repository.get_project_by_id(
                str(record["project_id"])
            )
            if project:
                project_name = project.get("project_name")

        return self._serialize_report(
            record,
            project_name=project_name,
            include_lines=include_lines,
        )

    def create_report(
        self,
        *,
        organization_id: str,
        actor_profile_id: str,
        project_id: str,
        visit_type: str,
        visit_date: str,
        header_fields: dict | None = None,
        catalog_version: str | None = None,
        snapshot_organization_profile: bool = True,
    ) -> dict:
        if not self.is_storage_available():
            raise ValidationError(
                message=(
                    "טבלת דוחות ביקור אינה מוגדרת במסד הנתונים. "
                    "יש להריץ את המיגרציה "
                    "db/migrations/2026060102_field_visit_reports.sql"
                ),
            )

        if not is_valid_visit_type(visit_type):
            raise ValidationError(
                message="סוג ביקור לא תקין",
                details={"visit_type": visit_type},
            )

        project = self.project_repository.get_project_by_id(
            project_id
        )

        if not project:
            raise NotFoundError(
                message="Project not found",
                resource_type="project",
                resource_id=project_id,
            )

        if str(project.get("organization_id")) != organization_id:
            raise NotFoundError(
                message="Project not found",
                resource_type="project",
                resource_id=project_id,
            )

        existing = self.report_repository.get_open_for_project(
            organization_id=organization_id,
            project_id=project_id,
        )

        if existing:
            raise ConflictError(
                message=(
                    "כבר קיים דוח בעבודה לפרויקט זה. "
                    "יש להמשיך את הדוח הקיים או לסגור אותו."
                ),
                details={
                    "existing_report_id": str(existing["id"]),
                    "project_id": project_id,
                },
            )

        profile_snapshot = None

        if snapshot_organization_profile:
            profile_snapshot = (
                self.organization_profile_service.get_profile(
                    organization_id,
                    require_module=False,
                )
            )

        merged_header_fields = _merge_header_fields(
            project,
            header_fields,
            visit_type=visit_type,
        )
        resolved_catalog_version = (
            catalog_version
            or self.catalog_service.get_catalog_summary().get(
                "catalog_version"
            )
        )

        record = self.report_repository.create(
            organization_id=organization_id,
            project_id=project_id,
            created_by_profile_id=actor_profile_id,
            visit_type=visit_type,
            visit_date=visit_date,
            header_fields=merged_header_fields,
            catalog_version=resolved_catalog_version,
            organization_profile_snapshot=profile_snapshot,
        )

        return self._serialize_report(
            record,
            project_name=project.get("project_name"),
        )

    def preview_close_report(
        self,
        *,
        organization_id: str,
        report_id: str,
    ) -> dict:
        record = self._get_org_report(
            organization_id=organization_id,
            report_id=report_id,
        )
        self._ensure_editable(record)

        current_catalog_version = (
            self.catalog_service.get_catalog_summary().get(
                "catalog_version"
            )
        )
        lines = self._load_lines(
            report_id,
            current_catalog_version=current_catalog_version,
        )
        return _build_close_preview(lines)

    def close_report(
        self,
        *,
        organization_id: str,
        report_id: str,
    ) -> dict:
        record = self._get_org_report(
            organization_id=organization_id,
            report_id=report_id,
        )
        self._ensure_editable(record)

        current_catalog_version = (
            self.catalog_service.get_catalog_summary().get(
                "catalog_version"
            )
        )
        lines = self._load_lines(
            report_id,
            current_catalog_version=current_catalog_version,
        )
        close_preview = _build_close_preview(lines)

        updated = self.report_repository.update(
            report_id,
            {
                "status": "CLOSED",
                "closed_at": datetime.now(UTC).isoformat(),
            },
        )

        if not updated:
            raise NotFoundError(
                message="Field visit report not found",
                resource_type="field_visit_report",
                resource_id=report_id,
            )

        project = self.project_repository.get_project_by_id(
            str(record["project_id"])
        )
        project_name = (
            project.get("project_name") if project else None
        )

        serialized = self._serialize_report(
            updated,
            project_name=project_name,
        )
        return {
            **serialized,
            "close_preview": close_preview,
        }

    def reopen_report(
        self,
        *,
        organization_id: str,
        report_id: str,
    ) -> dict:
        record = self._get_org_report(
            organization_id=organization_id,
            report_id=report_id,
        )
        status = str(record.get("status") or "")

        if status not in REOPENABLE_STATUSES:
            raise ConflictError(
                message="ניתן לערוך שוב רק דוח במצב סגור",
                details={"status": status},
            )

        project_id = str(record["project_id"])
        existing = self.report_repository.get_open_for_project(
            organization_id=organization_id,
            project_id=project_id,
        )

        if existing and str(existing["id"]) != report_id:
            raise ConflictError(
                message=(
                    "כבר קיים דוח בעבודה לפרויקט זה. "
                    "יש לסגור או לשלוח את הדוח הפתוח לפני עריכה מחדש."
                ),
                details={
                    "existing_report_id": str(existing["id"]),
                    "project_id": project_id,
                },
            )

        updated = self.report_repository.update(
            report_id,
            {"status": "IN_PROGRESS"},
        )

        if not updated:
            raise NotFoundError(
                message="Field visit report not found",
                resource_type="field_visit_report",
                resource_id=report_id,
            )

        project = self.project_repository.get_project_by_id(
            project_id
        )
        project_name = (
            project.get("project_name") if project else None
        )

        return self._serialize_report(
            updated,
            project_name=project_name,
        )

    def request_send_to_core(
        self,
        *,
        organization_id: str,
        report_id: str,
        source_filename: str,
        source_content: bytes,
    ) -> dict:
        record = self._get_org_report(
            organization_id=organization_id,
            report_id=report_id,
        )
        status = str(record.get("status") or "")

        project = self.project_repository.get_project_by_id(
            str(record["project_id"])
        )
        project_name = (
            project.get("project_name") if project else None
        )

        # 3D.4 idempotency:
        # If the report was already successfully sent (locked),
        # return the current report state instead of failing the retry.
        if status in {"LOCKED", "PENDING_UPLOAD"}:
            return self._serialize_report(
                record,
                project_name=project_name,
            )

        if status not in SENDABLE_STATUSES:
            raise ConflictError(
                message="ניתן לשלוח לליבה רק דוח במצב סגור",
                details={"status": status},
            )

        core_result = self._send_to_core_pipeline(
            record,
            source_filename=source_filename,
            source_content=source_content,
        )
        if not core_result.get("success"):
            raise ConflictError(
                message=(
                    core_result.get("error_message")
                    or "שליחה לליבה נכשלה"
                ),
                details={
                    "error_code": core_result.get(
                        "error_code",
                        "FIELD_VISIT_REPORT_CORE_SEND_FAILED",
                    ),
                },
            )

        # 3D.3: on successful network send request, lock the report.
        # (In this MVP implementation we treat the request as "server-approved".)
        updated = self.report_repository.update(
            report_id,
            {
                "status": "LOCKED",
                "locked_at": datetime.now(UTC).isoformat(),
            },
        )

        if not updated:
            raise NotFoundError(
                message="Field visit report not found",
                resource_type="field_visit_report",
                resource_id=report_id,
            )

        return self._serialize_report(
            updated,
            project_name=project_name,
        )

    def update_report(
        self,
        *,
        organization_id: str,
        report_id: str,
        visit_date: str | None = None,
        header_fields: dict | None = None,
        catalog_version: str | None = None,
    ) -> dict:
        record = self._get_org_report(
            organization_id=organization_id,
            report_id=report_id,
        )
        self._ensure_editable(record)

        payload: dict = {}

        if visit_date is not None:
            payload["visit_date"] = visit_date

        if header_fields is not None:
            payload["header_fields"] = {
                **(record.get("header_fields") or {}),
                **header_fields,
            }

        if catalog_version is not None:
            payload["catalog_version"] = catalog_version

        if not payload:
            return self.get_report(
                organization_id=organization_id,
                report_id=report_id,
            )

        updated = self.report_repository.update(report_id, payload)
        if not updated:
            raise NotFoundError(
                message="Field visit report not found",
                resource_type="field_visit_report",
                resource_id=report_id,
            )

        return self.get_report(
            organization_id=organization_id,
            report_id=report_id,
        )

    def list_lines(
        self,
        *,
        organization_id: str,
        report_id: str,
    ) -> dict:
        record = self._get_org_report(
            organization_id=organization_id,
            report_id=report_id,
        )
        current_catalog_version = self._current_catalog_version()
        lines = self._load_lines(
            str(record["id"]),
            current_catalog_version=current_catalog_version,
        )
        return {
            "lines": lines,
            "total": len(lines),
        }

    def create_line(
        self,
        *,
        organization_id: str,
        report_id: str,
        payload: dict,
    ) -> dict:
        if not self.are_lines_available():
            raise ValidationError(
                message=(
                    "טבלת שורות דוח אינה מוגדרת במסד הנתונים. "
                    "יש להריץ את המיגרציה "
                    "db/migrations/2026060103_field_visit_report_lines.sql"
                ),
            )

        record = self._get_org_report(
            organization_id=organization_id,
            report_id=report_id,
        )
        self._ensure_editable(record)

        line_payload = self._build_line_payload(
            record=record,
            incoming=payload,
            for_create=True,
        )

        created = self.line_repository.create(line_payload)
        return self._serialize_line(
            created,
            current_catalog_version=self._current_catalog_version(),
        )

    def update_line(
        self,
        *,
        organization_id: str,
        report_id: str,
        line_id: str,
        payload: dict,
    ) -> dict:
        if not self.are_lines_available():
            raise ValidationError(
                message=(
                    "טבלת שורות דוח אינה מוגדרת במסד הנתונים. "
                    "יש להריץ את המיגרציה "
                    "db/migrations/2026060103_field_visit_report_lines.sql"
                ),
            )

        record = self._get_org_report(
            organization_id=organization_id,
            report_id=report_id,
        )
        self._ensure_editable(record)

        existing = self._get_org_line(
            organization_id=organization_id,
            report_id=report_id,
            line_id=line_id,
        )

        update_payload = self._build_line_update_payload(
            record=record,
            existing=existing,
            incoming=payload,
        )

        current_catalog_version = self._current_catalog_version()
        if not update_payload:
            return self._serialize_line(
                existing,
                current_catalog_version=current_catalog_version,
            )

        updated = self.line_repository.update(line_id, update_payload)
        if not updated:
            raise NotFoundError(
                message="Field visit report line not found",
                resource_type="field_visit_report_line",
                resource_id=line_id,
            )

        return self._serialize_line(
            updated,
            current_catalog_version=current_catalog_version,
        )

    def delete_line(
        self,
        *,
        organization_id: str,
        report_id: str,
        line_id: str,
    ) -> dict:
        if not self.are_lines_available():
            raise ValidationError(
                message=(
                    "טבלת שורות דוח אינה מוגדרת במסד הנתונים. "
                    "יש להריץ את המיגרציה "
                    "db/migrations/2026060103_field_visit_report_lines.sql"
                ),
            )

        record = self._get_org_report(
            organization_id=organization_id,
            report_id=report_id,
        )
        self._ensure_editable(record)

        existing = self._get_org_line(
            organization_id=organization_id,
            report_id=report_id,
            line_id=line_id,
        )

        existing_photo = existing.get("photo_storage_path")
        if existing_photo:
            self.photo_service.delete_photo(str(existing_photo))

        self.line_repository.delete(line_id)
        return {"deleted": True, "id": line_id}

    def upload_line_photo(
        self,
        *,
        organization_id: str,
        report_id: str,
        line_id: str,
        content: bytes,
        content_type: str | None,
        filename: str | None = None,
    ) -> dict:
        if not self.are_lines_available():
            raise ValidationError(
                message=(
                    "טבלת שורות דוח אינה מוגדרת במסד הנתונים. "
                    "יש להריץ את המיגרציה "
                    "db/migrations/2026060103_field_visit_report_lines.sql"
                ),
            )

        record = self._get_org_report(
            organization_id=organization_id,
            report_id=report_id,
        )
        self._ensure_editable(record)

        existing = self._get_org_line(
            organization_id=organization_id,
            report_id=report_id,
            line_id=line_id,
        )

        previous_path = existing.get("photo_storage_path")
        storage_path = self.photo_service.save_photo(
            organization_id=organization_id,
            report_id=report_id,
            line_id=line_id,
            content=content,
            content_type=content_type,
            filename=filename,
        )

        updated = self.line_repository.update(
            line_id,
            {"photo_storage_path": storage_path},
        )
        if not updated:
            self.photo_service.delete_photo(storage_path)
            raise NotFoundError(
                message="Field visit report line not found",
                resource_type="field_visit_report_line",
                resource_id=line_id,
            )

        if previous_path and previous_path != storage_path:
            self.photo_service.delete_photo(str(previous_path))

        return self._serialize_line(updated)

    def get_line_photo(
        self,
        *,
        organization_id: str,
        report_id: str,
        line_id: str,
    ) -> tuple[bytes, str]:
        if not self.are_lines_available():
            raise ValidationError(
                message=(
                    "טבלת שורות דוח אינה מוגדרת במסד הנתונים. "
                    "יש להריץ את המיגרציה "
                    "db/migrations/2026060103_field_visit_report_lines.sql"
                ),
            )

        self._get_org_report(
            organization_id=organization_id,
            report_id=report_id,
        )
        existing = self._get_org_line(
            organization_id=organization_id,
            report_id=report_id,
            line_id=line_id,
        )

        storage_path = existing.get("photo_storage_path")
        if not storage_path:
            raise NotFoundError(
                message="Line photo not found",
                resource_type="field_visit_report_line_photo",
                resource_id=line_id,
            )

        try:
            return self.photo_service.read_photo(str(storage_path))
        except FileNotFoundError as error:
            raise NotFoundError(
                message="Line photo file not found",
                resource_type="field_visit_report_line_photo",
                resource_id=line_id,
            ) from error

    def delete_line_photo(
        self,
        *,
        organization_id: str,
        report_id: str,
        line_id: str,
    ) -> dict:
        if not self.are_lines_available():
            raise ValidationError(
                message=(
                    "טבלת שורות דוח אינה מוגדרת במסד הנתונים. "
                    "יש להריץ את המיגרציה "
                    "db/migrations/2026060103_field_visit_report_lines.sql"
                ),
            )

        record = self._get_org_report(
            organization_id=organization_id,
            report_id=report_id,
        )
        self._ensure_editable(record)

        existing = self._get_org_line(
            organization_id=organization_id,
            report_id=report_id,
            line_id=line_id,
        )

        previous_path = existing.get("photo_storage_path")
        if not previous_path:
            return self._serialize_line(existing)

        self.photo_service.delete_photo(str(previous_path))
        updated = self.line_repository.update(
            line_id,
            {"photo_storage_path": None},
        )
        if not updated:
            raise NotFoundError(
                message="Field visit report line not found",
                resource_type="field_visit_report_line",
                resource_id=line_id,
            )

        return self._serialize_line(updated)

    def _get_org_line(
        self,
        *,
        organization_id: str,
        report_id: str,
        line_id: str,
    ) -> dict:
        existing = self.line_repository.get_by_id(line_id)
        if (
            not existing
            or str(existing.get("report_id")) != report_id
            or str(existing.get("organization_id")) != organization_id
        ):
            raise NotFoundError(
                message="Field visit report line not found",
                resource_type="field_visit_report_line",
                resource_id=line_id,
            )
        return existing

    def _build_line_payload(
        self,
        *,
        record: dict,
        incoming: dict,
        for_create: bool,
    ) -> dict:
        visit_type = str(record.get("visit_type") or "")
        report_id = str(record["id"])
        organization_id = str(record["organization_id"])

        normalized = dict(incoming)
        issue_id = normalized.get("issue_id")
        if issue_id:
            issue_id = str(issue_id).strip().upper()
            normalized["issue_id"] = issue_id
            catalog_issue = self.catalog_service.find_issue(issue_id)
            if not catalog_issue:
                raise ValidationError(
                    message="ממצא לא נמצא בקטלוג",
                    details={"issue_id": issue_id},
                )
            allowed = set(allowed_top_families(visit_type))
            if catalog_issue["top_family"] not in allowed:
                raise ValidationError(
                    message=(
                        "ממצא זה אינו זמין לסוג הביקור שנבחר"
                    ),
                    details={
                        "issue_id": issue_id,
                        "visit_type": visit_type,
                    },
                )
            normalized = _apply_catalog_issue_defaults(
                normalized,
                catalog_issue,
                catalog_version=record.get("catalog_version"),
            )
        else:
            normalized["issue_id"] = None
            normalized["standard_ref"] = None
            normalized["top_family"] = None
            normalized["category_id"] = None
            normalized["category_name_he"] = None

        sort_order = normalized.pop("sort_order", None)
        if sort_order is None and for_create:
            sort_order = self.line_repository.next_sort_order(
                report_id
            )

        return {
            "report_id": report_id,
            "organization_id": organization_id,
            "sort_order": sort_order or 0,
            "location": normalized.get("location"),
            "trade": normalized.get("trade"),
            "status": normalized.get("status"),
            "description": normalized.get("description"),
            "notes": normalized.get("notes"),
            "severity": normalized.get("severity"),
            "standard_ref": normalized.get("standard_ref"),
            "engineering_impact": normalized.get(
                "engineering_impact"
            ),
            "issue_id": normalized.get("issue_id"),
            "catalog_version": normalized.get("catalog_version"),
            "top_family": normalized.get("top_family"),
            "category_id": normalized.get("category_id"),
            "category_name_he": normalized.get("category_name_he"),
        }

    def _build_line_update_payload(
        self,
        *,
        record: dict,
        existing: dict,
        incoming: dict,
    ) -> dict:
        if "issue_id" in incoming and incoming["issue_id"] is None:
            merged = {
                **existing,
                **incoming,
                "issue_id": None,
                "standard_ref": None,
                "top_family": None,
                "category_id": None,
                "category_name_he": None,
                "catalog_version": None,
            }
            editable_keys = (
                "location",
                "trade",
                "status",
                "description",
                "notes",
                "severity",
                "engineering_impact",
                "sort_order",
            )
            payload = {
                key: merged.get(key)
                for key in editable_keys
                if key in incoming
            }
            payload.update(
                {
                    "issue_id": None,
                    "standard_ref": None,
                    "top_family": None,
                    "category_id": None,
                    "category_name_he": None,
                    "catalog_version": None,
                }
            )
            return payload

        if incoming.get("issue_id"):
            return self._build_line_payload(
                record=record,
                incoming={
                    **existing,
                    **incoming,
                },
                for_create=False,
            )

        update_payload = {}
        for key in (
            "location",
            "trade",
            "status",
            "description",
            "notes",
            "severity",
            "engineering_impact",
            "sort_order",
        ):
            if key in incoming:
                update_payload[key] = incoming[key]

        if existing.get("issue_id"):
            if "standard_ref" in incoming:
                raise ValidationError(
                    message=(
                        "לא ניתן לערוך תקן כשהשורה מקושרת לממצא במפרט"
                    ),
                )

        return update_payload

    def _current_catalog_version(self) -> str | None:
        return self.catalog_service.get_catalog_summary().get(
            "catalog_version"
        )

    def _load_lines(
        self,
        report_id: str,
        *,
        current_catalog_version: str | None = None,
    ) -> list[dict]:
        if not self.are_lines_available():
            return []

        return [
            self._serialize_line(
                line,
                current_catalog_version=current_catalog_version,
            )
            for line in self.line_repository.list_by_report(
                report_id
            )
        ]

    def _get_org_report(
        self,
        *,
        organization_id: str,
        report_id: str,
    ) -> dict:
        record = self.report_repository.get_by_id(report_id)

        if not record or str(record.get("organization_id")) != organization_id:
            raise NotFoundError(
                message="Field visit report not found",
                resource_type="field_visit_report",
                resource_id=report_id,
            )

        return record

    @staticmethod
    def _ensure_editable(record: dict) -> None:
        status = str(record.get("status") or "")
        if status not in EDITABLE_STATUSES:
            raise ConflictError(
                message="הדוח אינו במצב עריכה",
                details={"status": status},
            )

    def _serialize_report(
        self,
        record: dict,
        *,
        project_name: str | None = None,
        include_lines: bool = True,
    ) -> dict:
        status = str(record.get("status") or "IN_PROGRESS")
        visit_type = str(record.get("visit_type") or "")
        report_id = str(record["id"])
        current_catalog_version = (
            self.catalog_service.get_catalog_summary().get(
                "catalog_version"
            )
        )
        lines = (
            self._load_lines(
                report_id,
                current_catalog_version=current_catalog_version,
            )
            if include_lines
            else []
        )
        report_catalog_version = record.get("catalog_version")
        catalog_sync = _catalog_sync_state(
            report_catalog_version=report_catalog_version,
            current_catalog_version=current_catalog_version,
        )

        return {
            "id": report_id,
            "organization_id": str(record["organization_id"]),
            "project_id": str(record["project_id"]),
            "project_name": project_name,
            "created_by_profile_id": str(
                record["created_by_profile_id"]
            ),
            "visit_type": visit_type,
            "visit_type_label_he": _visit_type_label(visit_type),
            "status": status,
            "status_label_he": VISIT_STATUS_LABELS_HE.get(
                status,
                status,
            ),
            "visit_date": record.get("visit_date"),
            "header_fields": record.get("header_fields") or {},
            "catalog_version": report_catalog_version,
            "current_catalog_version": current_catalog_version,
            "catalog_sync": catalog_sync,
            "closed_at": record.get("closed_at"),
            "locked_at": record.get("locked_at"),
            "created_at": record.get("created_at"),
            "updated_at": record.get("updated_at"),
            "lines": lines,
            "line_count": len(lines),
            "is_editable": status in EDITABLE_STATUSES,
            "can_reopen": status in REOPENABLE_STATUSES,
            "can_send_to_core": status in SENDABLE_STATUSES,
            "was_closed": bool(record.get("closed_at")),
            "organization_profile_snapshot": (
                record.get("organization_profile_snapshot")
            ),
        }

    def _serialize_line(
        self,
        record: dict,
        *,
        current_catalog_version: str | None = None,
    ) -> dict:
        issue_id = record.get("issue_id")
        line_id = str(record["id"])
        report_id = str(record["report_id"])
        photo_storage_path = record.get("photo_storage_path")
        has_photo = bool(photo_storage_path)
        catalog_warning = _line_catalog_warning(
            issue_id=issue_id,
            line_catalog_version=record.get("catalog_version"),
            current_catalog_version=current_catalog_version,
            catalog_issue=(
                self.catalog_service.find_issue(str(issue_id))
                if issue_id
                else None
            ),
        )
        return {
            "id": line_id,
            "report_id": report_id,
            "sort_order": int(record.get("sort_order") or 0),
            "location": record.get("location"),
            "trade": record.get("trade"),
            "status": record.get("status"),
            "description": record.get("description"),
            "notes": record.get("notes"),
            "severity": record.get("severity"),
            "standard_ref": record.get("standard_ref"),
            "engineering_impact": record.get("engineering_impact"),
            "issue_id": issue_id,
            "catalog_version": record.get("catalog_version"),
            "top_family": record.get("top_family"),
            "category_id": record.get("category_id"),
            "category_name_he": record.get("category_name_he"),
            "photo_storage_path": photo_storage_path,
            "has_photo": has_photo,
            "photo_url": (
                f"/field-reports/visits/{report_id}/lines/{line_id}/photo"
                if has_photo
                else None
            ),
            "has_catalog_issue": bool(issue_id),
            "catalog_warning": catalog_warning,
            "created_at": record.get("created_at"),
            "updated_at": record.get("updated_at"),
        }

    def _send_to_core_pipeline(
        self,
        record: dict,
        *,
        source_filename: str,
        source_content: bytes,
    ) -> dict:
        if not source_content:
            return {
                "success": False,
                "error_code": "FIELD_VISIT_REPORT_EMPTY_FILE",
                "error_message": "קובץ הדוח ריק",
            }

        filename = (
            source_filename.strip()
            if source_filename and source_filename.strip()
            else self._build_core_upload_filename(record)
        )
        suffix = Path(filename).suffix or ".pdf"
        with NamedTemporaryFile(
            mode="wb",
            suffix=suffix,
            delete=False,
        ) as temp_file:
            temp_file.write(source_content)
            temp_path = Path(temp_file.name)

        try:
            return self.report_processing_service.process_uploaded_report(
                project_id=str(record["project_id"]),
                filename=filename,
                file_path=str(temp_path),
            )
        finally:
            temp_path.unlink(missing_ok=True)

    @staticmethod
    def _build_core_upload_filename(record: dict) -> str:
        report_id = str(record["id"])
        visit_date = str(record.get("visit_date") or "unknown-date")
        return f"field-visit-{visit_date}-{report_id}.pdf"


def _line_is_empty(line: dict) -> bool:
    description = str(line.get("description") or "").strip()
    return not description


def _build_close_preview(lines: list[dict]) -> dict:
    empty_lines = [
        line for line in lines if _line_is_empty(line)
    ]
    catalog_warnings = [
        line
        for line in lines
        if line.get("catalog_warning")
    ]

    warnings: list[str] = []

    if not lines:
        warnings.append("אין שורות ממצאים בדוח.")

    if empty_lines:
        warnings.append(
            f"{len(empty_lines)} שורות ללא תיאור — מומלץ למלא לפני הפקת PDF."
        )

    if catalog_warnings:
        warnings.append(
            f"{len(catalog_warnings)} שורות עם אזהרת מפרט — "
            "מומלץ לבדוק לפני סגירה."
        )

    return {
        "line_count": len(lines),
        "empty_line_count": len(empty_lines),
        "empty_line_ids": [str(line["id"]) for line in empty_lines],
        "catalog_warning_count": len(catalog_warnings),
        "warnings": warnings,
    }


def _catalog_sync_state(
    *,
    report_catalog_version: str | None,
    current_catalog_version: str | None,
) -> dict:
    if not current_catalog_version:
        return {
            "is_current": True,
            "message": None,
        }

    if not report_catalog_version:
        return {
            "is_current": False,
            "message": (
                "דוח זה נפתח לפני שמירת גרסת קטלוג. "
                "מומלץ לסנכרן מפרט בהכנה לא מקוון."
            ),
        }

    if report_catalog_version != current_catalog_version:
        return {
            "is_current": False,
            "message": (
                f"גרסת הקטלוג במערכת ({current_catalog_version}) "
                f"חדשה מגרסת הדוח ({report_catalog_version})."
            ),
        }

    return {
        "is_current": True,
        "message": None,
    }


def _line_catalog_warning(
    *,
    issue_id: str | None,
    line_catalog_version: str | None,
    current_catalog_version: str | None,
    catalog_issue: dict | None,
) -> str | None:
    if not issue_id:
        return None

    if not catalog_issue:
        return (
            f"ממצא {issue_id} אינו קיים בקטלוג הנוכחי. "
            "השורה לא נמחקה — יש לעדכן ידנית."
        )

    if (
        current_catalog_version
        and line_catalog_version
        and line_catalog_version != current_catalog_version
    ):
        return (
            f"השורה נשמרה עם קטלוג {line_catalog_version}; "
            f"הגרסה הנוכחית היא {current_catalog_version}."
        )

    return None


def _merge_header_fields(
    project: dict,
    header_fields: dict | None,
    *,
    visit_type: str,
) -> dict:
    from app.config.field_report_construction_progress import (
        default_construction_progress_rows,
    )
    from app.config.field_report_pdf_defaults import (
        DEFAULT_CONTRACTOR_NOTES_HE,
        DEFAULT_PROJECT_UPDATES_HE,
        DEFAULT_WINTER_RECOMMENDATIONS_HE,
    )

    defaults = {
        "developer_name": project.get("developer_name"),
        "developer_pm_name": project.get("developer_pm_name")
        or project.get("contractor_name"),
        "contractor_name": project.get("contractor_name"),
        "lawyer_name": project.get("lawyer_name"),
        "site_address": project.get("city"),
        "project_updates": list(DEFAULT_PROJECT_UPDATES_HE),
        "winter_recommendations": DEFAULT_WINTER_RECOMMENDATIONS_HE,
        "contractor_notes": list(DEFAULT_CONTRACTOR_NOTES_HE),
        "inspector_title": "",
        "inspector_license": "",
        "construction_progress": default_construction_progress_rows(
            visit_type
        ),
    }
    merged = {**defaults, **(header_fields or {})}
    if not merged.get("construction_progress"):
        merged["construction_progress"] = default_construction_progress_rows(
            visit_type
        )
    return merged


def _apply_catalog_issue_defaults(
    payload: dict,
    catalog_issue: dict,
    *,
    catalog_version: str | None,
) -> dict:
    standard_ref = (
        catalog_issue.get("standard_ref")
        or catalog_issue.get("category_standard_id")
    )
    return {
        **payload,
        "trade": payload.get("trade") or catalog_issue.get(
            "issue_name_he"
        ),
        "description": payload.get("description")
        or catalog_issue.get("description"),
        "notes": payload.get("notes")
        or catalog_issue.get("rectification_action"),
        "severity": payload.get("severity")
        or catalog_issue.get("severity"),
        "standard_ref": standard_ref,
        "engineering_impact": payload.get("engineering_impact")
        or catalog_issue.get("engineering_impact"),
        "top_family": catalog_issue.get("top_family"),
        "category_id": catalog_issue.get("category_id"),
        "category_name_he": catalog_issue.get("category_name_he"),
        "catalog_version": payload.get("catalog_version")
        or catalog_version,
        "location": payload.get("location")
        or catalog_issue.get("target_elements"),
    }


def _visit_type_label(visit_type: str) -> str:
    from app.config.field_report_visit_types import (
        VISIT_TYPE_CONFIG,
    )

    config = VISIT_TYPE_CONFIG.get(visit_type)
    if not config:
        return visit_type
    return str(config["label_he"])
