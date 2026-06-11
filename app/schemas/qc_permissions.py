"""
QC Spec 0.3 - Personas, permissions, and access rules for the QC platform.

See docs/qc-spec/qc-personas-permissions.md.
"""

from __future__ import annotations

from enum import StrEnum

from app.schemas.quality_issue import (
    QualityIssueStatus,
    is_valid_status_transition,
)


class QCPersona(StrEnum):
    SUPERVISOR = "SUPERVISOR"
    CONTRACTOR = "CONTRACTOR"
    DEVELOPER = "DEVELOPER"
    ADMIN = "ADMIN"

    @property
    def label_he(self) -> str:
        return _PERSONA_LABELS_HE[self]


_PERSONA_LABELS_HE: dict[QCPersona, str] = {
    QCPersona.SUPERVISOR: "מפקח",
    QCPersona.CONTRACTOR: "קבלן",
    QCPersona.DEVELOPER: "יזם",
    QCPersona.ADMIN: "מנהל",
}

QC_PERMISSIONS: tuple[str, ...] = (
    "quality_issues:read",
    "quality_issues:write",
    "quality_issues:remediate",
    "quality_issues:verify",
    "quality_portfolio:read",
    "field_reports:read",
    "field_reports:write",
    "field_reports:admin",
    "tenant_manager:admin",
    "projects:read",
    "projects:write",
    "users:read",
    "users:write",
    "audit:read",
)

_SYSTEM_ROLE_TO_QC_PERSONA: dict[str, QCPersona] = {
    "SUPERVISOR": QCPersona.SUPERVISOR,
    "CONTRACTOR": QCPersona.CONTRACTOR,
    "DEVELOPER": QCPersona.DEVELOPER,
    "ADMIN": QCPersona.ADMIN,
    "PLATFORM_ADMIN": QCPersona.ADMIN,
    "MANAGER": QCPersona.SUPERVISOR,
    "VIEWER": QCPersona.DEVELOPER,
    "ANALYST": QCPersona.DEVELOPER,
}

_QC_PERMISSION_MATRIX: dict[QCPersona, frozenset[str]] = {
    QCPersona.SUPERVISOR: frozenset(
        {
            "quality_issues:read",
            "quality_issues:write",
            "quality_issues:verify",
            "quality_portfolio:read",
            "field_reports:read",
            "field_reports:write",
            "projects:read",
            "projects:write",
            "audit:read",
        }
    ),
    QCPersona.CONTRACTOR: frozenset(
        {
            "quality_issues:read",
            "quality_issues:remediate",
            "projects:read",
        }
    ),
    QCPersona.DEVELOPER: frozenset(
        {
            "quality_issues:read",
            "quality_portfolio:read",
            "field_reports:read",
            "projects:read",
        }
    ),
    QCPersona.ADMIN: frozenset(
        {
            "quality_issues:read",
            "quality_issues:write",
            "quality_issues:verify",
            "quality_portfolio:read",
            "field_reports:read",
            "field_reports:write",
            "field_reports:admin",
            "projects:read",
            "projects:write",
            "users:read",
            "users:write",
            "audit:read",
        }
    ),
}

_PLATFORM_ADMIN_EXTRA_PERMISSIONS: frozenset[str] = frozenset(
    {
        "organizations:read",
        "organizations:write",
        "impersonation:use",
        "tenant_manager:admin",
    }
)

_CONTRACTOR_VISIBLE_STATUSES: frozenset[QualityIssueStatus] = frozenset(
    {
        QualityIssueStatus.OPEN,
        QualityIssueStatus.IN_REMEDIATION,
    }
)

_CONTRACTOR_ALLOWED_TRANSITIONS: frozenset[
    tuple[QualityIssueStatus, QualityIssueStatus]
] = frozenset(
    {
        (
            QualityIssueStatus.IN_REMEDIATION,
            QualityIssueStatus.PENDING_VERIFICATION,
        ),
    }
)

_QC_INVITEABLE_ROLES_BY_PERSONA: dict[QCPersona, tuple[str, ...]] = {
    QCPersona.ADMIN: (
        "SUPERVISOR",
        "DEVELOPER",
        "CONTRACTOR",
        "VIEWER",
    ),
}

_PLATFORM_ADMIN_INVITEABLE_ROLES: tuple[str, ...] = (
    "ADMIN",
    "SUPERVISOR",
    "DEVELOPER",
    "CONTRACTOR",
    "VIEWER",
)


def normalize_system_role(role: str | None) -> str:
    return (role or "").strip().upper()


def resolve_qc_persona(role: str | None) -> QCPersona | None:
    return _SYSTEM_ROLE_TO_QC_PERSONA.get(normalize_system_role(role))


def resolve_qc_permissions(role: str | None) -> set[str]:
    normalized = normalize_system_role(role)
    persona = resolve_qc_persona(role)
    if persona is None:
        return set()

    permissions = set(_QC_PERMISSION_MATRIX[persona])
    if normalized == "PLATFORM_ADMIN":
        permissions |= _PLATFORM_ADMIN_EXTRA_PERMISSIONS
    return permissions


def has_qc_permission(role: str | None, permission: str) -> bool:
    return permission in resolve_qc_permissions(role)


def visible_issue_statuses_for_role(
    role: str | None,
) -> frozenset[QualityIssueStatus] | None:
    persona = resolve_qc_persona(role)
    if persona == QCPersona.CONTRACTOR:
        return _CONTRACTOR_VISIBLE_STATUSES
    if persona in {QCPersona.SUPERVISOR, QCPersona.ADMIN, QCPersona.DEVELOPER}:
        return None
    return frozenset()


def can_perform_issue_transition(
    role: str | None,
    from_status: QualityIssueStatus,
    to_status: QualityIssueStatus,
) -> bool:
    if from_status == to_status:
        return True

    if not is_valid_status_transition(from_status, to_status):
        return False

    persona = resolve_qc_persona(role)
    if persona is None:
        return False

    if persona == QCPersona.DEVELOPER:
        return False

    if persona == QCPersona.CONTRACTOR:
        return (from_status, to_status) in _CONTRACTOR_ALLOWED_TRANSITIONS

    if persona in {QCPersona.SUPERVISOR, QCPersona.ADMIN}:
        return True

    return False


def qc_inviteable_roles(actor_role: str | None) -> tuple[str, ...]:
    normalized = normalize_system_role(actor_role)
    if normalized == "PLATFORM_ADMIN":
        return _PLATFORM_ADMIN_INVITEABLE_ROLES
    if normalized == "ADMIN":
        return _QC_INVITEABLE_ROLES_BY_PERSONA[QCPersona.ADMIN]
    return ()


def can_assign_qc_role(
    *,
    actor_role: str | None,
    target_role: str | None,
) -> bool:
    return normalize_system_role(target_role) in set(
        qc_inviteable_roles(actor_role)
    )
