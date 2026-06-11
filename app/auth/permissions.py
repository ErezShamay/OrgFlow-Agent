from __future__ import annotations

from app.schemas.qc_permissions import resolve_qc_permissions

QC_PERMISSIONS: tuple[str, ...] = (
    "quality_issues:read",
    "quality_issues:write",
    "quality_issues:remediate",
    "quality_issues:verify",
    "quality_portfolio:read",
)

_QC_SUPERVISOR = {
    "quality_issues:read",
    "quality_issues:write",
    "quality_issues:verify",
    "quality_portfolio:read",
}

_QC_ADMIN = _QC_SUPERVISOR

_QC_CONTRACTOR = {
    "quality_issues:read",
    "quality_issues:remediate",
}

_QC_DEVELOPER = {
    "quality_issues:read",
    "quality_portfolio:read",
}

PERMISSION_MATRIX: dict[str, set[str]] = {
    "PLATFORM_ADMIN": {
        "projects:read",
        "projects:write",
        "reports:read",
        "reports:write",
        "users:read",
        "users:write",
        "organizations:read",
        "organizations:write",
        "field_reports:admin",
        "field_reports:read",
        "field_reports:write",
        "audit:read",
        "impersonation:use",
        *_QC_ADMIN,
    },
    "ADMIN": {
        "projects:read",
        "projects:write",
        "reports:read",
        "reports:write",
        "field_reports:read",
        "field_reports:write",
        "users:read",
        "users:write",
        "audit:read",
        *_QC_ADMIN,
    },
    "SUPERVISOR": {
        "projects:read",
        "projects:write",
        "reports:read",
        "reports:write",
        "field_reports:read",
        "field_reports:write",
        "audit:read",
        *_QC_SUPERVISOR,
    },
    "MANAGER": {
        "projects:read",
        "projects:write",
        "reports:read",
        "reports:write",
        "field_reports:read",
        "field_reports:write",
        "users:read",
        "audit:read",
        *_QC_SUPERVISOR,
    },
    "CONTRACTOR": {
        "projects:read",
        *_QC_CONTRACTOR,
    },
    "DEVELOPER": {
        "projects:read",
        "reports:read",
        "field_reports:read",
        *_QC_DEVELOPER,
    },
    "ANALYST": {
        "projects:read",
        "reports:read",
        *_QC_DEVELOPER,
    },
    "VIEWER": {
        "projects:read",
        "reports:read",
        *_QC_DEVELOPER,
    },
}


def resolve_permissions(role: str) -> set[str]:
    normalized = role.upper()
    base = set(PERMISSION_MATRIX.get(normalized, set()))
    return base | resolve_qc_permissions(role)
