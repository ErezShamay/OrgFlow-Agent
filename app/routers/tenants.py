"""Tenant manager routes.

Extracted from app/main.py during the 2026-07 architecture-modularization
refactor. Shared service singletons live in app/dependencies.py; shared
request models live in app/schemas/api_requests.py.
"""
from __future__ import annotations

from app.auth import get_auth_context
from fastapi import Depends

from fastapi import APIRouter
import app.dependencies as deps
from app.schemas.api_requests import (
    TenantExtractRequest,
    TenantExtractResponse,
)


router = APIRouter()


@router.get("/tenant-manager/module-status")
def get_tenant_manager_module_status(
    auth=Depends(get_auth_context),
):
    return deps.tenant_manager_module_service.get_status(
        auth.org_id
    )


@router.post("/tenants/extract", response_model=TenantExtractResponse)
def extract_tenants(
    request: TenantExtractRequest,
    _: object = Depends(get_auth_context),
):
    result = deps.tenant_extraction_service.extract_from_text(request.text)
    return TenantExtractResponse(
        tenants=result.get("tenants", []),
        error=result.get("error"),
    )


