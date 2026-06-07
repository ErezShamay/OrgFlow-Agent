from fastapi.testclient import TestClient

import app.main as main_module
from app.auth.jwt_service import JWTService
from app.main import app


class FakeProjectService:
    def __init__(self):
        self.projects = {
            "demo-project": {
                "id": "demo-project",
                "project_name": "Demo Tower",
                "status": "ACTIVE",
                "organization_id": "org-demo",
            },
            "client-project": {
                "id": "client-project",
                "project_name": "Client Site",
                "status": "ACTIVE",
                "organization_id": "org-client",
            },
        }

    def filter_projects(
        self,
        *,
        status=None,
        owner_id=None,
        tag=None,
        organization_id=None,
    ):
        results = list(self.projects.values())
        if organization_id:
            results = [
                project
                for project in results
                if project.get("organization_id") == organization_id
            ]
        return results

    def search_projects(
        self,
        query: str,
        *,
        organization_id=None,
    ):
        return self.filter_projects(organization_id=organization_id)


def _auth_headers(org_id: str):
    token = JWTService().issue_access_token(
        user_id="client-admin",
        org_id=org_id,
        role="ADMIN",
        token_id="tenant-isolation-test",
    )
    return {
        "Authorization": f"Bearer {token}",
        "X-Organization-ID": org_id,
    }


def test_projects_list_is_scoped_to_token_organization(monkeypatch):
    monkeypatch.setattr(main_module, "project_service", FakeProjectService())
    client = TestClient(app)

    response = client.get(
        "/projects",
        headers=_auth_headers("org-client"),
    )

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["id"] == "client-project"


def test_projects_list_requires_authentication(monkeypatch):
    monkeypatch.setattr(main_module, "project_service", FakeProjectService())
    client = TestClient(app)

    response = client.get("/projects")

    assert response.status_code == 401


class FakeProjectRepository:
    def __init__(self):
        self.projects = {
            "client-project": {
                "id": "client-project",
                "project_name": "Client Site",
                "organization_id": "org-client",
            },
            "demo-project": {
                "id": "demo-project",
                "project_name": "Demo Tower",
                "organization_id": "org-demo",
            },
        }

    def get_project_by_id(self, project_id: str):
        return self.projects.get(project_id)


class FakeEditableProjectService(FakeProjectService):
    def edit_project(self, project_id: str, **updates):
        project = self.projects.get(project_id)
        if not project:
            return None
        for key, value in updates.items():
            if value is not None:
                project[key] = value
        return project


def _patch_tenant_scope(monkeypatch, repository: FakeProjectRepository):
    monkeypatch.setattr(
        main_module.tenant_scope_service,
        "project_repository",
        repository,
    )


def test_edit_project_is_scoped_to_token_organization(monkeypatch):
    repository = FakeProjectRepository()
    _patch_tenant_scope(monkeypatch, repository)
    monkeypatch.setattr(
        main_module,
        "project_service",
        FakeEditableProjectService(),
    )
    client = TestClient(app)

    response = client.patch(
        "/projects/client-project",
        json={"developer_name": "יזם מעודכן"},
        headers=_auth_headers("org-client"),
    )

    assert response.status_code == 200
    assert response.json()["developer_name"] == "יזם מעודכן"


def test_edit_project_rejects_other_organization(monkeypatch):
    repository = FakeProjectRepository()
    _patch_tenant_scope(monkeypatch, repository)
    monkeypatch.setattr(
        main_module,
        "project_service",
        FakeEditableProjectService(),
    )
    client = TestClient(app)

    response = client.patch(
        "/projects/demo-project",
        json={"developer_name": "Hacked"},
        headers=_auth_headers("org-client"),
    )

    assert response.status_code == 404


def test_project_workspace_rejects_other_organization(monkeypatch):
    repository = FakeProjectRepository()
    _patch_tenant_scope(monkeypatch, repository)
    client = TestClient(app)

    response = client.get(
        "/projects/demo-project/workspace",
        headers=_auth_headers("org-client"),
    )

    assert response.status_code == 404
