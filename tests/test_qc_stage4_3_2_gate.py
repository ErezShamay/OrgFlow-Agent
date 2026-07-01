"""Gate test - roadmap 4.3.2 open report email reminders."""

from __future__ import annotations

from datetime import timedelta
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from app.auth.jwt_service import JWTService
from app.main import app
from app.services.qc_notification_service import QcNotificationService
from app.services.field_visit_report_open_alert_service import (
    FieldVisitReportOpenAlertService,
)
from tests.quality_issues_test_support import FakeProjectRepository, qc_now
from tests.test_field_visit_reports import FakeVisitReportRepository


NOW = qc_now()


def _build_access_token(role: str = "SUPERVISOR") -> str:
    return JWTService().issue_access_token(
        user_id="supervisor-1",
        org_id="org-1",
        role=role,
        token_id="token-qc-4-3-2",
    )


def _auth_headers(role: str = "SUPERVISOR") -> dict[str, str]:
    return {
        "Authorization": f"Bearer {_build_access_token(role=role)}",
        "X-Organization-ID": "org-1",
    }


def test_post_open_report_reminders_triggers_notification_tool(
    monkeypatch,
) -> None:
    report_repo = FakeVisitReportRepository()
    report_repo.create(
        organization_id="org-1",
        project_id="proj-1",
        visit_date="2026-06-01",
        visit_type="STRUCTURE",
        created_at=(NOW - timedelta(days=5)).isoformat(),
        updated_at=(NOW - timedelta(days=5)).isoformat(),
    )
    notification_tool = MagicMock()
    notification_tool.build_open_report_reminder_messages.return_value = [
        {
            "to": "yossi@example.com",
            "subject": "תזכורת",
            "body": "test",
            "reports": [{"report_id": "report-1"}],
        }
    ]
    notification_tool.send_reminders.return_value = [
        {"to": "yossi@example.com", "status": "SENT"}
    ]
    alert_service = FieldVisitReportOpenAlertService(
        report_repository=report_repo,
        project_repository=FakeProjectRepository(
            projects={
                "proj-1": {
                    "id": "proj-1",
                    "organization_id": "org-1",
                    "project_name": "האורנים 7",
                    "supervisor_name": "יוסי",
                    "supervisor_email": "yossi@example.com",
                }
            }
        ),
        notification_tool=notification_tool,
    )
    qc_service = QcNotificationService(
        open_report_service=alert_service,
    )
    monkeypatch.setattr(
        "app.dependencies.qc_notification_service",
        qc_service,
    )

    client = TestClient(app)
    response = client.post(
        "/portfolio/quality-alerts/open-reports",
        headers=_auth_headers("SUPERVISOR"),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["overdue_report_count"] == 1
    assert body["digest_count"] == 1
    assert body["deliveries"][0]["status"] == "SENT"
    notification_tool.send_reminders.assert_called_once()


def test_contractor_cannot_trigger_open_report_reminders(monkeypatch) -> None:
    alert_service = FieldVisitReportOpenAlertService(
        report_repository=FakeVisitReportRepository(),
        project_repository=FakeProjectRepository(),
        notification_tool=MagicMock(),
    )
    qc_service = QcNotificationService(
        open_report_service=alert_service,
    )
    monkeypatch.setattr(
        "app.dependencies.qc_notification_service",
        qc_service,
    )

    client = TestClient(app)
    response = client.post(
        "/portfolio/quality-alerts/open-reports",
        headers=_auth_headers("CONTRACTOR"),
    )

    assert response.status_code == 403
