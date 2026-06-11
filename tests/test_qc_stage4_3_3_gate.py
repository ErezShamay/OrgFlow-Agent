"""Gate test - roadmap 4.3.3 QC notifications via NotificationTool (not automation)."""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from app.auth.jwt_service import JWTService
from app.main import app
from app.schemas.qc_freeze import is_allowed_qc_exception, is_frozen_surface
from app.services.field_visit_report_open_alert_service import (
    FieldVisitReportOpenAlertService,
)
from app.services.qc_notification_service import QcNotificationService
from app.services.quality_issue_critical_alert_service import (
    QualityIssueCriticalAlertService,
)
from tests.quality_issues_test_support import (
    FakeProjectRepository,
    InMemoryQualityIssueRepository,
    qc_create_request,
    qc_now,
)
from tests.test_field_visit_reports import FakeVisitReportRepository


NOW = qc_now()
REPO_ROOT = Path(__file__).resolve().parents[1]


def _build_access_token(role: str = "SUPERVISOR") -> str:
    return JWTService().issue_access_token(
        user_id="supervisor-1",
        org_id="org-1",
        role=role,
        token_id="token-qc-4-3-3",
    )


def _auth_headers(role: str = "SUPERVISOR") -> dict[str, str]:
    return {
        "Authorization": f"Bearer {_build_access_token(role=role)}",
        "X-Organization-ID": "org-1",
    }


def test_qc_notifications_use_allowed_notification_tool_exception() -> None:
    assert is_allowed_qc_exception("NotificationTool") is True
    assert is_frozen_surface("automation_engine") is True


def test_automation_jobs_do_not_register_qc_notifications() -> None:
    automation_jobs = (REPO_ROOT / "app/automation/jobs.py").read_text()

    assert "qc_notification" not in automation_jobs
    assert "QcNotificationService" not in automation_jobs
    assert "critical_stale_alert" not in automation_jobs


def test_qc_notification_jobs_do_not_use_automation_engine() -> None:
    qc_jobs = (REPO_ROOT / "app/jobs/qc_notification_jobs.py").read_text()

    assert "AutomationNotificationService" not in qc_jobs
    assert "automation.jobs" not in qc_jobs
    assert "QcNotificationService" in qc_jobs
    assert "run_qc_notification_cycle" in qc_jobs


def test_scheduler_registers_single_qc_notification_cycle_job() -> None:
    scheduler_source = (REPO_ROOT / "app/jobs/scheduler.py").read_text()

    assert "run_qc_notification_cycle" in scheduler_source
    assert "qc_notification_cycle" in scheduler_source
    assert "run_critical_stale_alert_job" not in scheduler_source


def test_post_run_qc_notification_alerts_uses_notification_tool(
    monkeypatch,
) -> None:
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
    notification_tool = MagicMock()
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
    qc_service = QcNotificationService(
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
    monkeypatch.setattr("app.main.qc_notification_service", qc_service)

    client = TestClient(app)
    response = client.post(
        "/portfolio/quality-alerts/run",
        headers=_auth_headers("SUPERVISOR"),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["critical_stale"]["stale_issue_count"] == 1
    assert body["open_reports"]["overdue_report_count"] == 1
    assert body["total_emails_sent"] == 2
    assert notification_tool.send_reminders.call_count == 2
