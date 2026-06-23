"""Gate D2 — GET /projects/{project_id}/supervision-dashboard."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

import app.main as main_module
from app.auth.jwt_service import JWTService
from app.main import app
from app.services.project_supervision_dashboard_service import (
    ProjectSupervisionDashboardService,
)
from tests.test_project_supervision_dashboard_d1_gate import (
    _checklist_item,
    _report,
)
from tests.test_project_zero_setup_gate import (
    InMemoryProjectApartmentRepository,
    InMemoryProjectRepository,
)


ORG_ID = "org-d2"
PROJECT_ID = "proj-d2"


def _token(role: str = "SUPERVISOR") -> str:
    return JWTService().issue_access_token(
        user_id="user-d2",
        org_id=ORG_ID,
        role=role,
        token_id="token-d2",
    )


def _headers(role: str = "SUPERVISOR") -> dict[str, str]:
    return {
        "Authorization": f"Bearer {_token(role)}",
        "X-Organization-ID": ORG_ID,
    }


class FakeReportRepository:
    def list_by_organization(
        self,
        organization_id: str,
        *,
        project_id: str,
        include_hidden: bool = False,
    ) -> list[dict]:
        assert organization_id == ORG_ID
        assert project_id == PROJECT_ID
        return [
            _report(
                report_id="visit-d2",
                apartment_number="3",
                updated_at="2026-06-10T10:00:00Z",
                items=[
                    _checklist_item(
                        item_id="ok",
                        status="OK",
                        category_name_he="חשמל",
                        category_id="ELECTRICAL",
                    ),
                ],
            )
        ]


class FakeIssueRepository:
    def list_by_project(self, *, organization_id, project_id, query=None):
        return []


@pytest.fixture
def dashboard_client() -> TestClient:
    project_repo = InMemoryProjectRepository()
    project_repo.projects[PROJECT_ID] = {
        "id": PROJECT_ID,
        "organization_id": ORG_ID,
        "project_name": "ויצמן 129",
    }

    apartment_repo = InMemoryProjectApartmentRepository()
    apartment_repo.records = [
        {
            "id": "apt-d2-3",
            "organization_id": ORG_ID,
            "project_id": PROJECT_ID,
            "apartment_number": "3",
            "group_key": "apartment:3",
        }
    ]

    main_module.project_supervision_dashboard_service = (
        ProjectSupervisionDashboardService(
            project_repository=project_repo,
            report_repository=FakeReportRepository(),
            issue_repository=FakeIssueRepository(),
            apartment_repository=apartment_repo,
        )
    )
    return TestClient(app)


def test_supervision_dashboard_success(dashboard_client: TestClient) -> None:
    response = dashboard_client.get(
        f"/projects/{PROJECT_ID}/supervision-dashboard",
        headers=_headers("SUPERVISOR"),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["project_id"] == PROJECT_ID
    assert payload["project_name"] == "ויצמן 129"
    assert payload["overall_status"] == "healthy"
    assert payload["kpis"]["total_items"] == 1
    assert payload["kpis"]["progress_percent"] == 100
    assert payload["apartments"][0]["apartment_number"] == "3"
    assert payload["trades"][0]["label_he"] == "חשמל"


def test_supervision_dashboard_forbidden_for_contractor(
    dashboard_client: TestClient,
) -> None:
    response = dashboard_client.get(
        f"/projects/{PROJECT_ID}/supervision-dashboard",
        headers=_headers("CONTRACTOR"),
    )

    assert response.status_code == 403


def test_supervision_dashboard_not_found_for_missing_project(
    dashboard_client: TestClient,
) -> None:
    response = dashboard_client.get(
        "/projects/missing-project/supervision-dashboard",
        headers=_headers("SUPERVISOR"),
    )

    assert response.status_code == 404


def test_supervision_dashboard_forbidden_for_wrong_organization_header(
    dashboard_client: TestClient,
) -> None:
    response = dashboard_client.get(
        f"/projects/{PROJECT_ID}/supervision-dashboard",
        headers={
            "Authorization": f"Bearer {_token('SUPERVISOR')}",
            "X-Organization-ID": "other-org",
        },
    )

    assert response.status_code == 403
