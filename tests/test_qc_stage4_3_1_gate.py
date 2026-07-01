"""Gate test - roadmap 4.3.1 critical stale email alerts."""

from __future__ import annotations

from datetime import timedelta
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from app.auth.jwt_service import JWTService
from app.main import app
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


NOW = qc_now()


def _build_access_token(role: str = "SUPERVISOR") -> str:
    return JWTService().issue_access_token(
        user_id="supervisor-1",
        org_id="org-1",
        role=role,
        token_id="token-qc-4-3-1",
    )


def _auth_headers(role: str = "SUPERVISOR") -> dict[str, str]:
    return {
        "Authorization": f"Bearer {_build_access_token(role=role)}",
        "X-Organization-ID": "org-1",
    }


def test_post_critical_stale_alerts_triggers_notification_tool(monkeypatch) -> None:
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
    notification_tool = MagicMock()
    notification_tool.build_critical_stale_issue_messages.return_value = [
        {
            "to": "yossi@example.com",
            "subject": "התראת ליקוי קריטי",
            "body": "test",
            "issues": [{"issue_id": "issue-1"}],
        }
    ]
    notification_tool.send_reminders.return_value = [
        {"to": "yossi@example.com", "status": "SENT"}
    ]
    alert_service = QualityIssueCriticalAlertService(
        issue_repository=issue_repo,
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
        critical_alert_service=alert_service,
    )
    monkeypatch.setattr(
        "app.dependencies.qc_notification_service",
        qc_service,
    )

    client = TestClient(app)
    response = client.post(
        "/portfolio/quality-alerts/critical-stale",
        headers=_auth_headers("SUPERVISOR"),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["stale_issue_count"] == 1
    assert body["digest_count"] == 1
    assert body["deliveries"][0]["status"] == "SENT"
    notification_tool.send_reminders.assert_called_once()


def test_contractor_cannot_trigger_critical_stale_alerts(monkeypatch) -> None:
    alert_service = QualityIssueCriticalAlertService(
        issue_repository=InMemoryQualityIssueRepository(),
        project_repository=FakeProjectRepository(),
        notification_tool=MagicMock(),
    )
    qc_service = QcNotificationService(
        critical_alert_service=alert_service,
    )
    monkeypatch.setattr(
        "app.dependencies.qc_notification_service",
        qc_service,
    )

    client = TestClient(app)
    response = client.post(
        "/portfolio/quality-alerts/critical-stale",
        headers=_auth_headers("CONTRACTOR"),
    )

    assert response.status_code == 403
