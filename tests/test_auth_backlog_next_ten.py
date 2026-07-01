from __future__ import annotations

from datetime import UTC, datetime, timedelta

import jwt
from fastapi.testclient import TestClient

import app.main as main_module
from app.auth.jwt_service import JWTService
from app.config import config_manager
from app.main import app
import app.dependencies as deps


def _build_access_token(
    *,
    user_id: str = "user-1",
    org_id: str = "org-1",
    role: str = "ANALYST",
) -> str:
    return JWTService().issue_access_token(
        user_id=user_id,
        org_id=org_id,
        role=role,
        token_id="token-1",
    )


def _build_refresh_token(
    *,
    user_id: str = "user-1",
    org_id: str = "org-1",
    role: str = "ANALYST",
) -> str:
    return JWTService().issue_refresh_token(
        user_id=user_id,
        org_id=org_id,
        role=role,
        token_id="refresh-1",
    )


def test_jwt_validation_middleware_rejects_missing_token():
    client = TestClient(app)
    response = client.get("/auth/me")
    assert response.status_code == 401


def test_role_permissions_allow_authorized_endpoint():
    client = TestClient(app)
    token = _build_access_token(role="MANAGER")
    response = client.get(
        "/auth/secure/reports",
        headers={"Authorization": f"Bearer {token}", "X-Organization-ID": "org-1"},
    )
    assert response.status_code == 200


def test_permission_matrix_blocks_insufficient_role():
    client = TestClient(app)
    token = _build_access_token(role="VIEWER")
    response = client.get(
        "/auth/secure/admin",
        headers={"Authorization": f"Bearer {token}", "X-Organization-ID": "org-1"},
    )
    assert response.status_code == 403


def test_organization_isolation_blocks_cross_tenant_access():
    client = TestClient(app)
    token = _build_access_token(org_id="org-a")
    response = client.get(
        "/auth/tenant/check",
        headers={"Authorization": f"Bearer {token}", "X-Organization-ID": "org-b"},
    )
    assert response.status_code == 403


def test_admin_impersonation_supported_for_admin_role():
    client = TestClient(app)
    token = _build_access_token(user_id="admin-1", role="PLATFORM_ADMIN")
    response = client.get(
        "/auth/impersonation/status",
        headers={
            "Authorization": f"Bearer {token}",
            "X-Organization-ID": "org-1",
            "X-Impersonate-User": "analyst-42",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["is_impersonating"] is True
    assert payload["effective_user_id"] == "analyst-42"


def test_non_admin_impersonation_is_forbidden():
    client = TestClient(app)
    token = _build_access_token(role="ANALYST")
    response = client.get(
        "/auth/impersonation/status",
        headers={
            "Authorization": f"Bearer {token}",
            "X-Organization-ID": "org-1",
            "X-Impersonate-User": "viewer-1",
        },
    )
    assert response.status_code == 403


def test_refresh_token_flow_issues_new_access_token():
    client = TestClient(app)
    refresh = _build_refresh_token(role="MANAGER")
    response = client.post("/auth/refresh", headers={"Authorization": f"Bearer {refresh}"})
    assert response.status_code == 200
    assert response.json()["access_token"]


def test_session_timeout_handling_rejects_stale_access_token():
    settings = config_manager.get_settings()
    stale_auth_time = datetime.now(UTC) - timedelta(minutes=settings.AUTH_SESSION_TIMEOUT_MINUTES + 5)
    payload = {
        "sub": "user-timeout",
        "org_id": "org-1",
        "role": "ANALYST",
        "jti": "stale-token",
        "typ": "access",
        "auth_time": stale_auth_time.timestamp(),
        "iat": stale_auth_time.timestamp(),
        "exp": (datetime.now(UTC) + timedelta(minutes=5)).timestamp(),
    }
    stale_token = jwt.encode(payload, settings.AUTH_JWT_SECRET, algorithm=settings.AUTH_JWT_ALGORITHM)
    client = TestClient(app)
    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {stale_token}", "X-Organization-ID": "org-1"},
    )
    assert response.status_code == 401


def test_permission_matrix_endpoint_available():
    client = TestClient(app)
    response = client.get("/auth/permission-matrix")
    assert response.status_code == 401
    # Endpoint is auth-protected by middleware but still registered.
    assert any(route.path == "/auth/permission-matrix" for route in app.routes)


def test_auth_exchange_issues_access_token(monkeypatch):
    class FakeProfileService:
        def get_profile(self, profile_id: str):
            return {
                "id": profile_id,
                "organization_id": "org-1",
                "role": "MANAGER",
                "email": "manager@example.com",
            }

        def ensure_organization_id(
            self,
            profile_id: str,
            *,
            preferred_organization_id: str | None = None,
        ):
            return preferred_organization_id or "org-1"

    monkeypatch.setattr(deps, "profile_service", FakeProfileService())
    client = TestClient(app)

    response = client.post(
        "/auth/exchange",
        json={"user_id": "user-1"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["access_token"]
    assert payload["org_id"] == "org-1"
    assert payload["role"] == "MANAGER"
