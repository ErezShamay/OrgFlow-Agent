from fastapi.testclient import TestClient

import app.main as main_module
from app.auth.jwt_service import JWTService
from app.main import app
from app.services.notification_service import NotificationService
import app.dependencies as deps
import app.services.connection_managers as conn_mgrs


def _auth_headers():
    token = JWTService().issue_access_token(
        user_id="user-1",
        org_id="org-1",
        role="MANAGER",
        token_id="notifications-tests",
    )
    return {"Authorization": f"Bearer {token}", "X-Organization-ID": "org-1"}


def _client(monkeypatch):
    monkeypatch.setattr(deps, "notification_service", NotificationService())
    monkeypatch.setattr(
        conn_mgrs,
        "notification_connection_manager",
        conn_mgrs.NotificationConnectionManager(),
    )
    return TestClient(app)


def test_realtime_notifications_and_in_app_banners(monkeypatch):
    client = _client(monkeypatch)
    with client.websocket_connect("/profiles/u1/notifications/stream") as websocket:
        response = client.post(
            "/profiles/u1/notifications",
            json={
                "title": "Permit overdue",
                "message": "Action SLA breached",
                "notification_type": "ACTION",
                "banner": True,
            },
            headers=_auth_headers(),
        )
        assert response.status_code == 200
        pushed = websocket.receive_json()
        assert pushed["event"] == "notification.created"
        assert pushed["notification"]["in_app_banner"] is True


def test_email_push_and_multi_channel_delivery(monkeypatch):
    client = _client(monkeypatch)
    response = client.post(
        "/profiles/u1/notifications",
        json={
            "title": "Review update",
            "message": "Review moved to approved",
            "notification_type": "REVIEW",
            "channels": ["EMAIL", "PUSH", "IN_APP"],
        },
        headers=_auth_headers(),
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "DELIVERED"
    assert sorted(payload["delivery"]["delivered_channels"]) == ["EMAIL", "IN_APP", "PUSH"]


def test_digest_notifications(monkeypatch):
    client = _client(monkeypatch)
    client.post(
        "/profiles/u1/notifications",
        json={"title": "A", "message": "m1", "notification_type": "REVIEW"},
        headers=_auth_headers(),
    )
    client.post(
        "/profiles/u1/notifications",
        json={"title": "B", "message": "m2", "notification_type": "ACTION"},
        headers=_auth_headers(),
    )

    digest_response = client.get("/profiles/u1/notifications/digest", headers=_auth_headers())
    assert digest_response.status_code == 200
    assert digest_response.json()["total_notifications"] == 2
    assert len(digest_response.json()["sections"]) >= 2


def test_notification_preferences_and_categories(monkeypatch):
    client = _client(monkeypatch)
    set_response = client.put(
        "/profiles/u1/notifications/preferences",
        json={
            "channels": {"email": False, "push": True},
            "categories": {"review": True, "marketing": False},
        },
        headers=_auth_headers(),
    )
    assert set_response.status_code == 200
    assert set_response.json()["channels"]["EMAIL"] is False

    get_response = client.get("/profiles/u1/notifications/preferences", headers=_auth_headers())
    assert get_response.status_code == 200
    assert get_response.json()["categories"]["MARKETING"] is False

    category_response = client.get("/profiles/u1/notifications/categories", headers=_auth_headers())
    assert category_response.status_code == 200
    assert "ESCALATION" in category_response.json()["categories"]


def test_notification_center_polish_and_unread_sync(monkeypatch):
    client = _client(monkeypatch)
    first = client.post(
        "/profiles/u1/notifications",
        json={"title": "A", "message": "m1", "notification_type": "GENERAL"},
        headers=_auth_headers(),
    ).json()
    second = client.post(
        "/profiles/u1/notifications",
        json={"title": "B", "message": "m2", "notification_type": "GENERAL", "banner": True},
        headers=_auth_headers(),
    ).json()

    center_response = client.get("/profiles/u1/notification-center", headers=_auth_headers())
    assert center_response.status_code == 200
    assert center_response.json()["total"] == 2
    assert center_response.json()["unread_count"] == 2
    assert center_response.json()["banner_count"] == 1

    sync_response = client.patch(
        "/profiles/u1/notifications/read-sync",
        json={"read_ids": [first["id"]]},
        headers=_auth_headers(),
    )
    assert sync_response.status_code == 200
    assert sync_response.json()["updated"] == 1

    unread_response = client.get("/profiles/u1/notifications/unread", headers=_auth_headers())
    assert unread_response.status_code == 200
    assert unread_response.json()["total"] == 1
    assert unread_response.json()["items"][0]["id"] == second["id"]


def test_notification_retries_and_delivery_log(monkeypatch):
    client = _client(monkeypatch)
    failed = client.post(
        "/profiles/u1/notifications",
        json={
            "title": "Retry me",
            "message": "email provider down",
            "notification_type": "ACTION",
            "channels": ["EMAIL"],
            "force_fail_channels": ["EMAIL"],
        },
        headers=_auth_headers(),
    )
    assert failed.status_code == 200
    assert failed.json()["status"] == "RETRYING"

    retry_response = client.post("/profiles/u1/notifications/retry", headers=_auth_headers())
    assert retry_response.status_code == 200
    assert retry_response.json()["retried"] == 1
    assert retry_response.json()["items"][0]["status"] == "DELIVERED"

    log_response = client.get("/profiles/u1/notifications/delivery-log", headers=_auth_headers())
    assert log_response.status_code == 200
    assert log_response.json()["total_attempts"] >= 2


def test_escalation_notifications(monkeypatch):
    client = _client(monkeypatch)
    response = client.post(
        "/profiles/u1/notifications/escalation",
        json={
            "title": "L2 escalation",
            "message": "Escalated because SLA is breached",
            "escalation_level": "L2_MANAGER",
        },
        headers=_auth_headers(),
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["notification_type"] == "ESCALATION"
    assert payload["escalation_level"] == "L2_MANAGER"
    assert payload["status"] == "ESCALATED"
