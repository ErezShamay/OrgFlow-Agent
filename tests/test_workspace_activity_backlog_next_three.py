from fastapi.testclient import TestClient

import app.main as main_module
from app.auth.jwt_service import JWTService
from app.main import app
from app.services.workspace_activity_service import WorkspaceActivityService
import app.dependencies as deps
import app.services.connection_managers as conn_mgrs


class FakeProjectRepository:
    def __init__(self):
        self.projects = {
            "p1": {"id": "p1", "project_name": "Alpha Tower"},
            "p2": {"id": "p2", "project_name": "Beta Site"},
        }

    def get_project_by_id(self, project_id: str):
        return self.projects.get(project_id)


def _auth_headers():
    token = JWTService().issue_access_token(
        user_id="user-1",
        org_id="org-1",
        role="MANAGER",
        token_id="workspace-tests",
    )
    return {"Authorization": f"Bearer {token}", "X-Organization-ID": "org-1"}


def _client(monkeypatch):
    monkeypatch.setattr(deps, "project_repository", FakeProjectRepository())
    monkeypatch.setattr(deps, "workspace_activity_service", WorkspaceActivityService())
    monkeypatch.setattr(
        conn_mgrs,
        "workspace_connection_manager",
        conn_mgrs.WorkspaceConnectionManager(),
    )
    return TestClient(app)


def test_workspace_realtime_updates_create_and_list(monkeypatch):
    client = _client(monkeypatch)

    create_response = client.post(
        "/projects/p1/workspace/activities",
        json={
            "activity_type": "REVIEW_UPDATED",
            "title": "Review status changed",
            "description": "AI review moved to completed",
            "metadata": {"review_id": "rv-1"},
            "actor_id": "user-1",
        },
        headers=_auth_headers(),
    )
    assert create_response.status_code == 200
    assert create_response.json()["activity_type"] == "REVIEW_UPDATED"

    list_response = client.get("/projects/p1/workspace/activities", headers=_auth_headers())
    assert list_response.status_code == 200
    assert list_response.json()["total"] == 1
    assert list_response.json()["activities"][0]["title"] == "Review status changed"


def test_workspace_activity_filtering(monkeypatch):
    client = _client(monkeypatch)

    client.post(
        "/projects/p1/workspace/activities",
        json={
            "activity_type": "ACTION_CREATED",
            "title": "Action created",
            "description": "New mitigation action",
            "actor_id": "owner-1",
        },
        headers=_auth_headers(),
    )
    client.post(
        "/projects/p1/workspace/activities",
        json={
            "activity_type": "REVIEW_UPDATED",
            "title": "Review approved",
            "description": "Approved by manager",
            "actor_id": "manager-1",
        },
        headers=_auth_headers(),
    )

    filtered_response = client.get(
        "/projects/p1/workspace/activities",
        params={
            "activity_type": "review_updated",
            "actor_id": "manager-1",
            "search": "approved",
        },
        headers=_auth_headers(),
    )
    assert filtered_response.status_code == 200
    payload = filtered_response.json()
    assert payload["total"] == 1
    assert payload["activities"][0]["activity_type"] == "REVIEW_UPDATED"
    assert payload["activities"][0]["actor_id"] == "manager-1"


def test_workspace_websocket_support_pushes_new_activity(monkeypatch):
    client = _client(monkeypatch)

    with client.websocket_connect("/projects/p1/workspace/stream") as websocket:
        create_response = client.post(
            "/projects/p1/workspace/activities",
            json={
                "activity_type": "WORKSPACE_WIDGET",
                "title": "Widget refreshed",
                "description": "Safety KPI widget auto refreshed",
                "actor_id": "system",
            },
            headers=_auth_headers(),
        )
        assert create_response.status_code == 200

        pushed = websocket.receive_json()
        assert pushed["event"] == "workspace.activity.created"
        assert pushed["project_id"] == "p1"
        assert pushed["activity"]["title"] == "Widget refreshed"


def test_workspace_widgets_customization(monkeypatch):
    client = _client(monkeypatch)

    save_response = client.put(
        "/projects/p1/workspace/widgets",
        json={"widgets": [{"id": "kpi", "position": 1}, {"id": "timeline", "position": 2}]},
        headers=_auth_headers(),
    )
    assert save_response.status_code == 200
    assert save_response.json()["total_widgets"] == 2

    get_response = client.get("/projects/p1/workspace/widgets", headers=_auth_headers())
    assert get_response.status_code == 200
    assert get_response.json()["widgets"][0]["id"] == "kpi"


def test_workspace_layout_customization(monkeypatch):
    client = _client(monkeypatch)

    save_response = client.put(
        "/projects/p1/workspace/layout",
        json={"layout": {"columns": 2, "sections": ["overview", "feed"]}},
        headers=_auth_headers(),
    )
    assert save_response.status_code == 200
    assert save_response.json()["layout"]["columns"] == 2

    get_response = client.get("/projects/p1/workspace/layout", headers=_auth_headers())
    assert get_response.status_code == 200
    assert get_response.json()["layout"]["sections"] == ["overview", "feed"]


def test_cross_project_workspace_feed(monkeypatch):
    client = _client(monkeypatch)

    client.post(
        "/projects/p1/workspace/activities",
        json={"activity_type": "ACTION_CREATED", "title": "P1 action", "actor_id": "u1"},
        headers=_auth_headers(),
    )
    client.post(
        "/projects/p2/workspace/activities",
        json={"activity_type": "ACTION_CREATED", "title": "P2 action", "actor_id": "u2"},
        headers=_auth_headers(),
    )

    response = client.post(
        "/workspace/cross-project",
        json={"project_ids": ["p1", "p2"], "limit": 10},
        headers=_auth_headers(),
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 2
    assert sorted([item["project_id"] for item in payload["activities"]]) == ["p1", "p2"]


def test_workspace_timeline_optimized_pagination(monkeypatch):
    client = _client(monkeypatch)

    first = client.post(
        "/projects/p1/workspace/activities",
        json={"activity_type": "ACTION_CREATED", "title": "first", "actor_id": "u1"},
        headers=_auth_headers(),
    ).json()
    second = client.post(
        "/projects/p1/workspace/activities",
        json={"activity_type": "ACTION_CREATED", "title": "second", "actor_id": "u1"},
        headers=_auth_headers(),
    ).json()
    _ = first

    page_response = client.get(
        "/projects/p1/workspace/activities",
        params={"before": second["created_at"], "limit": 10},
        headers=_auth_headers(),
    )
    assert page_response.status_code == 200
    assert page_response.json()["activities"][0]["title"] == "first"


def test_workspace_analytics_search_grouping_and_operational_feed(monkeypatch):
    client = _client(monkeypatch)

    client.post(
        "/projects/p1/workspace/activities",
        json={"activity_type": "ACTION_CREATED", "title": "Permit action", "description": "Action opened", "actor_id": "u1"},
        headers=_auth_headers(),
    )
    client.post(
        "/projects/p1/workspace/activities",
        json={"activity_type": "REVIEW_UPDATED", "title": "Review accepted", "description": "Accepted by manager", "actor_id": "u2"},
        headers=_auth_headers(),
    )

    analytics_response = client.get("/projects/p1/workspace/analytics", headers=_auth_headers())
    assert analytics_response.status_code == 200
    assert analytics_response.json()["activity_type_breakdown"]["ACTION_CREATED"] == 1

    search_response = client.get(
        "/projects/p1/workspace/activities/search",
        params={"q": "accepted"},
        headers=_auth_headers(),
    )
    assert search_response.status_code == 200
    assert search_response.json()["total"] == 1

    grouped_response = client.get(
        "/projects/p1/workspace/grouped",
        params={"group_by": "activity_type"},
        headers=_auth_headers(),
    )
    assert grouped_response.status_code == 200
    assert grouped_response.json()["total_groups"] >= 2

    operational_feed_response = client.get(
        "/projects/p1/workspace/live-operational-feed",
        headers=_auth_headers(),
    )
    assert operational_feed_response.status_code == 200
    assert operational_feed_response.json()["total"] == 1


def test_workspace_permissions_endpoint(monkeypatch):
    client = _client(monkeypatch)
    response = client.get("/projects/p1/workspace/permissions", headers=_auth_headers())
    assert response.status_code == 200
    assert response.json()["permissions"]["can_edit_layout"] is True
