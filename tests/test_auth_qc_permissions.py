from __future__ import annotations

import pytest

from app.auth.permissions import (
    PERMISSION_MATRIX,
    QC_PERMISSIONS,
    resolve_permissions,
)


@pytest.mark.parametrize(
    ("role", "permission", "expected"),
    [
        ("SUPERVISOR", "quality_issues:read", True),
        ("SUPERVISOR", "quality_issues:write", True),
        ("SUPERVISOR", "quality_issues:verify", True),
        ("SUPERVISOR", "quality_issues:remediate", False),
        ("CONTRACTOR", "quality_issues:read", True),
        ("CONTRACTOR", "quality_issues:remediate", True),
        ("CONTRACTOR", "quality_issues:write", False),
        ("CONTRACTOR", "quality_portfolio:read", False),
        ("DEVELOPER", "quality_issues:read", True),
        ("DEVELOPER", "quality_portfolio:read", True),
        ("DEVELOPER", "quality_issues:write", False),
        ("ADMIN", "quality_issues:write", True),
        ("ADMIN", "users:write", True),
        ("VIEWER", "quality_issues:read", True),
        ("VIEWER", "quality_portfolio:read", True),
        ("VIEWER", "users:write", False),
        ("MANAGER", "quality_issues:verify", True),
        ("PLATFORM_ADMIN", "quality_issues:read", True),
        ("PLATFORM_ADMIN", "organizations:write", True),
    ],
)
def test_resolve_permissions_includes_qc_matrix(
    role: str,
    permission: str,
    expected: bool,
) -> None:
    assert (permission in resolve_permissions(role)) is expected


def test_qc_permissions_constant_lists_all_qc_scopes() -> None:
    assert "quality_issues:read" in QC_PERMISSIONS
    assert "quality_portfolio:read" in QC_PERMISSIONS
    assert len(QC_PERMISSIONS) == 5


def test_permission_matrix_includes_contractor_and_developer_roles() -> None:
    assert "CONTRACTOR" in PERMISSION_MATRIX
    assert "DEVELOPER" in PERMISSION_MATRIX
    assert "quality_issues:remediate" in PERMISSION_MATRIX["CONTRACTOR"]
    assert "quality_portfolio:read" in PERMISSION_MATRIX["DEVELOPER"]


def test_resolve_permissions_merges_unknown_role_qc_mapping() -> None:
    # VIEWER is legacy but maps to DEVELOPER QC persona via resolve_qc_permissions.
    perms = resolve_permissions("VIEWER")
    assert "quality_issues:read" in perms
    assert "reports:read" in perms


def test_auth_me_exposes_contractor_limited_permissions() -> None:
    from fastapi.testclient import TestClient

    from app.auth.jwt_service import JWTService
    from app.main import app

    token = JWTService().issue_access_token(
        user_id="contractor-1",
        org_id="org-1",
        role="CONTRACTOR",
        token_id="token-contractor",
    )
    client = TestClient(app)

    response = client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {token}",
            "X-Organization-ID": "org-1",
        },
    )

    assert response.status_code == 200
    permissions = set(response.json()["permissions"])
    assert "quality_issues:read" in permissions
    assert "quality_issues:remediate" in permissions
    assert "field_reports:read" not in permissions
    assert "quality_portfolio:read" not in permissions


def test_auth_me_exposes_qc_permissions_in_session() -> None:
    from fastapi.testclient import TestClient

    from app.auth.jwt_service import JWTService
    from app.main import app

    token = JWTService().issue_access_token(
        user_id="supervisor-1",
        org_id="org-1",
        role="SUPERVISOR",
        token_id="token-qc",
    )
    client = TestClient(app)

    response = client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {token}",
            "X-Organization-ID": "org-1",
        },
    )

    assert response.status_code == 200
    permissions = response.json()["permissions"]
    assert "quality_issues:read" in permissions
    assert "quality_issues:write" in permissions
    assert "quality_portfolio:read" in permissions
