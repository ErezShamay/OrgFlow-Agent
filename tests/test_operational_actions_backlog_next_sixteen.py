from fastapi.testclient import TestClient

import app.main as main_module
from app.auth.jwt_service import JWTService
from app.main import app
import app.dependencies as deps


class FakeProjectRepository:
    def __init__(self):
        self.projects = {"p1": {"id": "p1", "project_name": "Alpha Tower"}}

    def get_project_by_id(self, project_id: str):
        return self.projects.get(project_id)


class FakeOperationalActionService:
    def __init__(self):
        self.attachments = {}
        self.notifications = {}
        self.comments = {}
        self.history = {}
        self.templates = {"p1": []}
        self.recurring = {"p1": []}
        self.actions = {"a1": {"id": "a1", "title": "Escalate permit", "project_id": "p1", "status": "OPEN"}}

    def _push_history(self, action_id: str, event_type: str, payload: dict):
        self.history.setdefault(action_id, []).append({"event_type": event_type, "payload": payload})

    def get_action_priorities(self, project_id: str):
        return {
            "project_id": project_id,
            "total_actions": 2,
            "actions": [
                {"id": "a1", "priority": "HIGH", "priority_score": 90},
                {"id": "a2", "priority": "MEDIUM", "priority_score": 60},
            ],
        }

    def get_dependency_graph(self, project_id: str):
        return {
            "project_id": project_id,
            "nodes": [{"id": "a1"}, {"id": "a2"}],
            "edges": [{"source": "a1", "target": "a2", "type": "BLOCKS"}],
            "total_nodes": 2,
            "total_edges": 1,
        }

    def create_recurring_action(self, project_id: str, title: str, recurrence_rule: str, created_by: str):
        payload = {
            "id": "rec-1",
            "project_id": project_id,
            "title": title,
            "recurrence_rule": recurrence_rule,
            "created_by": created_by,
        }
        self.recurring.setdefault(project_id, []).append(payload)
        return payload

    def list_recurring_actions(self, project_id: str):
        items = self.recurring.get(project_id, [])
        return {"project_id": project_id, "total_recurring_actions": len(items), "items": items}

    def bulk_create_actions(self, project_id: str, actions: list[dict]):
        return {
            "project_id": project_id,
            "created_count": len(actions),
            "actions": [{"id": f"bulk-{idx+1}", **item} for idx, item in enumerate(actions)],
        }

    def add_attachment(self, action_id: str, filename: str, uploaded_by: str):
        payload = {"id": f"att-{len(self.attachments.get(action_id, [])) + 1}", "filename": filename, "uploaded_by": uploaded_by}
        self.attachments.setdefault(action_id, []).append(payload)
        self._push_history(action_id, "ATTACHMENT_ADDED", payload)
        return payload

    def list_attachments(self, action_id: str):
        return self.attachments.get(action_id, [])

    def delete_attachment(self, action_id: str, attachment_id: str):
        current = self.attachments.get(action_id, [])
        remaining = [item for item in current if item["id"] != attachment_id]
        if len(current) == len(remaining):
            return False
        self.attachments[action_id] = remaining
        self._push_history(action_id, "ATTACHMENT_DELETED", {"attachment_id": attachment_id})
        return True

    def create_notification(self, action_id: str, recipient_id: str, message: str, channel: str = "IN_APP"):
        payload = {"id": "n-1", "recipient_id": recipient_id, "message": message, "channel": channel}
        self.notifications.setdefault(action_id, []).append(payload)
        return payload

    def list_notifications(self, action_id: str):
        return self.notifications.get(action_id, [])

    def get_action_analytics(self, project_id: str):
        return {"project_id": project_id, "total_open_actions": 4, "escalated_actions": 1, "blocked_actions": 1}

    def add_comment(self, action_id: str, comment: str, created_by: str):
        payload = {"id": "c-1", "comment": comment, "created_by": created_by}
        self.comments.setdefault(action_id, []).append(payload)
        self._push_history(action_id, "COMMENT_ADDED", payload)
        return payload

    def list_comments(self, action_id: str):
        return self.comments.get(action_id, [])

    def get_history(self, action_id: str):
        return self.history.get(action_id, [])

    def get_sla_dashboard(self, project_id: str):
        return {"project_id": project_id, "tracked_actions": 4, "breached_actions": 1}

    def retry_action(self, action_id: str, reason: str):
        payload = {"id": action_id, "status": "IN_PROGRESS", "retry_reason": reason}
        self._push_history(action_id, "RETRY_TRIGGERED", {"reason": reason})
        return payload

    def set_owner(self, action_id: str, owner_id: str):
        action = self.actions.setdefault(action_id, {"id": action_id})
        action["owner_id"] = owner_id
        self._push_history(action_id, "OWNER_UPDATED", {"owner_id": owner_id})
        return action

    def escalate_with_hierarchy(self, action_id: str, level: str, reason: str):
        action = self.actions.setdefault(action_id, {"id": action_id})
        action["status"] = "ESCALATED"
        action["escalation_level"] = level
        action["escalation_reason"] = reason
        self._push_history(action_id, "ESCALATION_LEVEL_SET", {"level": level, "reason": reason})
        return action

    def generate_ai_actions(self, project_id: str, context: str):
        return {
            "project_id": project_id,
            "generated_actions": [{"id": "ai-1", "title": f"AI: {context}", "confidence": 0.81}],
        }

    def create_template(self, project_id: str, name: str, title: str, description: str, category: str):
        payload = {
            "id": f"tpl-{len(self.templates.get(project_id, [])) + 1}",
            "name": name,
            "title": title,
            "description": description,
            "category": category,
        }
        self.templates.setdefault(project_id, []).append(payload)
        return payload

    def list_templates(self, project_id: str):
        templates = self.templates.get(project_id, [])
        return {"project_id": project_id, "total_templates": len(templates), "templates": templates}

    def apply_template(self, project_id: str, template_id: str, created_by: str):
        templates = self.templates.get(project_id, [])
        template = next((item for item in templates if item["id"] == template_id), None)
        if not template:
            return None
        return {"id": "a-from-template", "created_by": created_by, "title": template["title"], "action_type": template["category"]}

    def categorize_action(self, action_id: str, category: str):
        action = self.actions.get(action_id)
        if not action:
            return None
        action["category"] = category
        self._push_history(action_id, "CATEGORY_UPDATED", {"category": category})
        return action


def _auth_headers():
    token = JWTService().issue_access_token(
        user_id="user-1",
        org_id="org-1",
        role="MANAGER",
        token_id="operational-actions-tests",
    )
    return {"Authorization": f"Bearer {token}", "X-Organization-ID": "org-1"}


def _client(monkeypatch) -> TestClient:
    monkeypatch.setattr(deps, "project_repository", FakeProjectRepository())
    monkeypatch.setattr(deps, "operational_action_service", FakeOperationalActionService())
    return TestClient(app)


def test_action_priorities_engine(monkeypatch):
    client = _client(monkeypatch)
    response = client.get("/projects/p1/actions/priorities", headers=_auth_headers())
    assert response.status_code == 200
    assert response.json()["actions"][0]["priority"] == "HIGH"


def test_action_dependency_graph(monkeypatch):
    client = _client(monkeypatch)
    response = client.get("/projects/p1/actions/dependency-graph", headers=_auth_headers())
    assert response.status_code == 200
    assert response.json()["total_edges"] == 1


def test_recurring_actions(monkeypatch):
    client = _client(monkeypatch)
    create_response = client.post(
        "/projects/p1/actions/recurring",
        json={"title": "Weekly safety check", "recurrence_rule": "FREQ=WEEKLY", "created_by": "dana"},
        headers=_auth_headers(),
    )
    assert create_response.status_code == 200
    list_response = client.get("/projects/p1/actions/recurring", headers=_auth_headers())
    assert list_response.status_code == 200
    assert list_response.json()["total_recurring_actions"] == 1


def test_bulk_actions(monkeypatch):
    client = _client(monkeypatch)
    response = client.post(
        "/projects/p1/actions/bulk",
        json={"actions": [{"title": "Action 1"}, {"title": "Action 2"}]},
        headers=_auth_headers(),
    )
    assert response.status_code == 200
    assert response.json()["created_count"] == 2


def test_action_attachments(monkeypatch):
    client = _client(monkeypatch)
    create_response = client.post(
        "/projects/p1/actions/a1/attachments",
        json={"filename": "brief.pdf", "uploaded_by": "dana"},
        headers=_auth_headers(),
    )
    assert create_response.status_code == 200
    list_response = client.get("/projects/p1/actions/a1/attachments", headers=_auth_headers())
    assert list_response.status_code == 200
    assert len(list_response.json()["attachments"]) == 1
    delete_response = client.delete("/projects/p1/actions/a1/attachments/att-1", headers=_auth_headers())
    assert delete_response.status_code == 200


def test_action_notifications(monkeypatch):
    client = _client(monkeypatch)
    create_response = client.post(
        "/projects/p1/actions/a1/notifications",
        json={"recipient_id": "u2", "message": "Action updated", "channel": "EMAIL"},
        headers=_auth_headers(),
    )
    assert create_response.status_code == 200
    list_response = client.get("/projects/p1/actions/a1/notifications", headers=_auth_headers())
    assert list_response.status_code == 200
    assert len(list_response.json()["notifications"]) == 1


def test_action_analytics_dashboard(monkeypatch):
    client = _client(monkeypatch)
    response = client.get("/projects/p1/actions/analytics", headers=_auth_headers())
    assert response.status_code == 200
    assert response.json()["total_open_actions"] == 4


def test_action_comments(monkeypatch):
    client = _client(monkeypatch)
    create_response = client.post(
        "/projects/p1/actions/a1/comments",
        json={"comment": "Need municipal approval", "created_by": "dana"},
        headers=_auth_headers(),
    )
    assert create_response.status_code == 200
    list_response = client.get("/projects/p1/actions/a1/comments", headers=_auth_headers())
    assert list_response.status_code == 200
    assert len(list_response.json()["comments"]) == 1


def test_action_history(monkeypatch):
    client = _client(monkeypatch)
    client.post(
        "/projects/p1/actions/a1/comments",
        json={"comment": "Tracking for history", "created_by": "dana"},
        headers=_auth_headers(),
    )
    response = client.get("/projects/p1/actions/a1/history", headers=_auth_headers())
    assert response.status_code == 200
    assert len(response.json()["history"]) == 1


def test_action_sla_enforcement(monkeypatch):
    client = _client(monkeypatch)
    response = client.get("/projects/p1/actions/sla", headers=_auth_headers())
    assert response.status_code == 200
    assert response.json()["breached_actions"] == 1


def test_action_retry_flows(monkeypatch):
    client = _client(monkeypatch)
    response = client.post(
        "/projects/p1/actions/a1/retry",
        json={"reason": "External API timeout"},
        headers=_auth_headers(),
    )
    assert response.status_code == 200
    assert response.json()["status"] == "IN_PROGRESS"


def test_action_ownership(monkeypatch):
    client = _client(monkeypatch)
    response = client.patch(
        "/projects/p1/actions/a1/owner",
        json={"owner_id": "owner-2"},
        headers=_auth_headers(),
    )
    assert response.status_code == 200
    assert response.json()["owner_id"] == "owner-2"


def test_escalation_hierarchy(monkeypatch):
    client = _client(monkeypatch)
    response = client.post(
        "/projects/p1/actions/a1/escalate",
        json={"level": "L2_MANAGER", "reason": "SLA breach"},
        headers=_auth_headers(),
    )
    assert response.status_code == 200
    assert response.json()["escalation_level"] == "L2_MANAGER"


def test_ai_generated_actions(monkeypatch):
    client = _client(monkeypatch)
    response = client.post(
        "/projects/p1/actions/ai-generate",
        json={"context": "Delay in concrete delivery"},
        headers=_auth_headers(),
    )
    assert response.status_code == 200
    assert len(response.json()["generated_actions"]) == 1


def test_action_templates(monkeypatch):
    client = _client(monkeypatch)
    create_response = client.post(
        "/projects/p1/actions/templates",
        json={
            "name": "delay-template",
            "title": "Mitigate schedule delay",
            "description": "Coordinate timeline recovery",
            "category": "FOLLOW_UP",
        },
        headers=_auth_headers(),
    )
    assert create_response.status_code == 200
    list_response = client.get("/projects/p1/actions/templates", headers=_auth_headers())
    assert list_response.status_code == 200
    assert list_response.json()["total_templates"] == 1
    apply_response = client.post(
        "/projects/p1/actions/templates/tpl-1/apply",
        json={"created_by": "dana"},
        headers=_auth_headers(),
    )
    assert apply_response.status_code == 200
    assert apply_response.json()["action_type"] == "FOLLOW_UP"


def test_action_categorization(monkeypatch):
    client = _client(monkeypatch)
    response = client.patch(
        "/projects/p1/actions/a1/category",
        json={"category": "COMPLIANCE"},
        headers=_auth_headers(),
    )
    assert response.status_code == 200
    assert response.json()["category"] == "COMPLIANCE"
