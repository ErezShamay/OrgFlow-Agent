from fastapi.testclient import TestClient

import app.main as main_module
from app.auth.jwt_service import JWTService
from app.main import app


class FakeProjectService:
    def __init__(self):
        self.projects = {
            "p1": {
                "id": "p1",
                "project_name": "Alpha Tower",
                "supervisor_name": "Dana",
                "supervisor_email": "dana@example.com",
                "status": "ACTIVE",
                "owner_id": "owner-1",
                "tags": ["infra"],
                "lifecycle_phase": "PLANNING",
                "organization_id": "org-1",
            }
        }
        self.attachments = {"p1": []}
        self.comments = {"p1": []}

    def create_project(self, **payload):
        created = {"id": "p2", "status": "ACTIVE", **payload}
        self.projects["p2"] = created
        return created

    def edit_project(self, project_id: str, **updates):
        project = self.projects.get(project_id)
        if not project:
            return None
        for key, value in updates.items():
            if value is not None:
                project[key] = value
        return project

    def archive_project(self, project_id: str):
        project = self.projects.get(project_id)
        if not project:
            return None
        project["status"] = "ARCHIVED"
        return project

    def delete_project(self, project_id: str):
        if project_id not in self.projects:
            return False
        del self.projects[project_id]
        return True

    def search_projects(
        self,
        query: str,
        *,
        organization_id=None,
    ):
        lowered = query.lower()
        return [
            project
            for project in self.projects.values()
            if lowered in project["project_name"].lower()
            and (
                not organization_id
                or project.get("organization_id") == organization_id
            )
        ]

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
        if status:
            results = [project for project in results if project.get("status") == status.upper()]
        if owner_id:
            results = [project for project in results if project.get("owner_id") == owner_id]
        if tag:
            results = [project for project in results if tag.lower() in project.get("tags", [])]
        return results

    def update_project_tags(self, project_id: str, tags: list[str]):
        project = self.projects.get(project_id)
        if not project:
            return None
        project["tags"] = sorted({tag.strip().lower() for tag in tags if tag.strip()})
        return project

    def set_project_owner(self, project_id: str, owner_id: str):
        project = self.projects.get(project_id)
        if not project:
            return None
        project["owner_id"] = owner_id
        return project

    def set_project_lifecycle_phase(self, project_id: str, lifecycle_phase: str):
        project = self.projects.get(project_id)
        if not project:
            return None
        project["lifecycle_phase"] = lifecycle_phase.strip().upper()
        return project

    def get_dashboard_widgets(self, project_id: str):
        project = self.projects.get(project_id)
        if not project:
            return None
        return {
            "project_id": project_id,
            "widgets": [
                {"id": "status_overview", "value": project["status"]},
                {"id": "owner", "value": project["owner_id"]},
                {"id": "lifecycle", "value": project["lifecycle_phase"]},
            ],
        }

    def get_cross_project_links(self, project_id: str):
        if project_id not in self.projects:
            return None
        return {
            "project_id": project_id,
            "links": [
                {
                    "source_project_id": project_id,
                    "target_project_id": "p2",
                    "target_project_name": "Linked Site",
                    "link_type": "RELATED",
                    "reasons": ["shared_owner"],
                    "shared_tags": [],
                }
            ],
            "total_links": 1,
        }

    def get_project_kpis(self, project_id: str):
        if project_id not in self.projects:
            return None
        return {
            "project_id": project_id,
            "kpis": [
                {"id": "organization_projects", "value": 2},
                {"id": "active_projects", "value": 1},
            ],
        }

    def get_project_analytics(self, project_id: str):
        if project_id not in self.projects:
            return None
        return {
            "project_id": project_id,
            "analytics": {
                "engagement_score": len(self.comments.get(project_id, [])) * 3
                + len(self.attachments.get(project_id, [])) * 2,
                "portfolio_coverage": 2,
            },
        }

    def add_project_attachment(self, project_id: str, filename: str, uploaded_by: str):
        if project_id not in self.projects:
            return None
        payload = {"id": "a1", "filename": filename, "uploaded_by": uploaded_by}
        self.attachments.setdefault(project_id, []).append(payload)
        return payload

    def get_project_attachments(self, project_id: str):
        if project_id not in self.projects:
            return None
        return self.attachments.get(project_id, [])

    def add_project_comment(self, project_id: str, comment: str, author: str):
        if project_id not in self.projects:
            return None
        payload = {"id": "c1", "comment": comment, "author": author, "created_at": "2026-01-01T00:00:00Z"}
        self.comments.setdefault(project_id, []).append(payload)
        return payload

    def get_project_comments(self, project_id: str):
        if project_id not in self.projects:
            return None
        return self.comments.get(project_id, [])

    def get_project_timeline(self, project_id: str):
        if project_id not in self.projects:
            return None
        return {
            "project_id": project_id,
            "events": [
                {"id": "e1", "event_type": "PROJECT_STATUS", "created_at": "2026-01-01T00:00:00Z"}
            ],
        }


def _client_with_fake_service(monkeypatch) -> TestClient:
    fake_service = FakeProjectService()
    monkeypatch.setattr(main_module, "project_service", fake_service)

    class FakeProjectRepository:
        def get_project_by_id(self, project_id: str):
            return fake_service.projects.get(project_id)

    monkeypatch.setattr(
        main_module.tenant_scope_service,
        "project_repository",
        FakeProjectRepository(),
    )
    return TestClient(app)


def _auth_headers():
    token = JWTService().issue_access_token(
        user_id="user-1",
        org_id="org-1",
        role="MANAGER",
        token_id="project-tests",
    )
    return {"Authorization": f"Bearer {token}", "X-Organization-ID": "org-1"}


def test_create_project_flow(monkeypatch):
    client = _client_with_fake_service(monkeypatch)
    response = client.post(
        "/projects",
        json={
            "project_name": "Beta Site",
            "developer_name": "Dev Co",
            "contractor_name": "Build Co",
            "lawyer_name": "Legal Co",
            "supervisor_name": "Noa",
            "tags": ["Critical"],
        },
        headers=_auth_headers(),
    )
    assert response.status_code == 200
    assert response.json()["project_name"] == "Beta Site"


def test_edit_project_flow(monkeypatch):
    client = _client_with_fake_service(monkeypatch)
    response = client.patch(
        "/projects/p1",
        json={"project_name": "Alpha Tower Rev 2"},
        headers=_auth_headers(),
    )
    assert response.status_code == 200
    assert response.json()["project_name"] == "Alpha Tower Rev 2"


def test_archive_project_flow(monkeypatch):
    client = _client_with_fake_service(monkeypatch)
    response = client.post("/projects/p1/archive", headers=_auth_headers())
    assert response.status_code == 200
    assert response.json()["status"] == "ARCHIVED"


def test_delete_project_flow(monkeypatch):
    client = _client_with_fake_service(monkeypatch)
    response = client.delete("/projects/p1", headers=_auth_headers())
    assert response.status_code == 200
    assert response.json()["deleted"] is True


def test_project_search(monkeypatch):
    client = _client_with_fake_service(monkeypatch)
    response = client.get("/projects/search", params={"query": "alpha"}, headers=_auth_headers())
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_project_filtering(monkeypatch):
    client = _client_with_fake_service(monkeypatch)
    response = client.get("/projects", params={"status": "active"}, headers=_auth_headers())
    assert response.status_code == 200
    assert response.json()[0]["id"] == "p1"


def test_project_tags(monkeypatch):
    client = _client_with_fake_service(monkeypatch)
    response = client.patch(
        "/projects/p1/tags",
        json={"tags": ["infra", "Compliance", "infra"]},
        headers=_auth_headers(),
    )
    assert response.status_code == 200
    assert response.json()["tags"] == ["compliance", "infra"]


def test_project_ownership_model(monkeypatch):
    client = _client_with_fake_service(monkeypatch)
    response = client.patch(
        "/projects/p1/owner",
        json={"owner_id": "owner-2"},
        headers=_auth_headers(),
    )
    assert response.status_code == 200
    assert response.json()["owner_id"] == "owner-2"


def test_project_lifecycle_management(monkeypatch):
    client = _client_with_fake_service(monkeypatch)
    response = client.patch(
        "/projects/p1/lifecycle",
        json={"lifecycle_phase": "execution"},
        headers=_auth_headers(),
    )
    assert response.status_code == 200
    assert response.json()["lifecycle_phase"] == "EXECUTION"


def test_project_dashboard_widgets(monkeypatch):
    client = _client_with_fake_service(monkeypatch)
    response = client.get("/projects/p1/dashboard-widgets", headers=_auth_headers())
    assert response.status_code == 200
    assert response.json()["project_id"] == "p1"
    assert len(response.json()["widgets"]) >= 3


def test_cross_project_linking(monkeypatch):
    client = _client_with_fake_service(monkeypatch)
    response = client.get("/projects/p1/links", headers=_auth_headers())
    assert response.status_code == 200
    assert response.json()["project_id"] == "p1"
    assert response.json()["total_links"] == 1


def test_project_kpis(monkeypatch):
    client = _client_with_fake_service(monkeypatch)
    response = client.get("/projects/p1/kpis", headers=_auth_headers())
    assert response.status_code == 200
    assert len(response.json()["kpis"]) >= 2


def test_project_analytics(monkeypatch):
    client = _client_with_fake_service(monkeypatch)
    response = client.get("/projects/p1/analytics", headers=_auth_headers())
    assert response.status_code == 200
    assert "engagement_score" in response.json()["analytics"]


def test_project_attachments(monkeypatch):
    client = _client_with_fake_service(monkeypatch)
    create_response = client.post(
        "/projects/p1/attachments",
        json={"filename": "plan.pdf", "uploaded_by": "Dana"},
        headers=_auth_headers(),
    )
    assert create_response.status_code == 200
    list_response = client.get("/projects/p1/attachments", headers=_auth_headers())
    assert list_response.status_code == 200
    assert len(list_response.json()["attachments"]) == 1


def test_project_comments(monkeypatch):
    client = _client_with_fake_service(monkeypatch)
    create_response = client.post(
        "/projects/p1/comments",
        json={"comment": "Need updated schedule", "author": "Dana"},
        headers=_auth_headers(),
    )
    assert create_response.status_code == 200
    list_response = client.get("/projects/p1/comments", headers=_auth_headers())
    assert list_response.status_code == 200
    assert len(list_response.json()["comments"]) == 1


def test_project_timeline(monkeypatch):
    client = _client_with_fake_service(monkeypatch)
    response = client.get("/projects/p1/timeline", headers=_auth_headers())
    assert response.status_code == 200
    assert len(response.json()["events"]) >= 1
