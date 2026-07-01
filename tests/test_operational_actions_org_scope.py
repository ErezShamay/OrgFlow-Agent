from fastapi.testclient import TestClient

import app.main as main_module
from app.auth.jwt_service import JWTService
from app.main import app
from app.services.operational_action_service import (
    OperationalActionService,
)
from app.services.tenant_scope_service import (
    TenantScopeService,
)
import app.dependencies as deps


def _auth_headers():
    token = JWTService().issue_access_token(
        user_id="user-1",
        org_id="org-1",
        role="MANAGER",
        token_id="operational-actions-org-scope-tests",
    )
    return {"Authorization": f"Bearer {token}", "X-Organization-ID": "org-1"}


def test_get_open_actions_scopes_to_organization(monkeypatch):
    service = OperationalActionService.__new__(OperationalActionService)

    class FakeRepository:
        def get_open_actions(self):
            return [
                {"id": "orphan", "project_id": "other-project"},
            ]

        def get_open_actions_by_project_ids(self, project_ids: list[str]):
            if project_ids == ["project-a"]:
                return [{"id": "a-1", "project_id": "project-a"}]
            return []

        def get_open_actions_by_organization(self, organization_id: str):
            if organization_id == "org-client":
                return [
                    {
                        "id": "orphan-org",
                        "organization_id": "org-client",
                        "project_id": "other-project",
                    },
                ]
            return []

    class FakeProjectRepository:
        def get_projects_by_organization(self, organization_id: str):
            if organization_id == "org-client":
                return [{"id": "project-a"}]
            return []

    service.repository = FakeRepository()
    service.tenant_scope = TenantScopeService()
    service.tenant_scope.project_repository = (
        FakeProjectRepository()
    )

    scoped = service.get_open_actions(
        organization_id="org-client",
    )
    global_open = service.get_open_actions()

    assert [action["id"] for action in scoped] == ["a-1"]
    assert [action["id"] for action in global_open] == ["orphan"]


def test_get_escalations_scopes_to_organization(monkeypatch):
    service = OperationalActionService.__new__(OperationalActionService)

    class FakeRepository:
        def get_open_escalations(self):
            return [
                {"id": "orphan", "action_type": "ESCALATION"},
            ]

        def get_open_actions_by_project_ids(self, project_ids: list[str]):
            if project_ids == ["project-a"]:
                return [
                    {
                        "id": "e-1",
                        "project_id": "project-a",
                        "action_type": "ESCALATION",
                    },
                ]
            return []

        def get_open_actions_by_organization(self, organization_id: str):
            return []

    class FakeProjectRepository:
        def get_projects_by_organization(self, organization_id: str):
            if organization_id == "org-client":
                return [{"id": "project-a"}]
            return []

    service.repository = FakeRepository()
    service.tenant_scope = TenantScopeService()
    service.tenant_scope.project_repository = (
        FakeProjectRepository()
    )

    scoped = service.get_escalations(
        organization_id="org-client",
    )
    global_escalations = service.get_escalations()

    assert [item["id"] for item in scoped] == ["e-1"]
    assert [item["id"] for item in global_escalations] == ["orphan"]


def test_open_actions_endpoint_scopes_to_authenticated_org(monkeypatch):
    class FakeOperationalActionService:
        def get_open_actions(
            self,
            organization_id: str | None = None,
        ):
            assert organization_id == "org-1"
            return [{"id": "a-1", "status": "OPEN"}]

    monkeypatch.setattr(
        deps,
        "operational_action_service",
        FakeOperationalActionService(),
    )
    client = TestClient(app)

    response = client.get(
        "/actions/open",
        headers=_auth_headers(),
    )

    assert response.status_code == 200
    assert response.json() == [{"id": "a-1", "status": "OPEN"}]


def test_escalations_endpoint_scopes_to_authenticated_org(monkeypatch):
    class FakeOperationalActionService:
        def get_escalations(
            self,
            organization_id: str | None = None,
        ):
            assert organization_id == "org-1"
            return [{"id": "e-1", "action_type": "ESCALATION"}]

    monkeypatch.setattr(
        deps,
        "operational_action_service",
        FakeOperationalActionService(),
    )
    client = TestClient(app)

    response = client.get(
        "/actions/escalations",
        headers=_auth_headers(),
    )

    assert response.status_code == 200
    assert response.json() == [{"id": "e-1", "action_type": "ESCALATION"}]


def test_get_open_actions_returns_empty_when_organization_has_no_projects(
    monkeypatch,
):
    service = OperationalActionService.__new__(OperationalActionService)

    class FakeRepository:
        def get_open_actions(self):
            return [{"id": "global", "project_id": "any"}]

        def get_open_actions_by_project_ids(self, project_ids: list[str]):
            return [{"id": "should-not-run"}]

        def get_open_actions_by_organization(self, organization_id: str):
            return [{"id": "org-row", "organization_id": organization_id}]

    class FakeProjectRepository:
        def get_projects_by_organization(self, organization_id: str):
            return []

    service.repository = FakeRepository()
    service.tenant_scope = TenantScopeService()
    service.tenant_scope.project_repository = (
        FakeProjectRepository()
    )

    scoped = service.get_open_actions(
        organization_id="org-empty",
    )

    assert scoped == []
