"""Authentication routes.

Extracted from app/main.py during the 2026-07 architecture-modularization
refactor. Shared service singletons live in app/dependencies.py; shared
request models live in app/schemas/api_requests.py.
"""
from __future__ import annotations

from app.auth import (
    PERMISSION_MATRIX,
    get_auth_context,
    require_permission,
)
from app.auth.password_policy import get_password_policy
from app.auth.supabase_session_metadata import sync_active_organization_metadata
from fastapi import (
    Depends,
    HTTPException,
    Request,
)
from postgrest.exceptions import APIError

from fastapi import APIRouter
import app.dependencies as deps
from app.schemas.api_requests import (
    ExchangeTokenRequest,
)


router = APIRouter()


@router.get("/auth/me")
def get_current_session(auth=Depends(get_auth_context)):
    return {
        "user_id": auth.user_id,
        "org_id": auth.org_id,
        "role": auth.role,
        "effective_user_id": auth.effective_user_id,
        "permissions": sorted(auth.permissions),
    }


@router.get("/auth/permission-matrix")
def get_permission_matrix():
    return {role: sorted(perms) for role, perms in PERMISSION_MATRIX.items()}


@router.get("/auth/tenant/check")
def tenant_check(auth=Depends(get_auth_context)):
    return {"status": "ok", "org_id": auth.org_id}


@router.get("/auth/secure/reports")
def secure_reports(_: object = Depends(require_permission("reports:read"))):
    return {"status": "ok"}


@router.get("/auth/secure/admin")
def secure_admin(_: object = Depends(require_permission("users:write"))):
    return {"status": "ok"}


@router.get("/auth/impersonation/status")
def impersonation_status(auth=Depends(get_auth_context)):
    return {
        "is_impersonating": bool(auth.effective_user_id),
        "actor_user_id": auth.user_id,
        "effective_user_id": auth.actor_user_id,
    }


@router.post("/auth/refresh")
def refresh_access_token(request: Request):
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer refresh token")

    refresh_token = auth_header.replace("Bearer ", "", 1).strip()
    payload = deps.jwt_service.decode_refresh_token(refresh_token)
    access_token = deps.jwt_service.issue_access_token(
        user_id=payload["sub"],
        org_id=payload["org_id"],
        role=payload["role"],
        token_id=str(payload.get("jti", "refresh-rotation")),
    )
    deps.logger.info(
        "Refresh token exchanged",
        extra={
            "event": "audit.refresh",
            "user_id": payload["sub"],
            "org_id": payload["org_id"],
        },
    )
    return {"access_token": access_token, "token_type": "Bearer"}


@router.post("/auth/exchange")
def exchange_supabase_session(request: ExchangeTokenRequest):
    user_id = request.user_id.strip()
    if not user_id:
        raise HTTPException(
            status_code=422,
            detail="user_id is required",
        )

    try:
        profile = deps.profile_service.get_profile(user_id)
    except APIError as error:
        deps.logger.exception(
            "Database error loading profile during token exchange",
            extra={"user_id": user_id},
        )
        raise HTTPException(
            status_code=503,
            detail="Unable to load profile from database",
        ) from error

    if not profile:
        deps.logger.warning(
            "Token exchange rejected - profile missing for Supabase user",
            extra={"event": "auth.exchange.profile_not_found", "user_id": user_id},
        )
        raise HTTPException(
            status_code=404,
            detail=(
                "Profile not found. Ask an administrator to invite you "
                "before signing in."
            ),
        )

    try:
        org_id = deps.profile_service.ensure_organization_id(
            user_id,
            preferred_organization_id=request.organization_id,
        )
    except APIError as error:
        deps.logger.exception(
            "Database error resolving organization during token exchange",
            extra={"user_id": user_id},
        )
        raise HTTPException(
            status_code=503,
            detail="Unable to resolve organization for user",
        ) from error

    role = str(profile.get("role") or "VIEWER").strip().upper()
    if not org_id:
        raise HTTPException(
            status_code=422,
            detail=(
                "Profile missing organization_id. "
                "Run tenant migration in Supabase."
            ),
        )

    sync_active_organization_metadata(
        user_id=user_id,
        organization_id=org_id,
        role=role,
    )

    deps.resident_activation_service.activate_on_login(
        profile_id=user_id,
        role=role,
    )

    access_token = deps.jwt_service.issue_access_token(
        user_id=request.user_id,
        org_id=org_id,
        role=role,
        token_id=f"exchange-{request.user_id}",
    )
    deps.logger.info(
        "Supabase session exchanged for API token",
        extra={
            "event": "audit.login",
            "user_id": request.user_id,
            "org_id": org_id,
            "role": role,
        },
    )
    return {
        "access_token": access_token,
        "token_type": "Bearer",
        "org_id": org_id,
        "role": role,
    }


@router.get("/auth/organizations")
def list_accessible_organizations(
    auth=Depends(get_auth_context),
):
    return deps.organization_admin_service.list_accessible_organizations(
        auth.user_id
    )


@router.get("/auth/password-policy")
def get_password_policy_config():
    return get_password_policy()


