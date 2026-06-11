from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.auth.jwt_service import JWTService
from app.exceptions.exceptions import ConflictError, ForbiddenError
from app.main import app
from app.repositories.quality_issue_repository import (
    QualityIssueEventRepository,
    QualityIssueRepository,
    matches_issue_list_filters,
)
from app.schemas.quality_issue import (
    QualityIssueStatus,
    QualityIssueUpdateRequest,
)
from app.services.quality_issue_service import QualityIssueService
from tests.quality_issues_test_support import (
    FakeProjectRepository,
    InMemoryQualityIssueEventRepository,
    InMemoryQualityIssueRepository,
    qc_create_request,
    qc_issue_payload,
    qc_now_iso,
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


def _auth_headers(role: str = "SUPERVISOR") -> dict[str, str]:
    return {
        "Authorization": f"Bearer {_build_access_token(role=role)}",
        "X-Organization-ID": "org-1",
    }


def _issue_payload(**overrides: object) -> dict:
    return qc_issue_payload(**overrides)


@pytest.fixture
def issue_repo() -> InMemoryQualityIssueRepository:
    return InMemoryQualityIssueRepository()


@pytest.fixture
def event_repo() -> InMemoryQualityIssueEventRepository:
    return InMemoryQualityIssueEventRepository()


@pytest.fixture
def service() -> QualityIssueService:
    return QualityIssueService(
        issue_repository=InMemoryQualityIssueRepository(),
        event_repository=InMemoryQualityIssueEventRepository(),
        project_repository=FakeProjectRepository(),
    )


@pytest.fixture
def qc_setup(monkeypatch: pytest.MonkeyPatch) -> tuple[TestClient, QualityIssueService]:
    service = QualityIssueService(
        issue_repository=InMemoryQualityIssueRepository(),
        event_repository=InMemoryQualityIssueEventRepository(),
        project_repository=FakeProjectRepository(),
    )
    monkeypatch.setattr(
        "app.main.quality_issue_service",
        service,
    )
    return TestClient(app), service


@pytest.fixture
def client(qc_setup: tuple[TestClient, QualityIssueService]) -> TestClient:
    return qc_setup[0]


def test_create_project_quality_issue_success(client: TestClient) -> None:
    response = client.post(
        "/projects/proj-1/issues",
        headers=_auth_headers("SUPERVISOR"),
        json=_issue_payload(),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "נזילה"
    assert body["status"] == "OPEN"
    assert body["project_id"] == "proj-1"
    assert body["organization_id"] == "org-1"
    assert body["materialization_key"] == "report-1:line-1"


def test_create_project_quality_issue_forbidden_for_developer(
    client: TestClient,
) -> None:
    response = client.post(
        "/projects/proj-1/issues",
        headers=_auth_headers("DEVELOPER"),
        json=_issue_payload(),
    )

    assert response.status_code == 403


def test_create_project_quality_issue_requires_auth(
    client: TestClient,
) -> None:
    response = client.post(
        "/projects/proj-1/issues",
        json=_issue_payload(),
    )

    assert response.status_code == 401


def test_create_project_quality_issue_conflict_on_duplicate(
    client: TestClient,
) -> None:
    headers = _auth_headers("SUPERVISOR")
    payload = _issue_payload()

    first = client.post(
        "/projects/proj-1/issues",
        headers=headers,
        json=payload,
    )
    assert first.status_code == 200

    second = client.post(
        "/projects/proj-1/issues",
        headers=headers,
        json=payload,
    )
    assert second.status_code == 409


def test_create_project_quality_issue_unknown_project(
    client: TestClient,
) -> None:
    response = client.post(
        "/projects/missing/issues",
        headers=_auth_headers("SUPERVISOR"),
        json=_issue_payload(),
    )

    assert response.status_code == 404


def test_list_project_quality_issues_success(client: TestClient) -> None:
    headers = _auth_headers("SUPERVISOR")
    client.post(
        "/projects/proj-1/issues",
        headers=headers,
        json=_issue_payload(
            title="פתוח",
            materialization_key="report-1:line-1",
        ),
    )
    client.post(
        "/projects/proj-1/issues",
        headers=headers,
        json=_issue_payload(
            title="סגור",
            materialization_key="report-1:line-2",
        ),
    )

    response = client.get(
        "/projects/proj-1/issues",
        headers=headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["project_id"] == "proj-1"
    assert body["total"] == 2
    assert len(body["items"]) == 2


def test_list_project_open_quality_issues_excludes_closed(
    qc_setup: tuple[TestClient, QualityIssueService],
) -> None:
    client, service = qc_setup
    headers = _auth_headers("SUPERVISOR")
    client.post(
        "/projects/proj-1/issues",
        headers=headers,
        json=_issue_payload(
            title="פתוח",
            materialization_key="report-1:line-1",
        ),
    )
    closed = client.post(
        "/projects/proj-1/issues",
        headers=headers,
        json=_issue_payload(
            title="סגור",
            materialization_key="report-1:line-2",
        ),
    ).json()

    service.issue_repository.update(
        closed["id"],
        {"status": "CLOSED"},
    )

    response = client.get(
        "/projects/proj-1/issues/open",
        headers=headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["project_id"] == "proj-1"
    assert body["total"] == 1
    assert len(body["items"]) == 1
    assert body["items"][0]["status"] == "OPEN"
    assert body["items"][0]["title"] == "פתוח"


def test_list_project_open_quality_issues_limits_contractor_visibility(
    qc_setup: tuple[TestClient, QualityIssueService],
) -> None:
    client, service = qc_setup
    supervisor_headers = _auth_headers("SUPERVISOR")
    client.post(
        "/projects/proj-1/issues",
        headers=supervisor_headers,
        json=_issue_payload(
            title="פתוח",
            materialization_key="report-1:line-1",
        ),
    )
    pending = client.post(
        "/projects/proj-1/issues",
        headers=supervisor_headers,
        json=_issue_payload(
            title="ממתין",
            materialization_key="report-1:line-2",
        ),
    ).json()

    service.issue_repository.update(
        pending["id"],
        {"status": "PENDING_VERIFICATION"},
    )

    response = client.get(
        "/projects/proj-1/issues/open",
        headers=_auth_headers("CONTRACTOR"),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["status"] == "OPEN"


def test_list_project_open_quality_issues_requires_auth(
    client: TestClient,
) -> None:
    response = client.get("/projects/proj-1/issues/open")

    assert response.status_code == 401


def test_list_project_open_quality_issues_unknown_project(
    client: TestClient,
) -> None:
    response = client.get(
        "/projects/missing/issues/open",
        headers=_auth_headers("SUPERVISOR"),
    )

    assert response.status_code == 404


def test_suggest_project_quality_issue_matches_returns_ranked_candidates(
    qc_setup: tuple[TestClient, QualityIssueService],
) -> None:
    client, _service = qc_setup
    headers = _auth_headers("SUPERVISOR")
    client.post(
        "/projects/proj-1/issues",
        headers=headers,
        json=_issue_payload(
            title="נזילה",
            location="דירה 3",
            trade="אינסטלציה",
            group_key="bath",
            materialization_key="report-1:line-1",
        ),
    )
    client.post(
        "/projects/proj-1/issues",
        headers=headers,
        json=_issue_payload(
            title="אחר",
            location="דירה 4",
            trade="אינסטלציה",
            group_key="bath",
            materialization_key="report-1:line-2",
        ),
    )

    response = client.post(
        "/projects/proj-1/issues/suggest-matches",
        headers=headers,
        json={
            "location": "דירה 3",
            "trade": "אינסטלציה",
            "group_key": "bath",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["project_id"] == "proj-1"
    assert body["match_key"] == "דירה 3|אינסטלציה|bath"
    assert body["total"] == 1
    assert len(body["candidates"]) == 1
    assert body["candidates"][0]["score"] == 1.0
    assert body["candidates"][0]["issue"]["title"] == "נזילה"


def test_suggest_project_quality_issue_matches_returns_empty_when_no_match(
    client: TestClient,
) -> None:
    headers = _auth_headers("SUPERVISOR")
    client.post(
        "/projects/proj-1/issues",
        headers=headers,
        json=_issue_payload(
            title="נזילה",
            location="דירה 3",
            trade="טיח",
            group_key="bath",
            materialization_key="report-1:line-1",
        ),
    )

    response = client.post(
        "/projects/proj-1/issues/suggest-matches",
        headers=headers,
        json={
            "location": "דירה 3",
            "trade": "אינסטלציה",
            "group_key": "bath",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 0
    assert body["candidates"] == []


def test_suggest_project_quality_issue_matches_excludes_closed_issues(
    qc_setup: tuple[TestClient, QualityIssueService],
) -> None:
    client, service = qc_setup
    headers = _auth_headers("SUPERVISOR")
    created = client.post(
        "/projects/proj-1/issues",
        headers=headers,
        json=_issue_payload(
            title="סגור",
            location="דירה 3",
            trade="אינסטלציה",
            group_key="bath",
            materialization_key="report-1:line-1",
        ),
    ).json()
    service.issue_repository.update(created["id"], {"status": "CLOSED"})

    response = client.post(
        "/projects/proj-1/issues/suggest-matches",
        headers=headers,
        json={
            "location": "דירה 3",
            "trade": "אינסטלציה",
            "group_key": "bath",
        },
    )

    assert response.status_code == 200
    assert response.json()["total"] == 0


def test_suggest_project_quality_issue_matches_requires_auth(
    client: TestClient,
) -> None:
    response = client.post(
        "/projects/proj-1/issues/suggest-matches",
        json={"location": "דירה 3"},
    )

    assert response.status_code == 401


def test_suggest_project_quality_issue_matches_unknown_project(
    client: TestClient,
) -> None:
    response = client.post(
        "/projects/missing/issues/suggest-matches",
        headers=_auth_headers("SUPERVISOR"),
        json={"location": "דירה 3"},
    )

    assert response.status_code == 404


def test_list_project_quality_issues_filters_by_status(
    qc_setup: tuple[TestClient, QualityIssueService],
) -> None:
    client, service = qc_setup
    headers = _auth_headers("SUPERVISOR")
    client.post(
        "/projects/proj-1/issues",
        headers=headers,
        json=_issue_payload(
            title="פתוח",
            materialization_key="report-1:line-1",
        ),
    )
    closed = client.post(
        "/projects/proj-1/issues",
        headers=headers,
        json=_issue_payload(
            title="סגור",
            materialization_key="report-1:line-2",
        ),
    ).json()

    service.issue_repository.update(
        closed["id"],
        {"status": "CLOSED"},
    )

    response = client.get(
        "/projects/proj-1/issues",
        headers=headers,
        params={"status": "OPEN"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["status"] == "OPEN"


def test_list_project_quality_issues_hides_closed_from_contractor(
    qc_setup: tuple[TestClient, QualityIssueService],
) -> None:
    client, service = qc_setup
    supervisor_headers = _auth_headers("SUPERVISOR")
    client.post(
        "/projects/proj-1/issues",
        headers=supervisor_headers,
        json=_issue_payload(
            title="פתוח",
            materialization_key="report-1:line-1",
        ),
    )
    closed = client.post(
        "/projects/proj-1/issues",
        headers=supervisor_headers,
        json=_issue_payload(
            title="סגור",
            materialization_key="report-1:line-2",
        ),
    ).json()

    service.issue_repository.update(
        closed["id"],
        {"status": "CLOSED"},
    )

    response = client.get(
        "/projects/proj-1/issues",
        headers=_auth_headers("CONTRACTOR"),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["status"] == "OPEN"


def test_list_project_quality_issues_requires_auth(
    client: TestClient,
) -> None:
    response = client.get("/projects/proj-1/issues")

    assert response.status_code == 401


def test_list_project_quality_issues_unknown_project(
    client: TestClient,
) -> None:
    response = client.get(
        "/projects/missing/issues",
        headers=_auth_headers("SUPERVISOR"),
    )

    assert response.status_code == 404


def test_get_quality_issue_detail_success(client: TestClient) -> None:
    created = client.post(
        "/projects/proj-1/issues",
        headers=_auth_headers("SUPERVISOR"),
        json=_issue_payload(),
    ).json()

    response = client.get(
        f"/issues/{created['id']}",
        headers=_auth_headers("SUPERVISOR"),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["issue"]["id"] == created["id"]
    assert body["issue"]["title"] == "נזילה"
    assert len(body["events"]) == 1
    assert body["events"][0]["event_type"] == "DETECTED"


def test_get_quality_issue_detail_hides_closed_from_contractor(
    qc_setup: tuple[TestClient, QualityIssueService],
) -> None:
    client, service = qc_setup
    created = client.post(
        "/projects/proj-1/issues",
        headers=_auth_headers("SUPERVISOR"),
        json=_issue_payload(),
    ).json()

    service.issue_repository.update(
        created["id"],
        {"status": "CLOSED"},
    )

    response = client.get(
        f"/issues/{created['id']}",
        headers=_auth_headers("CONTRACTOR"),
    )

    assert response.status_code == 404


def test_get_quality_issue_detail_allows_developer_read_only(
    client: TestClient,
) -> None:
    created = client.post(
        "/projects/proj-1/issues",
        headers=_auth_headers("SUPERVISOR"),
        json=_issue_payload(),
    ).json()

    response = client.get(
        f"/issues/{created['id']}",
        headers=_auth_headers("DEVELOPER"),
    )

    assert response.status_code == 200
    assert response.json()["issue"]["id"] == created["id"]


def test_get_quality_issue_detail_requires_auth(client: TestClient) -> None:
    response = client.get("/issues/issue-1")

    assert response.status_code == 401


def test_get_quality_issue_detail_not_found(client: TestClient) -> None:
    response = client.get(
        "/issues/missing-issue",
        headers=_auth_headers("SUPERVISOR"),
    )

    assert response.status_code == 404


def test_update_quality_issue_closes_with_supervisor(
    client: TestClient,
) -> None:
    created = client.post(
        "/projects/proj-1/issues",
        headers=_auth_headers("SUPERVISOR"),
        json=_issue_payload(),
    ).json()

    response = client.patch(
        f"/issues/{created['id']}",
        headers=_auth_headers("SUPERVISOR"),
        json={
            "status": "CLOSED",
            "last_seen_report_id": "report-1",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "CLOSED"
    assert body["closed_by"] == "supervisor-1"
    assert body["closed_at"] is not None


def test_update_quality_issue_updates_fields(
    client: TestClient,
) -> None:
    created = client.post(
        "/projects/proj-1/issues",
        headers=_auth_headers("SUPERVISOR"),
        json=_issue_payload(),
    ).json()

    response = client.patch(
        f"/issues/{created['id']}",
        headers=_auth_headers("SUPERVISOR"),
        json={
            "title": "נזילה מתוקנת",
            "location": "דירה 5",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "נזילה מתוקנת"
    assert body["location"] == "דירה 5"


def test_update_quality_issue_open_to_in_remediation(
    client: TestClient,
) -> None:
    created = client.post(
        "/projects/proj-1/issues",
        headers=_auth_headers("SUPERVISOR"),
        json=_issue_payload(),
    ).json()

    response = client.patch(
        f"/issues/{created['id']}",
        headers=_auth_headers("SUPERVISOR"),
        json={"status": "IN_REMEDIATION"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "IN_REMEDIATION"


def test_update_quality_issue_contractor_cannot_start_remediation(
    client: TestClient,
) -> None:
    created = client.post(
        "/projects/proj-1/issues",
        headers=_auth_headers("SUPERVISOR"),
        json=_issue_payload(),
    ).json()

    response = client.patch(
        f"/issues/{created['id']}",
        headers=_auth_headers("CONTRACTOR"),
        json={"status": "IN_REMEDIATION"},
    )

    assert response.status_code == 403


def test_update_quality_issue_contractor_can_submit_remediation(
    qc_setup: tuple[TestClient, QualityIssueService],
) -> None:
    client, service = qc_setup
    created = client.post(
        "/projects/proj-1/issues",
        headers=_auth_headers("SUPERVISOR"),
        json=_issue_payload(),
    ).json()

    service.issue_repository.update(
        created["id"],
        {"status": "IN_REMEDIATION"},
    )

    response = client.patch(
        f"/issues/{created['id']}",
        headers=_auth_headers("CONTRACTOR"),
        json={
            "status": "PENDING_VERIFICATION",
            "photo_ids": ["photo-1"],
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "PENDING_VERIFICATION"


def test_update_quality_issue_contractor_remediation_requires_photo(
    qc_setup: tuple[TestClient, QualityIssueService],
) -> None:
    client, service = qc_setup
    created = client.post(
        "/projects/proj-1/issues",
        headers=_auth_headers("SUPERVISOR"),
        json=_issue_payload(),
    ).json()

    service.issue_repository.update(
        created["id"],
        {"status": "IN_REMEDIATION"},
    )

    response = client.patch(
        f"/issues/{created['id']}",
        headers=_auth_headers("CONTRACTOR"),
        json={
            "status": "PENDING_VERIFICATION",
            "notes": "הוחלפה ברז",
        },
    )

    assert response.status_code == 400


def test_update_quality_issue_supervisor_verifies_close_from_pending(
    qc_setup: tuple[TestClient, QualityIssueService],
) -> None:
    client, service = qc_setup
    created = client.post(
        "/projects/proj-1/issues",
        headers=_auth_headers("SUPERVISOR"),
        json=_issue_payload(),
    ).json()

    service.issue_repository.update(
        created["id"],
        {"status": "PENDING_VERIFICATION"},
    )

    response = client.patch(
        f"/issues/{created['id']}",
        headers=_auth_headers("SUPERVISOR"),
        json={"status": "CLOSED"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "CLOSED"
    assert body["closed_by"] == "supervisor-1"
    assert body["closed_at"] is not None

    detail = client.get(
        f"/issues/{created['id']}",
        headers=_auth_headers("SUPERVISOR"),
    ).json()
    verified_events = [
        event
        for event in detail["events"]
        if event["event_type"] == "VERIFIED_CLOSED"
    ]
    assert len(verified_events) == 1
    assert verified_events[0]["payload"]["from_status"] == "PENDING_VERIFICATION"


def test_update_quality_issue_supervisor_reopens_closed_issue(
    qc_setup: tuple[TestClient, QualityIssueService],
) -> None:
    client, service = qc_setup
    created = client.post(
        "/projects/proj-1/issues",
        headers=_auth_headers("SUPERVISOR"),
        json=_issue_payload(),
    ).json()

    service.issue_repository.update(
        created["id"],
        {
            "status": "CLOSED",
            "closed_at": "2026-06-09T10:00:00Z",
            "closed_by": "supervisor-1",
        },
    )

    response = client.patch(
        f"/issues/{created['id']}",
        headers=_auth_headers("SUPERVISOR"),
        json={"status": "REOPENED"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "REOPENED"
    assert body["recurrence_count"] == 1
    assert body["closed_at"] is None
    assert body["closed_by"] is None

    detail = client.get(
        f"/issues/{created['id']}",
        headers=_auth_headers("SUPERVISOR"),
    ).json()
    reopened_events = [
        event
        for event in detail["events"]
        if event["event_type"] == "REOPENED"
    ]
    assert len(reopened_events) == 1
    assert reopened_events[0]["payload"]["from_status"] == "CLOSED"


def test_update_quality_issue_contractor_cannot_reopen_closed_issue(
    qc_setup: tuple[TestClient, QualityIssueService],
) -> None:
    client, service = qc_setup
    created = client.post(
        "/projects/proj-1/issues",
        headers=_auth_headers("SUPERVISOR"),
        json=_issue_payload(),
    ).json()

    service.issue_repository.update(
        created["id"],
        {"status": "CLOSED"},
    )

    response = client.patch(
        f"/issues/{created['id']}",
        headers=_auth_headers("CONTRACTOR"),
        json={"status": "REOPENED"},
    )

    # CLOSED issues are hidden from contractors (persona filter → 404).
    assert response.status_code == 404


def test_update_quality_issue_forbidden_for_developer(
    client: TestClient,
) -> None:
    created = client.post(
        "/projects/proj-1/issues",
        headers=_auth_headers("SUPERVISOR"),
        json=_issue_payload(),
    ).json()

    response = client.patch(
        f"/issues/{created['id']}",
        headers=_auth_headers("DEVELOPER"),
        json={"title": "ניסיון עריכה"},
    )

    assert response.status_code == 403


def test_update_quality_issue_rejects_invalid_transition(
    client: TestClient,
) -> None:
    created = client.post(
        "/projects/proj-1/issues",
        headers=_auth_headers("SUPERVISOR"),
        json=_issue_payload(),
    ).json()

    response = client.patch(
        f"/issues/{created['id']}",
        headers=_auth_headers("SUPERVISOR"),
        json={"status": "PENDING_VERIFICATION"},
    )

    assert response.status_code == 400


def test_update_quality_issue_requires_auth(client: TestClient) -> None:
    response = client.patch(
        "/issues/issue-1",
        json={"title": "x"},
    )

    assert response.status_code == 401


def test_update_quality_issue_not_found(client: TestClient) -> None:
    response = client.patch(
        "/issues/missing-issue",
        headers=_auth_headers("SUPERVISOR"),
        json={"title": "x"},
    )

    assert response.status_code == 404


def test_portfolio_quality_summary_success(client: TestClient) -> None:
    headers = _auth_headers("SUPERVISOR")
    client.post(
        "/projects/proj-1/issues",
        headers=headers,
        json=_issue_payload(
            title="קריטי",
            severity="CRITICAL",
            materialization_key="k1",
        ),
    )
    client.post(
        "/projects/proj-1/issues",
        headers=headers,
        json=_issue_payload(
            title="פתוח",
            materialization_key="k2",
        ),
    )

    response = client.get(
        "/portfolio/quality-summary",
        headers=headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["organization_id"] == "org-1"
    assert body["total_open"] == 2
    assert body["total_open_critical"] == 1
    assert body["critical_open_over_14_days"] == 0
    assert len(body["projects"]) >= 1
    proj_one = next(
        project for project in body["projects"] if project["project_id"] == "proj-1"
    )
    assert proj_one["open_total"] == 2


def test_portfolio_quality_summary_allows_developer(
    client: TestClient,
) -> None:
    response = client.get(
        "/portfolio/quality-summary",
        headers=_auth_headers("DEVELOPER"),
    )

    assert response.status_code == 200
    assert response.json()["total_open"] == 0


def test_portfolio_quality_summary_forbidden_for_contractor(
    client: TestClient,
) -> None:
    response = client.get(
        "/portfolio/quality-summary",
        headers=_auth_headers("CONTRACTOR"),
    )

    assert response.status_code == 403


def test_portfolio_quality_summary_requires_auth(client: TestClient) -> None:
    response = client.get("/portfolio/quality-summary")

    assert response.status_code == 401


def test_portfolio_trade_heatmap_success(client: TestClient) -> None:
    headers = _auth_headers("SUPERVISOR")
    client.post(
        "/projects/proj-1/issues",
        headers=headers,
        json=_issue_payload(
            title="אינסטלציה",
            trade="אינסטלציה",
            severity="CRITICAL",
            materialization_key="heatmap-1",
        ),
    )
    client.post(
        "/projects/proj-1/issues",
        headers=headers,
        json=_issue_payload(
            title="חשמל",
            trade="חשמל",
            materialization_key="heatmap-2",
        ),
    )

    response = client.get(
        "/portfolio/quality-trade-heatmap",
        headers=headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["organization_id"] == "org-1"
    assert body["total_open"] == 2
    assert body["cells"][0]["trade"] == "אינסטלציה"
    assert body["cells"][0]["open_critical"] == 1


def test_portfolio_trade_heatmap_project_filter(client: TestClient) -> None:
    headers = _auth_headers("SUPERVISOR")
    client.post(
        "/projects/proj-1/issues",
        headers=headers,
        json=_issue_payload(
            title="proj-1",
            trade="אינסטלציה",
            materialization_key="heatmap-p1",
        ),
    )
    client.post(
        "/projects/proj-2/issues",
        headers=headers,
        json=_issue_payload(
            title="proj-2",
            trade="חשמל",
            materialization_key="heatmap-p2",
        ),
    )

    response = client.get(
        "/portfolio/quality-trade-heatmap?project_id=proj-2",
        headers=headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["project_id"] == "proj-2"
    assert body["total_open"] == 1
    assert body["cells"][0]["trade"] == "חשמל"


def test_portfolio_trade_heatmap_forbidden_for_contractor(
    client: TestClient,
) -> None:
    response = client.get(
        "/portfolio/quality-trade-heatmap",
        headers=_auth_headers("CONTRACTOR"),
    )

    assert response.status_code == 403


def test_portfolio_recurring_rankings_success(client: TestClient) -> None:
    headers = _auth_headers("SUPERVISOR")
    create_response = client.post(
        "/projects/proj-1/issues",
        headers=headers,
        json=_issue_payload(
            title="נזילה חוזרת",
            trade="אינסטלציה",
            severity="CRITICAL",
            materialization_key="recurring-1",
        ),
    )
    issue_id = create_response.json()["id"]

    client.patch(
        f"/issues/{issue_id}",
        headers=headers,
        json={
            "status": "CLOSED",
            "last_seen_report_id": "report-1",
        },
    )
    client.patch(
        f"/issues/{issue_id}",
        headers=headers,
        json={
            "status": "REOPENED",
            "last_seen_report_id": "report-2",
        },
    )

    response = client.get(
        "/portfolio/quality-recurring-rankings",
        headers=headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["organization_id"] == "org-1"
    assert body["total_recurring"] == 1
    assert body["issues"][0]["recurrence_count"] == 1
    assert body["issues"][0]["title"] == "נזילה חוזרת"


def test_portfolio_recurring_rankings_project_filter(
    client: TestClient,
) -> None:
    headers = _auth_headers("SUPERVISOR")
    client.post(
        "/projects/proj-1/issues",
        headers=headers,
        json=_issue_payload(
            title="חוזר",
            materialization_key="recurring-filter-1",
        ),
    )

    response = client.get(
        "/portfolio/quality-recurring-rankings?project_id=proj-2",
        headers=headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["project_id"] == "proj-2"
    assert body["total_recurring"] == 0
    assert body["issues"] == []


def test_portfolio_recurring_rankings_forbidden_for_contractor(
    client: TestClient,
) -> None:
    response = client.get(
        "/portfolio/quality-recurring-rankings",
        headers=_auth_headers("CONTRACTOR"),
    )

    assert response.status_code == 403


def test_portfolio_periodic_report_success(client: TestClient) -> None:
    supervisor_headers = _auth_headers("SUPERVISOR")
    developer_headers = _auth_headers("DEVELOPER")
    client.post(
        "/projects/proj-1/issues",
        headers=supervisor_headers,
        json=_issue_payload(
            title="ליקוי תקופתי",
            trade="אינסטלציה",
            materialization_key="periodic-api-1",
        ),
    )

    response = client.get(
        "/portfolio/quality-periodic-report?period_days=30",
        headers=developer_headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["organization_id"] == "org-1"
    assert body["summary"]["total_issues"] >= 1
    assert len(body["projects"]) >= 1


def test_portfolio_periodic_report_csv_export(client: TestClient) -> None:
    headers = _auth_headers("DEVELOPER")
    response = client.get(
        "/portfolio/quality-periodic-report/export?format=csv",
        headers=headers,
    )

    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    assert "attachment" in response.headers["content-disposition"]
    assert "דוח תקופתי" in response.text


def test_portfolio_periodic_report_forbidden_for_contractor(
    client: TestClient,
) -> None:
    response = client.get(
        "/portfolio/quality-periodic-report",
        headers=_auth_headers("CONTRACTOR"),
    )

    assert response.status_code == 403


# --- Repository ---


def test_repository_create_and_lookup_by_materialization_key(
    issue_repo: InMemoryQualityIssueRepository,
) -> None:
    created = issue_repo.create(
        organization_id="org-1",
        project_id="proj-1",
        request=qc_create_request(),
    )
    fetched = issue_repo.get_by_materialization_key(
        organization_id="org-1",
        materialization_key="report-1:line-1",
    )
    assert fetched is not None
    assert fetched["id"] == created["id"]


def test_repository_enforces_organization_scope(
    issue_repo: InMemoryQualityIssueRepository,
) -> None:
    created = issue_repo.create(
        organization_id="org-1",
        project_id="proj-1",
        request=qc_create_request(),
    )
    assert (
        issue_repo.get_for_organization(
            issue_id=created["id"],
            organization_id="org-1",
        )
        is not None
    )
    assert (
        issue_repo.get_for_organization(
            issue_id=created["id"],
            organization_id="org-2",
        )
        is None
    )


def test_repository_list_by_organization(
    issue_repo: InMemoryQualityIssueRepository,
) -> None:
    issue_repo.create(
        organization_id="org-1",
        project_id="proj-1",
        request=qc_create_request(materialization_key="k1"),
    )
    issue_repo.create(
        organization_id="org-2",
        project_id="proj-2",
        request=qc_create_request(materialization_key="k2"),
    )
    assert len(issue_repo.list_by_organization(organization_id="org-1")) == 1


def test_repository_matches_issue_list_filters() -> None:
    record = {
        "status": "OPEN",
        "severity": "HIGH",
        "trade": "אינסטלציה",
        "title": "נזילה בכיור",
        "description": "",
        "location": "דירה 3",
    }
    assert matches_issue_list_filters(record, statuses=["OPEN"], search="כיור")
    assert not matches_issue_list_filters(record, statuses=["CLOSED"])


def test_repository_table_names() -> None:
    assert QualityIssueRepository.TABLE == "quality_issues"
    assert QualityIssueEventRepository.TABLE == "quality_issue_events"


# --- Service ---


def test_service_create_issue_appends_detected_event(
    service: QualityIssueService,
) -> None:
    created = service.create_issue(
        organization_id="org-1",
        project_id="proj-1",
        request=qc_create_request(),
        actor_role="SUPERVISOR",
    )
    events = service.event_repository.list_by_issue_id(created["id"])
    assert created["status"] == "OPEN"
    assert len(events) == 1
    assert events[0]["event_type"] == "DETECTED"


def test_service_create_issue_rejects_duplicate_materialization_key(
    service: QualityIssueService,
) -> None:
    service.create_issue(
        organization_id="org-1",
        project_id="proj-1",
        request=qc_create_request(),
        actor_role="SUPERVISOR",
    )
    with pytest.raises(ConflictError):
        service.create_issue(
            organization_id="org-1",
            project_id="proj-1",
            request=qc_create_request(),
            actor_role="SUPERVISOR",
        )


def test_service_close_issue_creates_verified_closed_event(
    service: QualityIssueService,
) -> None:
    created = service.create_issue(
        organization_id="org-1",
        project_id="proj-1",
        request=qc_create_request(),
        actor_role="SUPERVISOR",
    )
    service.update_issue(
        organization_id="org-1",
        issue_id=created["id"],
        request=QualityIssueUpdateRequest(
            status=QualityIssueStatus.CLOSED,
            last_seen_report_id="report-1",
        ),
        actor_role="SUPERVISOR",
        actor_id="supervisor-1",
    )
    events = service.event_repository.list_by_issue_id(created["id"])
    assert any(event["event_type"] == "VERIFIED_CLOSED" for event in events)


def test_service_portfolio_summary_requires_portfolio_permission(
    service: QualityIssueService,
) -> None:
    with pytest.raises(ForbiddenError):
        service.get_portfolio_quality_summary(
            organization_id="org-1",
            actor_role="CONTRACTOR",
        )


# --- API integration ---


def test_list_project_quality_issues_filters_by_severity(
    client: TestClient,
) -> None:
    headers = _auth_headers("SUPERVISOR")
    client.post(
        "/projects/proj-1/issues",
        headers=headers,
        json=_issue_payload(
            title="קריטי",
            severity="CRITICAL",
            materialization_key="k1",
        ),
    )
    client.post(
        "/projects/proj-1/issues",
        headers=headers,
        json=_issue_payload(
            title="נמוך",
            severity="LOW",
            materialization_key="k2",
        ),
    )

    response = client.get(
        "/projects/proj-1/issues",
        headers=headers,
        params={"severity": "CRITICAL"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["severity"] == "CRITICAL"


def test_get_quality_issue_detail_rejects_cross_tenant_access(
    client: TestClient,
) -> None:
    created = client.post(
        "/projects/proj-1/issues",
        headers=_auth_headers("SUPERVISOR"),
        json=_issue_payload(),
    ).json()

    other_org_token = JWTService().issue_access_token(
        user_id="supervisor-2",
        org_id="org-2",
        role="SUPERVISOR",
        token_id="token-other",
    )
    response = client.get(
        f"/issues/{created['id']}",
        headers={
            "Authorization": f"Bearer {other_org_token}",
            "X-Organization-ID": "org-2",
        },
    )

    assert response.status_code == 404


def test_quality_issue_full_lifecycle_via_api(client: TestClient) -> None:
    headers = _auth_headers("SUPERVISOR")

    created = client.post(
        "/projects/proj-1/issues",
        headers=headers,
        json=_issue_payload(materialization_key="lifecycle-1"),
    )
    assert created.status_code == 200
    issue_id = created.json()["id"]

    listed = client.get("/projects/proj-1/issues", headers=headers)
    assert listed.json()["total"] == 1

    detail = client.get(f"/issues/{issue_id}", headers=headers)
    assert detail.json()["issue"]["status"] == "OPEN"
    assert detail.json()["events"][0]["event_type"] == "DETECTED"

    closed = client.patch(
        f"/issues/{issue_id}",
        headers=headers,
        json={
            "status": "CLOSED",
            "last_seen_report_id": "report-1",
        },
    )
    assert closed.status_code == 200
    assert closed.json()["status"] == "CLOSED"

    summary = client.get("/portfolio/quality-summary", headers=headers)
    assert summary.json()["total_open"] == 0
