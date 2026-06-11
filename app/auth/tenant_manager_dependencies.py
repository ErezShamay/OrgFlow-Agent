from __future__ import annotations

from fastapi import Depends, Request

from app.auth.dependencies import get_auth_context
from app.auth.models import AuthContext
from app.services.tenant_manager_module_service import (
    TenantManagerModuleService,
)


def require_tenant_manager_module(
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
) -> AuthContext:
    service = getattr(
        request.app.state,
        "tenant_manager_module_service",
        None,
    ) or TenantManagerModuleService()

    service.require_enabled(auth.org_id)
    return auth


def get_tenant_manager_module_service(
    request: Request,
) -> TenantManagerModuleService:
    return getattr(
        request.app.state,
        "tenant_manager_module_service",
        None,
    ) or TenantManagerModuleService()
