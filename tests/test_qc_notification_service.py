"""Roadmap 4.3.3 - unified QC notification service via NotificationTool."""

from __future__ import annotations

from datetime import timedelta
from unittest.mock import MagicMock

from app.schemas.field_reports import OpenReportReminderResponse
from app.schemas.quality_issue import (
    QualityCriticalStaleAlertDelivery,
    QualityCriticalStaleAlertResponse,
)
from app.services.qc_notification_service import (
    QcNotificationService,
    count_sent_deliveries,
)
from app.tools.notification_tool import NotificationTool
from tests.quality_issues_test_support import (
    FakeProjectRepository,
    InMemoryQualityIssueRepository,
    qc_create_request,
    qc_now,
)
from tests.test_field_visit_reports import FakeVisitReportRepository


NOW = qc_now()


def test_count_sent_deliveries() -> None:
    critical = QualityCriticalStaleAlertResponse(
        organization_id="org-1",
        threshold_days=7,
        stale_issue_count=1,
        digest_count=1,
        deliveries=[
            QualityCriticalStaleAlertDelivery(
                to="a@example.com",
                status="SENT",
                issue_ids=["issue-1"],
            ),
            QualityCriticalStaleAlertDelivery(
                to="b@example.com",
                status="FAILED",
                issue_ids=["issue-2"],
            ),
        ],
    )
    open_reports = OpenReportReminderResponse(
        organization_id="org-1",
        threshold_days=3,
        overdue_report_count=1,
        digest_count=1,
        deliveries=[],
    )

    assert count_sent_deliveries(critical, open_reports) == 1


def test_qc_notification_service_shares_notification_tool() -> None:
    notification_tool = NotificationTool()
    service = QcNotificationService(notification_tool=notification_tool)

    assert service.critical_alert_service.notification_tool is notification_tool
    assert service.open_report_service.notification_tool is notification_tool


def test_run_for_organization_runs_both_alert_types() -> None:
    issue_repo = InMemoryQualityIssueRepository()
    issue_repo.create(
        organization_id="org-1",
        project_id="proj-1",
        request=qc_create_request(
            title="נזילה קריטית",
            severity="CRITICAL",
            first_seen_at=NOW - timedelta(days=10),
            materialization_key="report-1:line-1",
        ),
    )
    report_repo = FakeVisitReportRepository()
    report_repo.create(
        organization_id="org-1",
        project_id="proj-1",
        visit_date="2026-06-01",
        created_at=(NOW - timedelta(days=5)).isoformat(),
        updated_at=(NOW - timedelta(days=5)).isoformat(),
    )
    projects = FakeProjectRepository(
        projects={
            "proj-1": {
                "id": "proj-1",
                "organization_id": "org-1",
                "project_name": "האורנים 7",
                "supervisor_name": "יוסי",
                "supervisor_email": "yossi@example.com",
            }
        }
    )
    notification_tool = MagicMock(spec=NotificationTool)
    notification_tool.build_critical_stale_issue_messages.return_value = [
        {
            "to": "yossi@example.com",
            "subject": "critical",
            "body": "test",
            "issues": [{"issue_id": "issue-1"}],
        }
    ]
    notification_tool.build_open_report_reminder_messages.return_value = [
        {
            "to": "yossi@example.com",
            "subject": "report",
            "body": "test",
            "reports": [{"report_id": "report-1"}],
        }
    ]
    notification_tool.send_reminders.side_effect = [
        [{"to": "yossi@example.com", "status": "SENT"}],
        [{"to": "yossi@example.com", "status": "SENT"}],
    ]

    from app.services.field_visit_report_open_alert_service import (
        FieldVisitReportOpenAlertService,
    )
    from app.services.quality_issue_critical_alert_service import (
        QualityIssueCriticalAlertService,
    )

    service = QcNotificationService(
        notification_tool=notification_tool,
        critical_alert_service=QualityIssueCriticalAlertService(
            issue_repository=issue_repo,
            project_repository=projects,
            notification_tool=notification_tool,
        ),
        open_report_service=FieldVisitReportOpenAlertService(
            report_repository=report_repo,
            project_repository=projects,
            notification_tool=notification_tool,
        ),
    )
    result = service.run_for_organization(
        organization_id="org-1",
        now=NOW,
    )

    assert result.critical_stale.stale_issue_count == 1
    assert result.open_reports.overdue_report_count == 1
    assert result.total_emails_sent == 2
    assert notification_tool.send_reminders.call_count == 2
