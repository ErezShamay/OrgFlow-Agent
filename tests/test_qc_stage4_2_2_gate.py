from __future__ import annotations

from fastapi.testclient import TestClient

from app.auth.jwt_service import JWTService
from app.main import app
from app.services.quality_issue_service import QualityIssueService
from tests.quality_issues_test_support import (
    FakeProjectRepository,
    InMemoryQualityIssueEventRepository,
    InMemoryQualityIssueRepository,
)


def _build_access_token(role: str = "CONTRACTOR") -> str:
    return JWTService().issue_access_token(
        user_id="contractor-1",
        org_id="org-1",
        role=role,
        token_id="token-qc-4-2-2",
    )


def _auth_headers(role: str = "CONTRACTOR") -> dict[str, str]:
    return {
        "Authorization": f"Bearer {_build_access_token(role=role)}",
        "X-Organization-ID": "org-1",
    }


def _issue_payload(**overrides: object) -> dict:
    from tests.quality_issues_test_support import qc_issue_payload

    return qc_issue_payload(**overrides)


def test_list_organization_issues_filters_contractor_statuses(
    monkeypatch,
) -> None:
    service = QualityIssueService(
        issue_repository=InMemoryQualityIssueRepository(),
        event_repository=InMemoryQualityIssueEventRepository(),
        project_repository=FakeProjectRepository(),
    )
    monkeypatch.setattr(
        "app.main.quality_issue_service",
        service,
    )
    client = TestClient(app)
    supervisor_headers = _auth_headers("SUPERVISOR")

    client.post(
        "/projects/proj-1/issues",
        headers=supervisor_headers,
        json=_issue_payload(
            title="פתוח",
            materialization_key="report-1:line-1",
        ),
    )
    in_remediation = client.post(
        "/projects/proj-1/issues",
        headers=supervisor_headers,
        json=_issue_payload(
            title="בטיפול",
            materialization_key="report-1:line-2",
        ),
    ).json()
    service.issue_repository.update(
        in_remediation["id"],
        {"status": "IN_REMEDIATION"},
    )
    closed = client.post(
        "/projects/proj-2/issues",
        headers=supervisor_headers,
        json=_issue_payload(
            title="סגור",
            materialization_key="report-2:line-1",
        ),
    ).json()
    service.issue_repository.update(
        closed["id"],
        {"status": "CLOSED"},
    )
    pending = client.post(
        "/projects/proj-2/issues",
        headers=supervisor_headers,
        json=_issue_payload(
            title="ממתין",
            materialization_key="report-2:line-2",
        ),
    ).json()
    service.issue_repository.update(
        pending["id"],
        {"status": "PENDING_VERIFICATION"},
    )

    response = client.get("/issues", headers=_auth_headers("CONTRACTOR"))

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    statuses = {item["status"] for item in body["items"]}
    assert statuses == {"OPEN", "IN_REMEDIATION"}


def test_list_organization_issues_allows_supervisor_all_statuses(
    monkeypatch,
) -> None:
    service = QualityIssueService(
        issue_repository=InMemoryQualityIssueRepository(),
        event_repository=InMemoryQualityIssueEventRepository(),
        project_repository=FakeProjectRepository(),
    )
    monkeypatch.setattr(
        "app.main.quality_issue_service",
        service,
    )
    client = TestClient(app)
    supervisor_headers = _auth_headers("SUPERVISOR")

    client.post(
        "/projects/proj-1/issues",
        headers=supervisor_headers,
        json=_issue_payload(materialization_key="report-1:line-1"),
    )
    closed = client.post(
        "/projects/proj-1/issues",
        headers=supervisor_headers,
        json=_issue_payload(materialization_key="report-1:line-2"),
    ).json()
    service.issue_repository.update(
        closed["id"],
        {"status": "CLOSED"},
    )

    response = client.get("/issues", headers=supervisor_headers)

    assert response.status_code == 200
    assert response.json()["total"] == 2
