"""
QC Spec 4.2.1 - Contractor persona access profile (limited permissions).

See docs/qc-spec/qc-personas-permissions.md §2.2.
"""

from __future__ import annotations

from app.schemas.qc_permissions import (
    QCPersona,
    has_qc_permission,
    resolve_qc_permissions,
    resolve_qc_persona,
    visible_issue_statuses_for_role,
)

CONTRACTOR_GRANTED_PERMISSIONS: tuple[str, ...] = (
    "quality_issues:read",
    "quality_issues:remediate",
    "projects:read",
)

CONTRACTOR_DENIED_PERMISSIONS: tuple[str, ...] = (
    "quality_issues:write",
    "quality_issues:verify",
    "quality_portfolio:read",
    "field_reports:read",
    "field_reports:write",
    "field_reports:admin",
    "reports:read",
    "reports:write",
    "users:read",
    "users:write",
    "audit:read",
)


def contractor_can_access_field_reports(role: str | None) -> bool:
    return has_qc_permission(role, "field_reports:read")


def contractor_can_access_catalog(role: str | None) -> bool:
    return contractor_can_access_field_reports(role)


def is_contractor_role(role: str | None) -> bool:
    return resolve_qc_persona(role) == QCPersona.CONTRACTOR


def contractor_has_limited_access(role: str | None) -> bool:
    if not is_contractor_role(role):
        return False

    permissions = resolve_qc_permissions(role)
    visible = visible_issue_statuses_for_role(role)

    return (
        has_qc_permission(role, "quality_issues:read")
        and has_qc_permission(role, "quality_issues:remediate")
        and not has_qc_permission(role, "field_reports:read")
        and not has_qc_permission(role, "quality_portfolio:read")
        and visible is not None
        and all(
            granted in permissions for granted in CONTRACTOR_GRANTED_PERMISSIONS
        )
        and all(
            denied not in permissions for denied in CONTRACTOR_DENIED_PERMISSIONS
        )
    )
