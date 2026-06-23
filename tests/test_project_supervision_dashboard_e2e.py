"""Gate D10 — project supervision dashboard E2E (D1–D7 flow)."""

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


ORG_ID = "org-e2e"
PROJECT_ID = "proj-e2e"


def _token(role: str = "SUPERVISOR") -> str:
    return JWTService().issue_access_token(
        user_id="user-e2e",
        org_id=ORG_ID,
        role=role,
        token_id="token-e2e",
    )


def _headers(role: str = "SUPERVISOR") -> dict[str, str]:
    return {
        "Authorization": f"Bearer {_token(role)}",
        "X-Organization-ID": ORG_ID,
    }


class E2EReportRepository:
    def list_by_organization(
        self,
        organization_id: str,
        *,
        project_id: str,
        include_hidden: bool = False,
    ) -> list[dict]:
        return [
            _report(
                report_id="visit-e2e",
                apartment_number="8",
                updated_at="2026-06-15T10:00:00Z",
                items=[
                    _checklist_item(
                        item_id="ok-1",
                        status="OK",
                        category_name_he="חשמל",
                        category_id="ELECTRICAL",
                    ),
                    _checklist_item(
                        item_id="defect-1",
                        status="DEFECT",
                        category_name_he="חשמל",
                        category_id="ELECTRICAL",
                    ),
                ],
            )
        ]


class E2EIssueRepository:
    def list_by_project(self, *, organization_id, project_id, query=None):
        return []


@pytest.fixture
def e2e_client() -> TestClient:
    project_repo = InMemoryProjectRepository()
    project_repo.projects[PROJECT_ID] = {
        "id": PROJECT_ID,
        "organization_id": ORG_ID,
        "project_name": "E2E Tower",
    }

    apartment_repo = InMemoryProjectApartmentRepository()
    apartment_repo.records = [
        {
            "id": "apt-e2e-8",
            "organization_id": ORG_ID,
            "project_id": PROJECT_ID,
            "apartment_number": "8",
            "group_key": "apartment:8",
        }
    ]

    service = ProjectSupervisionDashboardService(
        project_repository=project_repo,
        report_repository=E2EReportRepository(),
        issue_repository=E2EIssueRepository(),
        apartment_repository=apartment_repo,
    )
    main_module.project_supervision_dashboard_service = service
    return TestClient(app)


def test_supervision_dashboard_e2e_kpis_and_trade_detail(e2e_client: TestClient) -> None:
    dashboard = e2e_client.get(
        f"/projects/{PROJECT_ID}/supervision-dashboard",
        headers=_headers("SUPERVISOR"),
    )
    assert dashboard.status_code == 200
    payload = dashboard.json()
    assert payload["kpis"]["total_items"] == 2
    assert payload["kpis"]["completed"] == 1
    assert payload["kpis"]["with_defects"] == 1
    assert payload["kpis"]["progress_percent"] == 50
    assert payload["apartments"][0]["apartment_number"] == "8"

    summaries = e2e_client.get(
        "/projects/supervision-summaries",
        headers=_headers("SUPERVISOR"),
    )
    assert summaries.status_code == 200
    summary_items = summaries.json()["items"]
    assert any(item["project_id"] == PROJECT_ID for item in summary_items)

    trade = e2e_client.get(
        f"/projects/{PROJECT_ID}/supervision-dashboard/trades/electrical",
        headers=_headers("SUPERVISOR"),
    )
    assert trade.status_code == 200
    trade_payload = trade.json()
    assert trade_payload["label_he"] == "חשמל"
    assert len(trade_payload["items"]) == 2
    assert trade_payload["items"][0]["scope_label_he"] == "דירה 8"
