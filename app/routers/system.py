"""System / health / feature-flags / config / agent routes.

Extracted from app/main.py during the 2026-07 architecture-modularization
refactor. Shared service singletons live in app/dependencies.py; shared
request models live in app/schemas/api_requests.py.
"""
from __future__ import annotations

from app.automation.scheduler import scheduler
from app.config import config_manager
from app.config.settings import settings
from datetime import (
    UTC,
    datetime,
)
from fastapi.responses import JSONResponse

from fastapi import APIRouter, Request
import app.dependencies as deps
from app.schemas.api_requests import (
    AgentRequest,
)


router = APIRouter()


@router.get("/")
def root():

    return {
        "message":
            "OrgFlow AI Agent is running"
    }


@router.get("/healthcheck")
@router.get("/health")
def healthcheck():

    return {
        "status": "ok",
        "service": "orgflow-agent",
        "environment": settings.ENVIRONMENT,
    }


@router.get("/readiness")
def readiness(request: Request):
    checks = {
        "startup_complete": bool(request.app.state.startup_complete),
        "scheduler_running": bool(scheduler.running) if deps.IS_AUTOMATION_ENABLED else True,
        "automation_enabled": deps.IS_AUTOMATION_ENABLED,
        "supabase_configured": bool(
            settings.SUPABASE_URL and settings.SUPABASE_KEY
        ),
    }

    is_ready = checks["startup_complete"] and checks["scheduler_running"]
    payload = {
        "status": "ready" if is_ready else "not_ready",
        "service": "orgflow-agent",
        "checks": checks,
    }

    if not is_ready:
        return JSONResponse(status_code=503, content=payload)

    return payload


@router.get("/liveness")
def liveness():
    return {
        "status": "alive",
        "service": "orgflow-agent",
        "environment": settings.ENVIRONMENT,
        "timestamp": (
            datetime
            .now(UTC)
            .isoformat()
        ),
    }


@router.get("/feature-flags")
def get_feature_flags():
    current_settings = config_manager.get_settings()
    return {
        "environment": current_settings.ENVIRONMENT,
        "flags": current_settings.FEATURE_FLAGS.model_dump(),
    }


@router.get("/config")
def get_runtime_config():
    return {
        "environment": config_manager.get_settings().ENVIRONMENT,
        "config": config_manager.get_safe_snapshot(),
    }


@router.post("/config/reload")
def reload_runtime_config():
    updated = config_manager.force_reload()
    return {
        "status": "reloaded",
        "environment": updated.ENVIRONMENT,
    }


@router.post("/agent/run")
def run_agent(
    request: AgentRequest
):
    from app.schemas.qc_freeze import raise_if_frozen_api_path

    raise_if_frozen_api_path("/agent/run")

    return deps.orchestrator.run(
        request.user_request
    )


@router.post(
    "/approval/{approval_id}/approve"
)
def approve_request(
    approval_id: int
):

    return deps.approval_service.approve(
        approval_id
    )


@router.get(
    "/approval/{approval_id}"
)
def get_approval_request(
    approval_id: int
):

    return deps.approval_service.get_request(
        approval_id
    )


