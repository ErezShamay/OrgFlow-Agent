"""Gate test - roadmap 5.6 Agent Orchestrator freeze."""

from __future__ import annotations

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.auth.jwt_service import JWTService
from app.main import app
from app.schemas.qc_freeze import (
    QCFrozenFeatureError,
    QCFrozenSurfaceId,
    assert_not_frozen_for_feature,
    get_frozen_surface_for_api_path,
    is_frozen_surface,
    raise_if_frozen_api_path,
)


def _auth_headers(role: str = "ADMIN") -> dict[str, str]:
    token = JWTService().issue_access_token(
        user_id="admin-1",
        org_id="org-1",
        role=role,
        token_id="token-qc-5-6",
    )
    return {"Authorization": f"Bearer {token}"}


def test_agent_orchestrator_surface_is_frozen() -> None:
    assert is_frozen_surface(QCFrozenSurfaceId.AGENT_ORCHESTRATOR) is True


def test_assert_not_frozen_for_feature_blocks_agent_orchestrator() -> None:
    with pytest.raises(QCFrozenFeatureError, match="agent_orchestrator"):
        assert_not_frozen_for_feature(QCFrozenSurfaceId.AGENT_ORCHESTRATOR)


def test_get_frozen_surface_for_agent_run_path() -> None:
    surface = get_frozen_surface_for_api_path("/agent/run")
    assert surface is not None
    assert surface.id == QCFrozenSurfaceId.AGENT_ORCHESTRATOR


def test_raise_if_frozen_api_path_blocks_agent_run() -> None:
    with pytest.raises(HTTPException) as exc_info:
        raise_if_frozen_api_path("/agent/run")

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail["surface_id"] == "agent_orchestrator"


def test_agent_run_api_returns_qc_frozen_403() -> None:
    client = TestClient(app)
    response = client.post(
        "/agent/run",
        json={"user_request": "בדוק פרויקטים"},
        headers=_auth_headers(),
    )

    assert response.status_code == 403
    payload = response.json()
    detail = payload["detail"]
    assert detail["code"] == "qc_frozen_surface"
    assert detail["surface_id"] == "agent_orchestrator"
    assert "materialization" in (detail.get("qc_replacement") or "")
