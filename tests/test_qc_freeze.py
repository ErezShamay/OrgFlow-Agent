from __future__ import annotations

import pytest

from app.schemas.qc_freeze import (
    QCFreezeCategory,
    QCFrozenFeatureError,
    QCFrozenSurfaceId,
    QC_FROZEN_SURFACES,
    assert_not_frozen_for_feature,
    is_allowed_qc_exception,
    is_deprecated_route,
    is_frozen_api_path,
    is_frozen_surface,
    list_surfaces_by_category,
)


def test_frozen_surfaces_include_core_pm_ai_items() -> None:
    ids = {surface.id for surface in QC_FROZEN_SURFACES}
    assert QCFrozenSurfaceId.AGENT_ORCHESTRATOR in ids
    assert QCFrozenSurfaceId.AI_UPLOAD_PIPELINE in ids
    assert QCFrozenSurfaceId.REVIEWS_GLOBAL in ids
    assert QCFrozenSurfaceId.AUTOMATION_UI in ids


def test_agent_orchestrator_is_frozen() -> None:
    assert is_frozen_surface("agent_orchestrator") is True
    assert is_frozen_surface("upload_legacy") is False


def test_deprecated_routes() -> None:
    assert is_deprecated_route("/upload") is True
    assert is_deprecated_route("/reviews") is True
    assert is_deprecated_route("/actions") is True
    assert is_deprecated_route("/portfolio") is False
    assert is_deprecated_route("/field-reports") is False


def test_frozen_api_paths() -> None:
    assert is_frozen_api_path("/agent/run") is True
    assert is_frozen_api_path("/reports/upload") is True
    assert is_frozen_api_path("/reports/upload/bulk") is True
    assert is_frozen_api_path("/automation/runs") is True
    assert is_frozen_api_path("/field-reports/abc") is False
    assert is_frozen_api_path("/projects/1/issues") is False


def test_list_surfaces_by_category() -> None:
    frozen = list_surfaces_by_category(QCFreezeCategory.FROZEN)
    deprecated = list_surfaces_by_category(QCFreezeCategory.DEPRECATED)
    assert len(frozen) >= 6
    assert len(deprecated) >= 5
    assert all(surface.category == QCFreezeCategory.FROZEN for surface in frozen)


def test_admin_only_surfaces() -> None:
    admin_only = list_surfaces_by_category(QCFreezeCategory.ADMIN_ONLY)
    ids = {surface.id for surface in admin_only}
    assert QCFrozenSurfaceId.AUTOMATION_UI in ids
    assert QCFrozenSurfaceId.DEAD_LETTERS in ids


def test_secondary_reviews_project() -> None:
    secondary = list_surfaces_by_category(QCFreezeCategory.SECONDARY)
    assert any(surface.id == QCFrozenSurfaceId.REVIEWS_PROJECT for surface in secondary)


def test_allowed_qc_exceptions() -> None:
    assert is_allowed_qc_exception("NotificationTool") is True
    assert is_allowed_qc_exception("Orchestrator") is False


def test_assert_not_frozen_for_feature_allows_non_frozen() -> None:
    assert_not_frozen_for_feature(QCFrozenSurfaceId.UPLOAD_LEGACY)


def test_assert_not_frozen_for_feature_blocks_agent_orchestrator() -> None:
    with pytest.raises(QCFrozenFeatureError, match="agent_orchestrator"):
        assert_not_frozen_for_feature(QCFrozenSurfaceId.AGENT_ORCHESTRATOR)
