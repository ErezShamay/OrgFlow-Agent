"""Admin / organization management routes.

Extracted from app/main.py during the 2026-07 architecture-modularization
refactor. Shared service singletons live in app/dependencies.py; shared
request models live in app/schemas/api_requests.py.
"""
from __future__ import annotations

from app.auth import require_permission
from app.schemas.field_reports import (
    FieldReportModuleToggleRequest,
    FieldReportOrganizationProfileUpdateRequest,
)
from app.schemas.organization import OrganizationCreateRequest
from app.schemas.tenant_manager import TenantManagerModuleToggleRequest
from app.schemas.user_management import (
    ALL_ORGANIZATIONS_SCOPE,
    UserInviteRequest,
    UserSetPasswordRequest,
    UserUpdateRequest,
)
from fastapi import Depends
from fastapi.responses import Response
from urllib.parse import quote

from fastapi import APIRouter
import app.dependencies as deps


router = APIRouter()


def _admin_target_organization_id(
    auth,
    requested_organization_id: str | None = None,
) -> str:
    return (
        deps.organization_admin_service.tenant_access_service
        .resolve_admin_target_organization(
            profile_id=auth.user_id,
            role=auth.role,
            session_org_id=auth.org_id,
            requested_organization_id=requested_organization_id,
        )
    )


@router.get("/admin/organizations")
def list_admin_organizations(
    auth=Depends(require_permission("users:read")),
):
    return deps.organization_admin_service.list_accessible_organizations(
        auth.user_id
    )


@router.post("/admin/organizations")
def create_admin_organization(
    request: OrganizationCreateRequest,
    auth=Depends(require_permission("organizations:write")),
):
    return deps.organization_admin_service.create_customer_organization(
        organization_name=request.organization_name,
        contact_email=request.contact_email,
        owner_profile_id=auth.user_id,
    )


@router.delete("/admin/organizations/{organization_id}")
def delete_admin_organization(
    organization_id: str,
    auth=Depends(require_permission("organizations:write")),
):
    return deps.organization_admin_service.delete_customer_organization(
        organization_id=organization_id,
        actor_user_id=auth.user_id,
        actor_role=auth.role,
    )


@router.get("/admin/field-reports/modules")
def list_field_report_modules(
    _: object = Depends(
        require_permission("field_reports:admin")
    ),
):
    return deps.field_report_module_service.list_all_with_organizations()


@router.patch(
    "/admin/field-reports/modules/{organization_id}"
)
def set_field_report_module(
    organization_id: str,
    request: FieldReportModuleToggleRequest,
    auth=Depends(require_permission("field_reports:admin")),
):
    return deps.field_report_module_service.set_enabled(
        organization_id=organization_id,
        is_enabled=request.is_enabled,
        actor_profile_id=auth.user_id,
    )


@router.get("/admin/ai-usage")
def get_platform_ai_usage_dashboard(
    period_days: int = 90,
    _: object = Depends(require_permission("organizations:read")),
):
    return deps.ai_usage_dashboard_service.get_platform_dashboard(
        period_days=period_days,
    )


@router.get("/admin/tenant-manager/modules")
def list_tenant_manager_modules(
    _: object = Depends(
        require_permission("tenant_manager:admin")
    ),
):
    return deps.tenant_manager_module_service.list_all_with_organizations()


@router.patch(
    "/admin/tenant-manager/modules/{organization_id}"
)
def set_tenant_manager_module(
    organization_id: str,
    request: TenantManagerModuleToggleRequest,
    auth=Depends(require_permission("tenant_manager:admin")),
):
    return deps.tenant_manager_module_service.set_enabled(
        organization_id=organization_id,
        is_enabled=request.is_enabled,
        actor_profile_id=auth.user_id,
    )


@router.patch(
    "/admin/field-reports/organizations/{organization_id}/profile"
)
def update_field_report_organization_profile(
    organization_id: str,
    request: FieldReportOrganizationProfileUpdateRequest,
    _: object = Depends(
        require_permission("field_reports:admin")
    ),
):
    return deps.field_report_organization_profile_service.update_profile(
        organization_id,
        report_phone=request.report_phone,
        report_address_line=request.report_address_line,
        report_city=request.report_city,
        report_tagline=request.report_tagline,
        logo_storage_path=request.logo_storage_path,
    )


@router.get(
    "/admin/field-reports/organizations/{organization_id}/profile"
)
def get_admin_field_report_organization_profile(
    organization_id: str,
    _: object = Depends(
        require_permission("field_reports:admin")
    ),
):
    return deps.field_report_organization_profile_service.get_profile(
        organization_id,
        require_module=False,
    )


@router.get(
    "/admin/field-reports/organizations/{organization_id}/export"
)
def export_admin_field_report_pdfs(
    organization_id: str,
    _: object = Depends(
        require_permission("field_reports:admin")
    ),
):
    content, filename = (
        deps.field_visit_report_export_service.export_organization_pdfs_zip(
            organization_id
        )
    )
    safe_filename = quote(filename)
    return Response(
        content=content,
        media_type="application/zip",
        headers={
            "Content-Disposition": (
                f'attachment; filename="{safe_filename}"; '
                f"filename*=UTF-8''{safe_filename}"
            ),
        },
    )


@router.get("/admin/tenant-migration/status")
def get_tenant_migration_status(
    _: object = Depends(require_permission("organizations:write")),
):
    return deps.tenant_migration_service.get_status()


@router.post("/admin/tenant-migration/backfill")
def run_tenant_migration_backfill(
    _: object = Depends(require_permission("organizations:write")),
):
    return deps.tenant_migration_service.backfill()


@router.get("/organizations")
def get_organizations():

    return (
        deps.organization_repository
        .get_all_organizations()
    )


@router.get("/admin/users")
def list_organization_users(
    organization_id: str | None = None,
    auth=Depends(require_permission("users:read")),
):
    if organization_id == ALL_ORGANIZATIONS_SCOPE:
        return deps.user_management_service.list_users(
            ALL_ORGANIZATIONS_SCOPE,
            actor_role=auth.role,
        )

    target_org_id = _admin_target_organization_id(
        auth,
        organization_id,
    )
    return deps.user_management_service.list_users(
        target_org_id,
        actor_role=auth.role,
    )


@router.post("/admin/users")
def invite_organization_user(
    request: UserInviteRequest,
    auth=Depends(require_permission("users:write")),
):
    target_org_id = _admin_target_organization_id(
        auth,
        request.organization_id,
    )
    return deps.user_management_service.invite_user(
        organization_id=target_org_id,
        email=str(request.email),
        full_name=request.full_name,
        role=request.role,
        invited_by=auth.user_id,
        inviter_role=auth.role,
    )


@router.delete("/admin/users/{profile_id}")
def delete_organization_user(
    profile_id: str,
    organization_id: str | None = None,
    auth=Depends(require_permission("users:write")),
):
    target_org_id = _admin_target_organization_id(
        auth,
        organization_id,
    )
    return deps.user_management_service.delete_user(
        organization_id=target_org_id,
        profile_id=profile_id,
        actor_user_id=auth.user_id,
        actor_role=auth.role,
    )


@router.post("/admin/users/{profile_id}/resend-invite")
def resend_organization_user_invite(
    profile_id: str,
    organization_id: str | None = None,
    auth=Depends(require_permission("users:write")),
):
    target_org_id = _admin_target_organization_id(
        auth,
        organization_id,
    )
    return deps.user_management_service.resend_invite(
        organization_id=target_org_id,
        profile_id=profile_id,
        actor_user_id=auth.user_id,
    )


@router.post("/admin/users/{profile_id}/password-reset")
def send_organization_user_password_reset(
    profile_id: str,
    organization_id: str | None = None,
    auth=Depends(require_permission("users:write")),
):
    target_org_id = _admin_target_organization_id(
        auth,
        organization_id,
    )
    return deps.user_management_service.send_password_reset(
        organization_id=target_org_id,
        profile_id=profile_id,
        actor_user_id=auth.user_id,
    )


@router.patch("/admin/users/{profile_id}")
def update_organization_user(
    profile_id: str,
    request: UserUpdateRequest,
    organization_id: str | None = None,
    auth=Depends(require_permission("users:write")),
):
    target_org_id = _admin_target_organization_id(
        auth,
        organization_id or request.organization_id,
    )
    return deps.user_management_service.update_user(
        organization_id=target_org_id,
        profile_id=profile_id,
        actor_user_id=auth.user_id,
        actor_role=auth.role,
        full_name=request.full_name,
        role=request.role,
    )


@router.post("/admin/users/{profile_id}/set-password")
def set_organization_user_password(
    profile_id: str,
    request: UserSetPasswordRequest,
    organization_id: str | None = None,
    auth=Depends(require_permission("users:write")),
):
    target_org_id = _admin_target_organization_id(
        auth,
        organization_id or request.organization_id,
    )
    return deps.user_management_service.set_password(
        organization_id=target_org_id,
        profile_id=profile_id,
        password=request.password,
        actor_user_id=auth.user_id,
    )


