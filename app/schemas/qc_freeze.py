"""
QC Spec 0.5 - Freeze list: surfaces not developed during QC pivot.

See docs/qc-spec/qc-freeze-list.md.
"""

from __future__ import annotations

from enum import StrEnum
from typing import NamedTuple


class QCFreezeCategory(StrEnum):
    FROZEN = "FROZEN"
    DEPRECATED = "DEPRECATED"
    ADMIN_ONLY = "ADMIN_ONLY"
    SECONDARY = "SECONDARY"


class QCFrozenSurfaceId(StrEnum):
    AGENT_ORCHESTRATOR = "agent_orchestrator"
    AUTOMATION_ENGINE = "automation_engine"
    OPERATIONAL_ACTIONS = "operational_actions"
    AI_UPLOAD_PIPELINE = "ai_upload_pipeline"
    WORKFLOW_RUNS = "workflow_runs"
    AUTONOMOUS_RECOVERY_AGENTS = "autonomous_recovery_agents"
    UPLOAD_LEGACY = "upload_legacy"
    REVIEWS_GLOBAL = "reviews_global"
    ACTIONS_GLOBAL = "actions_global"
    ESCALATIONS_GLOBAL = "escalations_global"
    TENANTS_MANAGER = "tenants_manager"
    ALERTS_GLOBAL = "alerts_global"
    AUTOMATION_UI = "automation_ui"
    DEAD_LETTERS = "dead_letters"
    REVIEWS_PROJECT = "reviews_project"


class QCFrozenSurface(NamedTuple):
    id: QCFrozenSurfaceId
    label_he: str
    category: QCFreezeCategory
    ui_routes: tuple[str, ...]
    api_prefixes: tuple[str, ...]
    code_paths: tuple[str, ...]
    qc_replacement: str | None


QC_FROZEN_SURFACES: tuple[QCFrozenSurface, ...] = (
    QCFrozenSurface(
        id=QCFrozenSurfaceId.AGENT_ORCHESTRATOR,
        label_he="Agent Orchestrator",
        category=QCFreezeCategory.FROZEN,
        ui_routes=(),
        api_prefixes=("/agent/run",),
        code_paths=("app/agent/orchestrator.py",),
        qc_replacement="דוחות שטח + materialization",
    ),
    QCFrozenSurface(
        id=QCFrozenSurfaceId.AUTOMATION_ENGINE,
        label_he="מנוע אוטומציה",
        category=QCFreezeCategory.FROZEN,
        ui_routes=("/automation",),
        api_prefixes=("/automation/",),
        code_paths=("app/services/automation_rules_engine.py",),
        qc_replacement="התראות ידניות (שלב 4.3)",
    ),
    QCFrozenSurface(
        id=QCFrozenSurfaceId.OPERATIONAL_ACTIONS,
        label_he="פעולות תפעוליות",
        category=QCFreezeCategory.FROZEN,
        ui_routes=("/actions",),
        api_prefixes=("/actions/",),
        code_paths=("app/services/operational_action_service.py",),
        qc_replacement="quality_issues lifecycle",
    ),
    QCFrozenSurface(
        id=QCFrozenSurfaceId.AI_UPLOAD_PIPELINE,
        label_he="העלאת דוח → findings",
        category=QCFreezeCategory.FROZEN,
        ui_routes=("/upload", "/field-reports/upload"),
        api_prefixes=(
            "/reports/upload",
            "/reports/upload/bulk",
        ),
        code_paths=("app/services/report_processing_service.py",),
        qc_replacement="דוחות שטח + registry (שלב 5.7)",
    ),
    QCFrozenSurface(
        id=QCFrozenSurfaceId.WORKFLOW_RUNS,
        label_he="היסטוריית workflow",
        category=QCFreezeCategory.FROZEN,
        ui_routes=(),
        api_prefixes=("/workflow-runs",),
        code_paths=(),
        qc_replacement=None,
    ),
    QCFrozenSurface(
        id=QCFrozenSurfaceId.AUTONOMOUS_RECOVERY_AGENTS,
        label_he="סוכני recovery אוטונומיים",
        category=QCFreezeCategory.FROZEN,
        ui_routes=(),
        api_prefixes=(),
        code_paths=("app/services/autonomous_recovery_agents_service.py",),
        qc_replacement=None,
    ),
    QCFrozenSurface(
        id=QCFrozenSurfaceId.UPLOAD_LEGACY,
        label_he="העלאת דוח",
        category=QCFreezeCategory.DEPRECATED,
        ui_routes=("/upload", "/field-reports/upload"),
        api_prefixes=("/reports/upload",),
        code_paths=(
            "orgflow-ui/app/(dashboard)/upload/page.tsx",
            "orgflow-ui/app/(dashboard)/field-reports/upload/page.tsx",
        ),
        qc_replacement="field_visit_reports",
    ),
    QCFrozenSurface(
        id=QCFrozenSurfaceId.REVIEWS_GLOBAL,
        label_he="ביקורות AI (גלובלי)",
        category=QCFreezeCategory.DEPRECATED,
        ui_routes=("/reviews",),
        api_prefixes=("/reviews/",),
        code_paths=("orgflow-ui/app/(dashboard)/reviews/page.tsx",),
        qc_replacement="ליקויים + דוחות שטח",
    ),
    QCFrozenSurface(
        id=QCFrozenSurfaceId.ACTIONS_GLOBAL,
        label_he="פעולות תפעוליות",
        category=QCFreezeCategory.DEPRECATED,
        ui_routes=("/actions",),
        api_prefixes=("/actions/",),
        code_paths=("orgflow-ui/app/(dashboard)/actions/page.tsx",),
        qc_replacement="quality_issues",
    ),
    QCFrozenSurface(
        id=QCFrozenSurfaceId.ESCALATIONS_GLOBAL,
        label_he="נקודות סיכון",
        category=QCFreezeCategory.DEPRECATED,
        ui_routes=("/escalations",),
        api_prefixes=("/actions/escalations",),
        code_paths=("orgflow-ui/app/(dashboard)/escalations/page.tsx",),
        qc_replacement="quality_issues",
    ),
    QCFrozenSurface(
        id=QCFrozenSurfaceId.TENANTS_MANAGER,
        label_he="מנהל דיירים",
        category=QCFreezeCategory.DEPRECATED,
        ui_routes=("/tenants",),
        api_prefixes=(),
        code_paths=("orgflow-ui/app/(dashboard)/tenants/page.tsx",),
        qc_replacement=None,
    ),
    QCFrozenSurface(
        id=QCFrozenSurfaceId.ALERTS_GLOBAL,
        label_he="התראות",
        category=QCFreezeCategory.DEPRECATED,
        ui_routes=("/alerts",),
        api_prefixes=(),
        code_paths=("orgflow-ui/app/(dashboard)/alerts/page.tsx",),
        qc_replacement="התראות QC (שלב 4.3)",
    ),
    QCFrozenSurface(
        id=QCFrozenSurfaceId.AUTOMATION_UI,
        label_he="אוטומציה",
        category=QCFreezeCategory.ADMIN_ONLY,
        ui_routes=("/automation",),
        api_prefixes=("/automation/",),
        code_paths=("orgflow-ui/app/(dashboard)/automation/page.tsx",),
        qc_replacement=None,
    ),
    QCFrozenSurface(
        id=QCFrozenSurfaceId.DEAD_LETTERS,
        label_he="Dead Letters",
        category=QCFreezeCategory.ADMIN_ONLY,
        ui_routes=("/automation/dead-letters",),
        api_prefixes=(),
        code_paths=(
            "orgflow-ui/app/(dashboard)/automation/dead-letters/page.tsx",
        ),
        qc_replacement=None,
    ),
    QCFrozenSurface(
        id=QCFrozenSurfaceId.REVIEWS_PROJECT,
        label_he="ביקורות AI (פרויקט)",
        category=QCFreezeCategory.SECONDARY,
        ui_routes=(),
        api_prefixes=("/reviews/",),
        code_paths=(
            "orgflow-ui/app/(dashboard)/projects/[id]/reviews/page.tsx",
        ),
        qc_replacement="ליקויים בפרויקט",
    ),
)

QC_ALLOWED_EXCEPTIONS: frozenset[str] = frozenset(
    {
        "NotificationTool",
        "QcNotificationService",
        "field_report_catalog_parser",
        "ReportProcessingService",
    }
)

_SURFACES_BY_ID: dict[QCFrozenSurfaceId, QCFrozenSurface] = {
    surface.id: surface for surface in QC_FROZEN_SURFACES
}

_DEPRECATED_UI_ROUTES: frozenset[str] = frozenset(
    route
    for surface in QC_FROZEN_SURFACES
    if surface.category == QCFreezeCategory.DEPRECATED
    for route in surface.ui_routes
)

_FROZEN_API_PREFIXES: tuple[str, ...] = tuple(
    prefix
    for surface in QC_FROZEN_SURFACES
    if surface.category == QCFreezeCategory.FROZEN
    for prefix in surface.api_prefixes
)


def get_frozen_surface(surface_id: str | QCFrozenSurfaceId) -> QCFrozenSurface | None:
    try:
        key = QCFrozenSurfaceId(surface_id)
    except ValueError:
        return None
    return _SURFACES_BY_ID.get(key)


def is_frozen_surface(surface_id: str | QCFrozenSurfaceId) -> bool:
    surface = get_frozen_surface(surface_id)
    return surface is not None and surface.category == QCFreezeCategory.FROZEN


def is_deprecated_route(href: str) -> bool:
    normalized = (href or "").strip().rstrip("/") or "/"
    return normalized in _DEPRECATED_UI_ROUTES


def is_frozen_api_path(path: str) -> bool:
    normalized = (path or "").strip()
    return any(
        normalized == prefix or normalized.startswith(prefix)
        for prefix in _FROZEN_API_PREFIXES
    )


def list_surfaces_by_category(
    category: QCFreezeCategory,
) -> list[QCFrozenSurface]:
    return [
        surface
        for surface in QC_FROZEN_SURFACES
        if surface.category == category
    ]


def is_allowed_qc_exception(component_name: str) -> bool:
    return component_name in QC_ALLOWED_EXCEPTIONS


class QCFrozenFeatureError(RuntimeError):
    """Raised when QC code attempts to extend a frozen surface."""


def assert_not_frozen_for_feature(
    surface_id: str | QCFrozenSurfaceId,
) -> None:
    """Guard for CI and development - frozen surfaces must not gain new features."""
    if not is_frozen_surface(surface_id):
        return

    surface = get_frozen_surface(surface_id)
    message = f"QC freeze: surface '{surface_id}' is frozen"
    if surface and surface.qc_replacement:
        message += f"; use {surface.qc_replacement} instead"
    raise QCFrozenFeatureError(message)


def get_frozen_surface_for_api_path(path: str) -> QCFrozenSurface | None:
    normalized = (path or "").strip()
    for surface in QC_FROZEN_SURFACES:
        if surface.category != QCFreezeCategory.FROZEN:
            continue
        for prefix in surface.api_prefixes:
            if normalized == prefix or normalized.startswith(prefix):
                return surface
    return None


def raise_if_frozen_api_path(path: str) -> None:
    """Block HTTP handlers for frozen QC API surfaces (stage 5.6+)."""
    from fastapi import HTTPException

    surface = get_frozen_surface_for_api_path(path)
    if surface is None:
        return

    raise HTTPException(
        status_code=403,
        detail={
            "code": "qc_frozen_surface",
            "surface_id": surface.id.value,
            "message": (
                f"{surface.label_he} is frozen during QC pivot; "
                "no new development on this surface."
            ),
            "qc_replacement": surface.qc_replacement,
        },
    )
