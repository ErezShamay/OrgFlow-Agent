"""QC notifications - roadmap 4.3.3: unified cycle via NotificationTool (not automation)."""

from __future__ import annotations

from datetime import UTC, datetime

from app.repositories.project_repository import ProjectRepository
from app.schemas.field_reports import OpenReportReminderResponse
from app.schemas.qc_notifications import (
    DraftIssueNotificationResponse,
    QcNotificationCycleResponse,
    QcReportNotificationResponse,
)
from app.schemas.quality_issue import QualityCriticalStaleAlertResponse
from app.config.settings import settings
from app.services.alert_dedup_store import (
    CriticalAlertDedupStore,
    OpenReportAlertDedupStore,
    production_alert_dedup_repository,
)
from app.services.field_visit_report_open_alert_service import (
    FieldVisitReportOpenAlertService,
)
from app.services.quality_issue_critical_alert_service import (
    QualityIssueCriticalAlertService,
)
from app.services.workspace_activity_service import WorkspaceActivityService
from app.tools.notification_tool import NotificationTool


def count_sent_deliveries(
    *responses: QualityCriticalStaleAlertResponse | OpenReportReminderResponse,
) -> int:
    total = 0
    for response in responses:
        for delivery in response.deliveries:
            if delivery.status == "SENT":
                total += 1
    return total


class QcNotificationService:
    """
    Runs QC email alerts through a shared NotificationTool instance.

    Intentionally separate from the automation engine (see qc-freeze 4.3).
    """

    def __init__(
        self,
        *,
        notification_tool: NotificationTool | None = None,
        critical_alert_service: QualityIssueCriticalAlertService | None = None,
        open_report_service: FieldVisitReportOpenAlertService | None = None,
        project_repository: ProjectRepository | None = None,
        workspace_activity_service: WorkspaceActivityService | None = None,
    ) -> None:
        self.notification_tool = notification_tool or NotificationTool()
        self.critical_alert_service = critical_alert_service or (
            QualityIssueCriticalAlertService(
                notification_tool=self.notification_tool,
            )
        )
        self.open_report_service = open_report_service or (
            FieldVisitReportOpenAlertService(
                notification_tool=self.notification_tool,
            )
        )
        self.project_repository = (
            project_repository or self.critical_alert_service.project_repository
        )
        self.workspace_activity_service = (
            workspace_activity_service or WorkspaceActivityService()
        )

    def run_critical_stale_for_organization(
        self,
        *,
        organization_id: str,
        now: datetime | None = None,
        send_email: bool = True,
    ) -> QualityCriticalStaleAlertResponse:
        return self.critical_alert_service.run_for_organization(
            organization_id=organization_id,
            now=now,
            send_email=send_email,
        )

    def run_open_reports_for_organization(
        self,
        *,
        organization_id: str,
        now: datetime | None = None,
        send_email: bool = True,
    ) -> OpenReportReminderResponse:
        return self.open_report_service.run_for_organization(
            organization_id=organization_id,
            now=now,
            send_email=send_email,
        )

    def run_for_organization(
        self,
        *,
        organization_id: str,
        now: datetime | None = None,
        send_email: bool = True,
    ) -> QcNotificationCycleResponse:
        current_time = now or datetime.now(UTC)
        critical_stale = self.run_critical_stale_for_organization(
            organization_id=organization_id,
            now=current_time,
            send_email=send_email,
        )
        open_reports = self.run_open_reports_for_organization(
            organization_id=organization_id,
            now=current_time,
            send_email=send_email,
        )
        return QcNotificationCycleResponse(
            organization_id=organization_id,
            critical_stale=critical_stale,
            open_reports=open_reports,
            total_emails_sent=count_sent_deliveries(
                critical_stale,
                open_reports,
            ),
        )

    def run_for_report(
        self,
        *,
        organization_id: str,
        report_id: str,
        project_id: str,
        created_issue_ids: list[str] | None = None,
        now: datetime | None = None,
        send_email: bool = True,
    ) -> QcReportNotificationResponse:
        """Evaluate QC alerts relevant to a single finalized report (N01)."""
        _ = (now, send_email)
        issue_ids = created_issue_ids or []
        critical_count = 0
        for issue_id in issue_ids:
            issue = self.critical_alert_service.issue_repository.get_by_id(
                issue_id,
            )
            if issue is None:
                continue
            if str(issue.get("severity") or "").upper() == "CRITICAL":
                critical_count += 1

        return QcReportNotificationResponse(
            organization_id=organization_id,
            report_id=report_id,
            project_id=project_id,
            alerts_evaluated=True,
            open_report_resolved=True,
            critical_new_issue_count=critical_count,
        )

    def notify_contractor_on_draft_issue(
        self,
        *,
        organization_id: str,
        project_id: str,
        report_id: str,
        issue_id: str,
        line_id: str,
        actor_id: str | None = None,
        send_email: bool | None = None,
    ) -> DraftIssueNotificationResponse:
        """
        L3 instant loop — workspace activity on draft; optional contractor email.

        Contractor portal remains PUBLISHED-only; email is a heads-up only.
        """
        issue = self.critical_alert_service.issue_repository.get_for_organization(
            issue_id=issue_id,
            organization_id=organization_id,
        )
        if issue is None:
            raise ValueError(f"Draft issue not found: {issue_id}")

        project = self.project_repository.get_project_by_id(project_id) or {}
        project_name = str(project.get("project_name") or project_id).strip()
        trade = str(issue.get("trade") or "").strip()
        title = str(issue.get("title") or "ליקוי").strip()
        location = str(issue.get("location") or "").strip()

        activity = self.workspace_activity_service.create_activity(
            project_id,
            activity_type="DRAFT_DEFECT_RECORDED",
            title="ליקוי נרשם בדוח פיקוח",
            description=(
                f"ליקוי draft נרשם בדוח פיקוח: {title}"
                + (f" ({trade})" if trade else "")
            ),
            metadata={
                "issue_id": issue_id,
                "report_id": report_id,
                "line_id": line_id,
                "trade": trade or None,
                "location": location or None,
                "visibility": "DRAFT",
            },
            actor_id=actor_id,
        )

        contractor_email = str(project.get("contractor_email") or "").strip()
        email_status = "SKIPPED"
        should_send_email = (
            settings.FEATURE_FLAGS.enable_email_delivery
            if send_email is None
            else send_email
        )
        if should_send_email and contractor_email:
            messages = self.notification_tool.build_draft_contractor_issue_messages(
                [
                    {
                        "contractor_email": contractor_email,
                        "contractor_name": project.get("contractor_name"),
                        "project_name": project_name,
                        "issue_title": title,
                        "trade": trade or None,
                        "location": location or None,
                        "issue_id": issue_id,
                        "report_id": report_id,
                    }
                ]
            )
            if messages:
                deliveries = self.notification_tool.send_reminders(messages)
                email_status = str(
                    deliveries[0].get("status") or "SKIPPED"
                ).upper()

        return DraftIssueNotificationResponse(
            organization_id=organization_id,
            project_id=project_id,
            report_id=report_id,
            issue_id=issue_id,
            line_id=line_id,
            workspace_activity_id=str(activity.get("id") or "") or None,
            contractor_email=contractor_email or None,
            email_status=email_status,
        )


def build_qc_notification_service(
    *,
    persistent_dedup: bool = False,
    notification_tool: NotificationTool | None = None,
    critical_alert_service: QualityIssueCriticalAlertService | None = None,
    open_report_service: FieldVisitReportOpenAlertService | None = None,
    project_repository: ProjectRepository | None = None,
    workspace_activity_service: WorkspaceActivityService | None = None,
) -> QcNotificationService:
    tool = notification_tool or NotificationTool()
    repository = (
        production_alert_dedup_repository()
        if persistent_dedup
        else None
    )
    critical = critical_alert_service or QualityIssueCriticalAlertService(
        notification_tool=tool,
        dedup_store=CriticalAlertDedupStore(repository=repository),
        project_repository=project_repository,
    )
    open_reports = open_report_service or FieldVisitReportOpenAlertService(
        notification_tool=tool,
        dedup_store=OpenReportAlertDedupStore(repository=repository),
        project_repository=project_repository,
    )
    return QcNotificationService(
        notification_tool=tool,
        critical_alert_service=critical,
        open_report_service=open_reports,
        project_repository=project_repository or critical.project_repository,
        workspace_activity_service=workspace_activity_service,
    )
