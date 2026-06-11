"""Visit issue diff API (roadmap 2.3.1–2.3.2)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.auth.jwt_service import JWTService
from app.main import app
from app.services.quality_issue_service import QualityIssueService
from tests.quality_issues_test_support import (
    FakeFieldVisitReportRepository,
    FakeProjectRepository,
    InMemoryQualityIssueEventRepository,
    InMemoryQualityIssueRepository,
    qc_issue_payload,
)


def _build_access_token(role: str = "SUPERVISOR") -> str:
    return JWTService().issue_access_token(
        user_id="supervisor-1",
        org_id="org-1",
        role=role,
        token_id="token-qc",
    )


def _auth_headers(role: str = "SUPERVISOR") -> dict[str, str]:
    return {
        "Authorization": f"Bearer {_build_access_token(role=role)}",
        "X-Organization-ID": "org-1",
    }


@pytest.fixture
def qc_setup(monkeypatch: pytest.MonkeyPatch) -> tuple[TestClient, QualityIssueService]:
    service = QualityIssueService(
        issue_repository=InMemoryQualityIssueRepository(),
        event_repository=InMemoryQualityIssueEventRepository(),
        project_repository=FakeProjectRepository(),
        report_repository=FakeFieldVisitReportRepository(),
    )
    monkeypatch.setattr("app.main.quality_issue_service", service)
    return TestClient(app), service


def test_get_visit_issue_diff_requires_auth() -> None:
    unauthenticated = TestClient(app)
    response = unauthenticated.get(
        "/projects/proj-1/visits/report-1/issue-diff"
    )
    assert response.status_code == 401


def test_get_visit_issue_diff_unknown_report(
    qc_setup: tuple[TestClient, QualityIssueService],
) -> None:
    client, _service = qc_setup
    response = client.get(
        "/projects/proj-1/visits/missing-report/issue-diff",
        headers=_auth_headers(),
    )
    assert response.status_code == 404


def test_get_visit_issue_diff_report_project_mismatch(
    qc_setup: tuple[TestClient, QualityIssueService],
) -> None:
    client, _service = qc_setup
    response = client.get(
        "/projects/proj-1/visits/report-other/issue-diff",
        headers=_auth_headers(),
    )
    assert response.status_code == 404


def test_get_visit_issue_diff_classifies_new_closed_still_open_recurring(
    qc_setup: tuple[TestClient, QualityIssueService],
) -> None:
    client, service = qc_setup

    new_issue = client.post(
        "/projects/proj-1/issues",
        headers=_auth_headers(),
        json=qc_issue_payload(
            title="ליקוי חדש",
            materialization_key="report-2:line-new",
            first_seen_report_id="report-2",
            first_seen_line_id="line-new",
        ),
    ).json()

    still_open_issue = client.post(
        "/projects/proj-1/issues",
        headers=_auth_headers(),
        json=qc_issue_payload(
            title="ליקוי פתוח",
            materialization_key="report-1:line-open",
        ),
    ).json()

    closed_issue = client.post(
        "/projects/proj-1/issues",
        headers=_auth_headers(),
        json=qc_issue_payload(
            title="ליקוי נסגר",
            materialization_key="report-1:line-closed",
        ),
    ).json()

    recurring_issue = client.post(
        "/projects/proj-1/issues",
        headers=_auth_headers(),
        json=qc_issue_payload(
            title="ליקוי חוזר",
            materialization_key="report-1:line-recurring",
        ),
    ).json()

    service.event_repository.create(
        issue_id=still_open_issue["id"],
        event_type="LINKED",
        report_id="report-2",
        line_id="line-open",
    )
    service.event_repository.create(
        issue_id=closed_issue["id"],
        event_type="LINKED",
        report_id="report-2",
        line_id="line-closed-linked",
    )
    service.event_repository.create(
        issue_id=closed_issue["id"],
        event_type="VERIFIED_CLOSED",
        report_id="report-2",
        line_id="line-closed",
        payload={
            "from_status": "OPEN",
            "to_status": "CLOSED",
        },
    )
    service.issue_repository.update(
        closed_issue["id"],
        {"status": "CLOSED"},
    )
    service.event_repository.create(
        issue_id=recurring_issue["id"],
        event_type="REOPENED",
        report_id="report-2",
        line_id="line-recurring",
        payload={
            "from_status": "CLOSED",
            "to_status": "REOPENED",
            "recurrence_count": 1,
        },
    )
    service.issue_repository.update(
        recurring_issue["id"],
        {"status": "REOPENED", "recurrence_count": 1},
    )

    response = client.get(
        "/projects/proj-1/visits/report-2/issue-diff",
        headers=_auth_headers(),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["project_id"] == "proj-1"
    assert body["report_id"] == "report-2"
    assert body["total_new"] == 1
    assert body["total_still_open"] == 1
    assert body["total_closed"] == 1
    assert body["total_recurring"] == 1
    assert body["new"][0]["issue"]["id"] == new_issue["id"]
    assert body["new"][0]["line_id"] == "line-new"
    assert body["still_open"][0]["issue"]["id"] == still_open_issue["id"]
    assert body["closed"][0]["issue"]["id"] == closed_issue["id"]
    assert body["recurring"][0]["issue"]["id"] == recurring_issue["id"]


def test_get_visit_issue_diff_hides_closed_from_contractor(
    qc_setup: tuple[TestClient, QualityIssueService],
) -> None:
    client, service = qc_setup

    closed_issue = client.post(
        "/projects/proj-1/issues",
        headers=_auth_headers(),
        json=qc_issue_payload(
            title="נסגר",
            materialization_key="report-2:line-1",
            first_seen_report_id="report-2",
        ),
    ).json()

    service.event_repository.create(
        issue_id=closed_issue["id"],
        event_type="VERIFIED_CLOSED",
        report_id="report-2",
        line_id="line-1",
        payload={"from_status": "OPEN", "to_status": "CLOSED"},
    )
    service.issue_repository.update(closed_issue["id"], {"status": "CLOSED"})

    response = client.get(
        "/projects/proj-1/visits/report-2/issue-diff",
        headers=_auth_headers("CONTRACTOR"),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total_closed"] == 0
    assert body["total_new"] == 0
