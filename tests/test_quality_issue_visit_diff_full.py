"""Full visit issue diff E2E (roadmap 2.3.5).

Two-visit scenario: visit 1 materializes issues, visit 2 links / closes /
detects new / reopens - diff API reflects all four buckets.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.auth.jwt_service import JWTService
from app.exceptions.exceptions import ForbiddenError
from app.main import app
from app.services.quality_issue_service import QualityIssueService
from app.services.quality_issue_visit_diff_service import (
    QualityIssueVisitDiffService,
)
from tests.quality_issues_test_support import (
    FakeFieldVisitReportRepository,
    FakeProjectRepository,
    InMemoryQualityIssueEventRepository,
    InMemoryQualityIssueRepository,
    qc_create_request,
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
    monkeypatch.setattr("app.dependencies.quality_issue_service", service)
    return TestClient(app), service


def _create_issue(
    client: TestClient,
    *,
    title: str,
    materialization_key: str,
    report_id: str = "report-1",
    line_id: str | None = None,
) -> dict:
    payload = qc_issue_payload(
        title=title,
        materialization_key=materialization_key,
        first_seen_report_id=report_id,
        first_seen_line_id=line_id,
    )
    response = client.post(
        "/projects/proj-1/issues",
        headers=_auth_headers(),
        json=payload,
    )
    assert response.status_code == 200
    return response.json()


def test_two_visit_diff_flow_via_api(
    qc_setup: tuple[TestClient, QualityIssueService],
) -> None:
    """Gate-aligned: visit 2 links existing, closes one, adds new, reopens one."""
    client, service = qc_setup

    visit_one_issue = _create_issue(
        client,
        title="ליקוי מביקור 1",
        materialization_key="report-1:line-v1",
        report_id="report-1",
        line_id="line-v1",
    )
    to_close_issue = _create_issue(
        client,
        title="ליקוי לסגירה",
        materialization_key="report-1:line-close",
        report_id="report-1",
        line_id="line-close",
    )
    to_reopen_issue = _create_issue(
        client,
        title="ליקוי שיחזור",
        materialization_key="report-1:line-recur",
        report_id="report-1",
        line_id="line-recur",
    )

    service.event_repository.create(
        issue_id=visit_one_issue["id"],
        event_type="DETECTED",
        report_id="report-1",
        line_id="line-v1",
    )
    service.event_repository.create(
        issue_id=to_close_issue["id"],
        event_type="DETECTED",
        report_id="report-1",
        line_id="line-close",
    )
    service.event_repository.create(
        issue_id=to_reopen_issue["id"],
        event_type="DETECTED",
        report_id="report-1",
        line_id="line-recur",
    )
    service.issue_repository.update(to_reopen_issue["id"], {"status": "CLOSED"})

    visit_one_diff = client.get(
        "/projects/proj-1/visits/report-1/issue-diff",
        headers=_auth_headers(),
    )
    assert visit_one_diff.status_code == 200
    visit_one_body = visit_one_diff.json()
    assert visit_one_body["total_new"] == 3
    assert visit_one_body["total_still_open"] == 0
    assert visit_one_body["total_closed"] == 0
    assert visit_one_body["total_recurring"] == 0

    still_open_issue = _create_issue(
        client,
        title="ליקוי חדש בביקור 2",
        materialization_key="report-2:line-new",
        report_id="report-2",
        line_id="line-new",
    )

    service.event_repository.create(
        issue_id=visit_one_issue["id"],
        event_type="LINKED",
        report_id="report-2",
        line_id="line-v1-linked",
    )
    service.event_repository.create(
        issue_id=to_close_issue["id"],
        event_type="VERIFIED_CLOSED",
        report_id="report-2",
        line_id="line-close-v2",
        payload={"from_status": "OPEN", "to_status": "CLOSED"},
    )
    service.issue_repository.update(to_close_issue["id"], {"status": "CLOSED"})
    service.event_repository.create(
        issue_id=still_open_issue["id"],
        event_type="DETECTED",
        report_id="report-2",
        line_id="line-new",
    )
    service.event_repository.create(
        issue_id=to_reopen_issue["id"],
        event_type="REOPENED",
        report_id="report-2",
        line_id="line-recur-v2",
        payload={
            "from_status": "CLOSED",
            "to_status": "REOPENED",
            "recurrence_count": 1,
        },
    )
    service.issue_repository.update(
        to_reopen_issue["id"],
        {"status": "REOPENED", "recurrence_count": 1},
    )

    visit_two_diff = client.get(
        "/projects/proj-1/visits/report-2/issue-diff",
        headers=_auth_headers(),
    )
    assert visit_two_diff.status_code == 200
    body = visit_two_diff.json()

    assert body["project_id"] == "proj-1"
    assert body["report_id"] == "report-2"
    assert body["total_new"] == 1
    assert body["total_still_open"] == 1
    assert body["total_closed"] == 1
    assert body["total_recurring"] == 1
    assert {item["issue"]["id"] for item in body["new"]} == {still_open_issue["id"]}
    assert {item["issue"]["id"] for item in body["still_open"]} == {
        visit_one_issue["id"]
    }
    assert {item["issue"]["id"] for item in body["closed"]} == {to_close_issue["id"]}
    assert {item["issue"]["id"] for item in body["recurring"]} == {
        to_reopen_issue["id"]
    }


def test_visit_diff_empty_for_report_without_events(
    qc_setup: tuple[TestClient, QualityIssueService],
) -> None:
    client, _service = qc_setup

    response = client.get(
        "/projects/proj-1/visits/report-1/issue-diff",
        headers=_auth_headers(),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total_new"] == 0
    assert body["total_closed"] == 0
    assert body["total_still_open"] == 0
    assert body["total_recurring"] == 0
    assert body["new"] == []
    assert body["closed"] == []
    assert body["still_open"] == []
    assert body["recurring"] == []


def test_visit_diff_forbidden_without_read_permission(
    qc_setup: tuple[TestClient, QualityIssueService],
) -> None:
    client, _service = qc_setup

    response = client.get(
        "/projects/proj-1/visits/report-1/issue-diff",
        headers=_auth_headers("GUEST"),
    )

    assert response.status_code == 403


def test_visit_diff_service_prefers_reopened_over_linked(
    qc_setup: tuple[TestClient, QualityIssueService],
) -> None:
    _client, service = qc_setup

    issue = service.create_issue(
        organization_id="org-1",
        project_id="proj-1",
        request=qc_create_request(
            materialization_key="report-2:line-both",
            first_seen_report_id="report-2",
        ),
        actor_role="SUPERVISOR",
        actor_id="supervisor-1",
    )
    issue_id = issue["id"]

    service.event_repository.create(
        issue_id=issue_id,
        event_type="LINKED",
        report_id="report-2",
        line_id="line-linked",
    )
    service.event_repository.create(
        issue_id=issue_id,
        event_type="REOPENED",
        report_id="report-2",
        line_id="line-reopened",
        payload={"from_status": "CLOSED", "to_status": "REOPENED"},
    )
    service.issue_repository.update(issue_id, {"status": "REOPENED"})

    diff = service.visit_diff_service.get_visit_issue_diff(
        organization_id="org-1",
        project_id="proj-1",
        report_id="report-2",
        actor_role="SUPERVISOR",
    )

    assert diff.total_recurring == 1
    assert diff.total_still_open == 0
    assert diff.recurring[0].issue.id == issue_id


def test_visit_diff_service_skips_linked_when_issue_not_open(
    qc_setup: tuple[TestClient, QualityIssueService],
) -> None:
    _client, service = qc_setup

    issue = service.create_issue(
        organization_id="org-1",
        project_id="proj-1",
        request=qc_create_request(
            materialization_key="report-2:line-closed-link",
            first_seen_report_id="report-2",
        ),
        actor_role="SUPERVISOR",
        actor_id="supervisor-1",
    )
    issue_id = issue["id"]

    service.event_repository.create(
        issue_id=issue_id,
        event_type="LINKED",
        report_id="report-2",
        line_id="line-linked",
    )
    service.issue_repository.update(issue_id, {"status": "CLOSED"})

    diff = service.visit_diff_service.get_visit_issue_diff(
        organization_id="org-1",
        project_id="proj-1",
        report_id="report-2",
        actor_role="SUPERVISOR",
    )

    assert diff.total_still_open == 0
    assert diff.still_open == []


def test_visit_diff_service_requires_read_permission() -> None:
    service = QualityIssueVisitDiffService(
        issue_repository=InMemoryQualityIssueRepository(),
        event_repository=InMemoryQualityIssueEventRepository(),
        project_repository=FakeProjectRepository(),
        report_repository=FakeFieldVisitReportRepository(),
    )

    with pytest.raises(ForbiddenError):
        service.get_visit_issue_diff(
            organization_id="org-1",
            project_id="proj-1",
            report_id="report-1",
            actor_role="GUEST",
        )
