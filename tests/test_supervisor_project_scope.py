from fastapi.testclient import TestClient

import app.main as main_module
from app.auth.jwt_service import JWTService
from app.main import app
from app.services.supervisor_project_scope import (
    filter_supervised_projects,
    project_supervised_by,
    should_scope_projects_to_supervisor,
)
import app.dependencies as deps


class FakeProfileRepository:
    def __init__(self, profiles: dict[str, dict]):
        self.profiles = profiles

    def get_profile_by_id(self, profile_id: str):
        return self.profiles.get(profile_id)


class FakeProjectService:
    def __init__(self):
        self.projects = [
            {
                "id": "proj-a",
                "project_name": "Tower A",
                "status": "ACTIVE",
                "organization_id": "org-client",
                "supervisor_email": "supervisor@example.com",
            },
            {
                "id": "proj-b",
                "project_name": "Tower B",
                "status": "ACTIVE",
                "organization_id": "org-client",
                "supervisor_email": "other@example.com",
            },
        ]

    def filter_projects(self, *, status=None, owner_id=None, tag=None, organization_id=None):
        results = list(self.projects)
        if organization_id:
            results = [
                project
                for project in results
                if project.get("organization_id") == organization_id
            ]
        return results

    def search_projects(self, query: str, *, organization_id=None):
        return self.filter_projects(organization_id=organization_id)


def _auth_headers(*, user_id: str, org_id: str, role: str):
    token = JWTService().issue_access_token(
        user_id=user_id,
        org_id=org_id,
        role=role,
        token_id=f"supervisor-scope-{user_id}-{role}",
    )
    return {
        "Authorization": f"Bearer {token}",
        "X-Organization-ID": org_id,
    }


def test_should_scope_projects_to_supervisor_only_for_supervisor_role() -> None:
    assert should_scope_projects_to_supervisor("SUPERVISOR") is True
    assert should_scope_projects_to_supervisor("ADMIN") is False
    assert should_scope_projects_to_supervisor("VIEWER") is False
    assert should_scope_projects_to_supervisor("RESIDENT") is False


def test_project_supervised_by_matches_email_case_insensitively() -> None:
    project = {"supervisor_email": "Supervisor@Example.com"}
    assert project_supervised_by(project, "supervisor@example.com") is True
    assert project_supervised_by(project, "other@example.com") is False
    assert project_supervised_by(project, None) is False


def test_filter_supervised_projects_returns_only_matching_projects() -> None:
    projects = [
        {"id": "1", "supervisor_email": "a@example.com"},
        {"id": "2", "supervisor_email": "b@example.com"},
    ]
    filtered = filter_supervised_projects(
        projects,
        role="SUPERVISOR",
        supervisor_email="A@example.com",
    )
    assert [project["id"] for project in filtered] == ["1"]

    unchanged = filter_supervised_projects(
        projects,
        role="ADMIN",
        supervisor_email="A@example.com",
    )
    assert unchanged == projects


def test_supervisor_projects_list_is_scoped_by_email(monkeypatch) -> None:
    monkeypatch.setattr(deps, "project_service", FakeProjectService())
    monkeypatch.setattr(
        deps.tenant_scope_service,
        "profile_repository",
        FakeProfileRepository(
            {
                "supervisor-1": {
                    "id": "supervisor-1",
                    "email": "supervisor@example.com",
                    "role": "SUPERVISOR",
                }
            }
        ),
    )
    client = TestClient(app)

    response = client.get(
        "/projects",
        headers=_auth_headers(
            user_id="supervisor-1",
            org_id="org-client",
            role="SUPERVISOR",
        ),
    )

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["id"] == "proj-a"


def test_admin_projects_list_is_not_scoped_to_supervisor_email(monkeypatch) -> None:
    monkeypatch.setattr(deps, "project_service", FakeProjectService())
    client = TestClient(app)

    response = client.get(
        "/projects",
        headers=_auth_headers(
            user_id="admin-1",
            org_id="org-client",
            role="ADMIN",
        ),
    )

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 2


def test_supervisor_cannot_open_unassigned_project_workspace(monkeypatch) -> None:
    monkeypatch.setattr(
        deps.tenant_scope_service,
        "profile_repository",
        FakeProfileRepository(
            {
                "supervisor-1": {
                    "id": "supervisor-1",
                    "email": "supervisor@example.com",
                    "role": "SUPERVISOR",
                }
            }
        ),
    )
    monkeypatch.setattr(
        deps.tenant_scope_service,
        "project_repository",
        type(
            "Repo",
            (),
            {
                "get_project_by_id": lambda self, project_id: {
                    "id": project_id,
                    "organization_id": "org-client",
                    "supervisor_email": "other@example.com",
                }
            },
        )(),
    )
    client = TestClient(app)

    response = client.get(
        "/projects/proj-b/workspace",
        headers=_auth_headers(
            user_id="supervisor-1",
            org_id="org-client",
            role="SUPERVISOR",
        ),
    )

    assert response.status_code == 404
