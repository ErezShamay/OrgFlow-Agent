from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.auth.jwt_service import JWTService
from app.auth.permissions import resolve_permissions
from app.auth.role_labels import ROLE_DESCRIPTIONS_HE, ROLE_LABELS_HE
from app.auth.roles import CLIENT_ADMIN_INVITE_ROLES, inviteable_roles
from app.exceptions.exceptions import ValidationError
from app.main import app
from app.schemas.contractor_access import (
    CONTRACTOR_DENIED_PERMISSIONS,
    CONTRACTOR_GRANTED_PERMISSIONS,
    contractor_has_limited_access,
    is_contractor_role,
)
from app.services.user_management_service import UserManagementService


def _build_access_token(role: str = "CONTRACTOR") -> str:
    return JWTService().issue_access_token(
        user_id="contractor-1",
        org_id="org-1",
        role=role,
        token_id="token-qc-4-2-1",
    )


def _auth_headers(role: str = "CONTRACTOR") -> dict[str, str]:
    return {
        "Authorization": f"Bearer {_build_access_token(role=role)}",
        "X-Organization-ID": "org-1",
    }


def test_contractor_role_is_inviteable_by_admin() -> None:
    assert "CONTRACTOR" in inviteable_roles("ADMIN")
    assert "CONTRACTOR" in inviteable_roles("PLATFORM_ADMIN")
    assert "CONTRACTOR" in CLIENT_ADMIN_INVITE_ROLES
    assert "CONTRACTOR" not in inviteable_roles("SUPERVISOR")


def test_contractor_role_labels_defined() -> None:
    assert ROLE_LABELS_HE["CONTRACTOR"] == "קבלן"
    assert "ליקויים" in ROLE_DESCRIPTIONS_HE["CONTRACTOR"]


def test_contractor_has_limited_permission_profile() -> None:
    assert is_contractor_role("CONTRACTOR") is True
    assert contractor_has_limited_access("CONTRACTOR") is True

    permissions = resolve_permissions("CONTRACTOR")
    for granted in CONTRACTOR_GRANTED_PERMISSIONS:
        assert granted in permissions
    for denied in CONTRACTOR_DENIED_PERMISSIONS:
        assert denied not in permissions


def test_contractor_auth_me_exposes_limited_permissions() -> None:
    client = TestClient(app)

    response = client.get("/auth/me", headers=_auth_headers("CONTRACTOR"))

    assert response.status_code == 200
    body = response.json()
    assert body["role"] == "CONTRACTOR"
    permissions = set(body["permissions"])
    assert "quality_issues:read" in permissions
    assert "quality_issues:remediate" in permissions
    assert "field_reports:read" not in permissions
    assert "quality_portfolio:read" not in permissions


def test_contractor_blocked_from_portfolio_quality_summary() -> None:
    client = TestClient(app)

    response = client.get(
        "/portfolio/quality-summary",
        headers=_auth_headers("CONTRACTOR"),
    )

    assert response.status_code == 403


def test_contractor_lacks_field_reports_read_permission() -> None:
    permissions = resolve_permissions("CONTRACTOR")
    assert "field_reports:read" not in permissions
    assert "quality_issues:remediate" in permissions


def test_contractor_blocked_from_field_reports_home() -> None:
    client = TestClient(app)

    response = client.get(
        "/field-reports/home",
        headers=_auth_headers("CONTRACTOR"),
    )

    assert response.status_code == 403


def test_admin_can_assign_contractor_role_on_invite_validation() -> None:
    service = UserManagementService(
        profile_repository=MagicMock(
            list_profiles_by_organization=MagicMock(return_value=[]),
            count_profiles_with_role=MagicMock(return_value=0),
        )
    )

    with pytest.raises(ValidationError):
        service.invite_user(
            organization_id="org-1",
            email="user@example.com",
            full_name="Test User",
            role="CONTRACTOR",
            invited_by="supervisor-1",
            inviter_role="SUPERVISOR",
        )

    allowed_roles = service._allowed_roles_for_inviter("ADMIN")
    assert "CONTRACTOR" in allowed_roles
