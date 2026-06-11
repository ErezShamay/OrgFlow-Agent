"""QC alerts - roadmap 4.3.2: IN_PROGRESS report open > 3 days → email via NotificationTool."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Protocol

from app.repositories.field_visit_report_repository import FieldVisitReportRepository
from app.repositories.project_repository import ProjectRepository
from app.schemas.field_reports import (
    OpenReportReminderDelivery,
    OpenReportReminderResponse,
)
from app.services.quality_issue_portfolio_kpi import _parse_timestamp
from app.tools.notification_tool import NotificationTool

OPEN_REPORT_REMINDER_DAYS_THRESHOLD = 3
IN_PROGRESS_REPORT_STATUS = "IN_PROGRESS"


class OpenReportAlertDedupStore:
    """Skip duplicate reminders for the same report on the same calendar day."""

    def __init__(self) -> None:
        self._last_alert_date_by_report: dict[str, str] = {}

    def should_alert(self, report_id: str, *, alert_date: str) -> bool:
        return self._last_alert_date_by_report.get(report_id) != alert_date

    def mark_alerted(self, report_id: str, *, alert_date: str) -> None:
        self._last_alert_date_by_report[report_id] = alert_date


class OpenReportNotificationSender(Protocol):
    def build_open_report_reminder_messages(
        self,
        digests: list[dict[str, Any]],
    ) -> list[dict[str, Any]]: ...

    def send_reminders(
        self,
        reminders: list[dict[str, Any]],
    ) -> list[dict[str, Any]]: ...


def days_open_for_report(
    report: dict[str, Any],
    *,
    now: datetime,
) -> int | None:
    started_at = _parse_timestamp(report.get("created_at"))
    if started_at is None:
        started_at = _parse_timestamp(report.get("updated_at"))
    if started_at is None:
        return None
    return max(0, int((now - started_at).total_seconds() // 86400))


def is_report_open_over_days(
    report: dict[str, Any],
    *,
    threshold: int = OPEN_REPORT_REMINDER_DAYS_THRESHOLD,
    now: datetime,
) -> bool:
    if str(report.get("status") or "") != IN_PROGRESS_REPORT_STATUS:
        return False
    days_open = days_open_for_report(report, now=now)
    if days_open is None:
        return False
    return days_open > threshold


def select_open_reports_over_days(
    reports: list[dict[str, Any]],
    *,
    threshold: int = OPEN_REPORT_REMINDER_DAYS_THRESHOLD,
    now: datetime,
) -> list[dict[str, Any]]:
    """Return IN_PROGRESS reports open longer than threshold days."""
    overdue_reports = [
        report
        for report in reports
        if is_report_open_over_days(report, threshold=threshold, now=now)
    ]
    return sorted(
        overdue_reports,
        key=lambda report: (
            -int(days_open_for_report(report, now=now) or 0),
            str(report.get("visit_date") or "").casefold(),
        ),
    )


def build_supervisor_report_digests(
    overdue_reports: list[dict[str, Any]],
    *,
    projects_by_id: dict[str, dict[str, Any]],
    now: datetime,
) -> list[dict[str, Any]]:
    """Group overdue open reports by supervisor email for one digest email each."""
    digests_by_email: dict[str, dict[str, Any]] = {}

    for report in overdue_reports:
        project_id = str(report.get("project_id") or "")
        project = projects_by_id.get(project_id, {})
        supervisor_email = (project.get("supervisor_email") or "").strip()
        supervisor_name = (project.get("supervisor_name") or "מפקח").strip()
        project_name = (project.get("project_name") or project_id or "פרויקט").strip()
        days_open = days_open_for_report(report, now=now)

        digest_key = supervisor_email or f"missing-email:{project_id}"
        digest = digests_by_email.setdefault(
            digest_key,
            {
                "supervisor_email": supervisor_email or None,
                "supervisor_name": supervisor_name,
                "reports": [],
            },
        )
        digest["reports"].append(
            {
                "report_id": str(report.get("id") or ""),
                "project_id": project_id,
                "project_name": project_name,
                "visit_date": str(report.get("visit_date") or "").strip() or None,
                "visit_type": str(report.get("visit_type") or "").strip() or None,
                "days_open": days_open,
            }
        )

    return list(digests_by_email.values())


class FieldVisitReportOpenAlertService:
    def __init__(
        self,
        *,
        report_repository: FieldVisitReportRepository | None = None,
        project_repository: ProjectRepository | None = None,
        notification_tool: OpenReportNotificationSender | None = None,
        dedup_store: OpenReportAlertDedupStore | None = None,
    ) -> None:
        self.report_repository = report_repository or FieldVisitReportRepository()
        self.project_repository = project_repository or ProjectRepository()
        self.notification_tool = notification_tool or NotificationTool()
        self.dedup_store = dedup_store or OpenReportAlertDedupStore()

    def run_for_organization(
        self,
        *,
        organization_id: str,
        now: datetime | None = None,
        threshold: int = OPEN_REPORT_REMINDER_DAYS_THRESHOLD,
        send_email: bool = True,
    ) -> OpenReportReminderResponse:
        current_time = now or datetime.now(UTC)
        alert_date = current_time.date().isoformat()

        reports = self.report_repository.list_by_organization(
            organization_id,
            status=IN_PROGRESS_REPORT_STATUS,
        )
        overdue_reports = select_open_reports_over_days(
            reports,
            threshold=threshold,
            now=current_time,
        )

        projects = self.project_repository.get_projects_by_organization(
            organization_id
        )
        projects_by_id = {
            str(project.get("id") or ""): project
            for project in projects
            if project.get("id")
        }

        reports_to_notify: list[dict[str, Any]] = []
        skipped_report_ids: list[str] = []
        for report in overdue_reports:
            report_id = str(report.get("id") or "")
            if not report_id:
                continue
            if self.dedup_store.should_alert(report_id, alert_date=alert_date):
                reports_to_notify.append(report)
            else:
                skipped_report_ids.append(report_id)

        digests = build_supervisor_report_digests(
            reports_to_notify,
            projects_by_id=projects_by_id,
            now=current_time,
        )
        reminders = self.notification_tool.build_open_report_reminder_messages(
            digests
        )

        deliveries: list[OpenReportReminderDelivery] = []
        if send_email and reminders:
            sent_results = self.notification_tool.send_reminders(reminders)
            for reminder, result in zip(reminders, sent_results, strict=False):
                report_ids = [
                    str(item.get("report_id") or "")
                    for item in reminder.get("reports", [])
                    if item.get("report_id")
                ]
                for report_id in report_ids:
                    self.dedup_store.mark_alerted(
                        report_id,
                        alert_date=alert_date,
                    )
                deliveries.append(
                    OpenReportReminderDelivery(
                        to=result.get("to"),
                        status=str(result.get("status") or "UNKNOWN"),
                        report_ids=report_ids,
                        error=result.get("error"),
                    )
                )
        elif reminders:
            for reminder in reminders:
                report_ids = [
                    str(item.get("report_id") or "")
                    for item in reminder.get("reports", [])
                    if item.get("report_id")
                ]
                deliveries.append(
                    OpenReportReminderDelivery(
                        to=reminder.get("to"),
                        status="DRY_RUN",
                        report_ids=report_ids,
                    )
                )

        return OpenReportReminderResponse(
            organization_id=organization_id,
            threshold_days=threshold,
            overdue_report_count=len(overdue_reports),
            digest_count=len(digests),
            skipped_report_ids=skipped_report_ids,
            deliveries=deliveries,
        )
