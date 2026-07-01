"""Full remediation lifecycle E2E (roadmap 2.2.7).

OPEN → IN_REMEDIATION → PENDING_VERIFICATION → CLOSED → REOPENED
with persona permissions, events, open-issues registry, and portfolio KPIs.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.auth.jwt_service import JWTService
from app.main import app
from app.services.quality_issue_service import QualityIssueService
from tests.quality_issues_test_support import (
    FakeProjectRepository,
    InMemoryQualityIssueEventRepository,
    InMemoryQualityIssueRepository,
    qc_issue_payload,
)


def _build_access_token(
    *,
    user_id: str = "supervisor-1",
    org_id: str = "org-1",
    role: str = "SUPERVISOR",
) -> str:
    return JWTService().issue_access_token(
        user_id=user_id,
        org_id=org_id,
        role=role,
        token_id="token-qc",
    )


def _auth_headers(
    role: str = "SUPERVISOR",
    *,
    user_id: str | None = None,
) -> dict[str, str]:
    user_by_role = {
        "SUPERVISOR": "supervisor-1",
        "CONTRACTOR": "contractor-1",
        "DEVELOPER": "developer-1",
        "ADMIN": "admin-1",
    }
    return {
        "Authorization": (
            f"Bearer {_build_access_token(role=role, user_id=user_id or user_by_role[role])}"
        ),
        "X-Organization-ID": "org-1",
    }


@pytest.fixture
def qc_setup(monkeypatch: pytest.MonkeyPatch) -> tuple[TestClient, QualityIssueService]:
    service = QualityIssueService(
        issue_repository=InMemoryQualityIssueRepository(),
        event_repository=InMemoryQualityIssueEventRepository(),
        project_repository=FakeProjectRepository(),
    )
    monkeypatch.setattr("app.dependencies.quality_issue_service", service)
    return TestClient(app), service


def test_full_remediation_lifecycle_via_api(
    qc_setup: tuple[TestClient, QualityIssueService],
) -> None:
    client, _service = qc_setup
    supervisor_headers = _auth_headers("SUPERVISOR")
    contractor_headers = _auth_headers("CONTRACTOR")

    created = client.post(
        "/projects/proj-1/issues",
        headers=supervisor_headers,
        json=qc_issue_payload(materialization_key="lifecycle-full-1"),
    )
    assert created.status_code == 200
    issue_id = created.json()["id"]
    assert created.json()["status"] == "OPEN"

    open_list = client.get(
        "/projects/proj-1/issues/open",
        headers=supervisor_headers,
    ).json()
    assert open_list["total"] == 1

    draft_portfolio = client.get(
        "/portfolio/quality-summary",
        headers=supervisor_headers,
    ).json()
    assert draft_portfolio["total_open"] == 0

    contractor_cannot_start = client.patch(
        f"/issues/{issue_id}",
        headers=contractor_headers,
        json={"status": "IN_REMEDIATION"},
    )
    assert contractor_cannot_start.status_code == 403

    in_remediation = client.patch(
        f"/issues/{issue_id}",
        headers=supervisor_headers,
        json={"status": "IN_REMEDIATION"},
    )
    assert in_remediation.status_code == 200
    assert in_remediation.json()["status"] == "IN_REMEDIATION"

    pending = client.patch(
        f"/issues/{issue_id}",
        headers=contractor_headers,
        json={
            "status": "PENDING_VERIFICATION",
            "notes": "הוחלפה ברז",
            "photo_ids": ["photo-remediation-1"],
        },
    )
    assert pending.status_code == 200
    assert pending.json()["status"] == "PENDING_VERIFICATION"

    contractor_open = client.get(
        "/projects/proj-1/issues/open",
        headers=contractor_headers,
    ).json()
    assert contractor_open["total"] == 0

    closed = client.patch(
        f"/issues/{issue_id}",
        headers=supervisor_headers,
        json={
            "status": "CLOSED",
            "last_seen_report_id": "report-2",
            "last_seen_line_id": "line-2",
        },
    )
    assert closed.status_code == 200
    closed_body = closed.json()
    assert closed_body["status"] == "CLOSED"
    assert closed_body["closed_by"] == "supervisor-1"
    assert closed_body["closed_at"] is not None
    assert closed_body["last_seen_report_id"] == "report-2"

    open_after_close = client.get(
        "/projects/proj-1/issues/open",
        headers=supervisor_headers,
    ).json()
    assert open_after_close["total"] == 0

    summary_closed = client.get(
        "/portfolio/quality-summary",
        headers=supervisor_headers,
    ).json()
    assert summary_closed["total_open"] == 0

    reopened = client.patch(
        f"/issues/{issue_id}",
        headers=supervisor_headers,
        json={
            "status": "REOPENED",
            "last_seen_report_id": "report-3",
            "last_seen_line_id": "line-3",
        },
    )
    assert reopened.status_code == 200
    reopened_body = reopened.json()
    assert reopened_body["status"] == "REOPENED"
    assert reopened_body["recurrence_count"] == 1
    assert reopened_body["closed_at"] is None
    assert reopened_body["closed_by"] is None
    assert reopened_body["last_seen_report_id"] == "report-3"

    open_after_reopen = client.get(
        "/projects/proj-1/issues/open",
        headers=supervisor_headers,
    ).json()
    assert open_after_reopen["total"] == 1
    assert open_after_reopen["items"][0]["status"] == "REOPENED"

    detail = client.get(
        f"/issues/{issue_id}",
        headers=supervisor_headers,
    ).json()
    event_types = [event["event_type"] for event in detail["events"]]

    assert event_types[0] == "DETECTED"
    assert "STATUS_CHANGED" in event_types
    assert "REMEDIATION_SUBMITTED" in event_types
    assert "VERIFIED_CLOSED" in event_types
    assert "REOPENED" in event_types

    remediation = next(
        event
        for event in detail["events"]
        if event["event_type"] == "REMEDIATION_SUBMITTED"
    )
    assert remediation["payload"]["notes"] == "הוחלפה ברז"
    assert remediation["payload"]["photo_ids"] == ["photo-remediation-1"]
    assert remediation["actor_id"] == "contractor-1"

    verified = next(
        event for event in detail["events"] if event["event_type"] == "VERIFIED_CLOSED"
    )
    assert verified["payload"]["from_status"] == "PENDING_VERIFICATION"
    assert verified["payload"]["to_status"] == "CLOSED"
    assert verified["actor_id"] == "supervisor-1"

    reopened_event = next(
        event for event in detail["events"] if event["event_type"] == "REOPENED"
    )
    assert reopened_event["payload"]["from_status"] == "CLOSED"
    assert reopened_event["payload"]["to_status"] == "REOPENED"
    assert reopened_event["payload"]["recurrence_count"] == 1


def test_full_lifecycle_direct_close_from_open_via_api(
    qc_setup: tuple[TestClient, QualityIssueService],
) -> None:
    """Supervisor may close directly from OPEN during a field visit (shortcut path)."""
    client, _service = qc_setup
    supervisor_headers = _auth_headers("SUPERVISOR")

    created = client.post(
        "/projects/proj-1/issues",
        headers=supervisor_headers,
        json=qc_issue_payload(materialization_key="lifecycle-direct-close"),
    ).json()

    closed = client.patch(
        f"/issues/{created['id']}",
        headers=supervisor_headers,
        json={
            "status": "CLOSED",
            "last_seen_report_id": "report-visit-2",
            "last_seen_line_id": "line-visit-2",
        },
    )
    assert closed.status_code == 200
    assert closed.json()["status"] == "CLOSED"

    detail = client.get(
        f"/issues/{created['id']}",
        headers=supervisor_headers,
    ).json()
    verified = next(
        event
        for event in detail["events"]
        if event["event_type"] == "VERIFIED_CLOSED"
    )
    assert verified["payload"]["from_status"] == "OPEN"
    assert verified["payload"]["to_status"] == "CLOSED"
