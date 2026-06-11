"""QC notifications - roadmap 4.3.3: unified cycle via NotificationTool (not automation)."""

from __future__ import annotations

from datetime import UTC, datetime

from app.schemas.field_reports import OpenReportReminderResponse
from app.schemas.qc_notifications import QcNotificationCycleResponse
from app.schemas.quality_issue import QualityCriticalStaleAlertResponse
from app.services.field_visit_report_open_alert_service import (
    FieldVisitReportOpenAlertService,
)
from app.services.quality_issue_critical_alert_service import (
    QualityIssueCriticalAlertService,
)
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
