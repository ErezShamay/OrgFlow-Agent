from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.auth.jwt_service import JWTService
from app.main import app
from app.schemas.contractor_access import (
    contractor_can_access_catalog,
    contractor_can_access_field_reports,
)


def _build_access_token(*, role: str) -> str:
    return JWTService().issue_access_token(
        user_id="user-1",
        org_id="org-1",
        role=role,
        token_id=f"token-{role.lower()}",
    )


def _auth_headers(role: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {_build_access_token(role=role)}",
        "X-Organization-ID": "org-1",
    }


@pytest.mark.parametrize("role", ["CONTRACTOR"])
def test_contractor_cannot_access_field_report_catalog(role: str) -> None:
    client = TestClient(app)

    response = client.get(
        "/field-reports/catalog",
        headers=_auth_headers(role),
    )

    assert response.status_code == 403
    assert contractor_can_access_catalog(role) is False
    assert contractor_can_access_field_reports(role) is False


@pytest.mark.parametrize("role", ["CONTRACTOR"])
def test_contractor_cannot_access_field_report_offline_prep(role: str) -> None:
    client = TestClient(app)

    response = client.get(
        "/field-reports/offline-prep",
        headers=_auth_headers(role),
    )

    assert response.status_code == 403


def test_supervisor_has_field_report_and_catalog_access_helpers() -> None:
    assert contractor_can_access_field_reports("SUPERVISOR") is True
    assert contractor_can_access_catalog("SUPERVISOR") is True
