"""Operational actions routes.

Extracted from app/main.py during the 2026-07 architecture-modularization
refactor. Shared service singletons live in app/dependencies.py; shared
request models live in app/schemas/api_requests.py.
"""
from __future__ import annotations

from app.auth import require_permission
from fastapi import (
    Depends,
    HTTPException,
)

from fastapi import APIRouter
import app.dependencies as deps
from app.schemas.api_requests import (
    ActionAssignRequest,
    ActionCommentRequest,
)


router = APIRouter()


@router.get("/actions/open")
def get_open_actions(
    auth=Depends(require_permission("projects:read")),
):
    return deps.operational_action_service.get_open_actions(
        organization_id=auth.org_id,
    )


@router.get("/actions/escalations")
def get_action_escalations(
    auth=Depends(require_permission("projects:read")),
):
    return deps.operational_action_service.get_escalations(
        organization_id=auth.org_id,
    )


@router.get("/actions/{action_id}")
def get_action_details(action_id: str):
    payload = deps.operational_action_service.get_action_details(action_id)
    if not payload.get("success"):
        raise HTTPException(status_code=404, detail="Action not found")
    return payload


@router.get("/actions/{action_id}/comments")
def list_action_comments(action_id: str):
    action = deps.operational_action_repository.get_action_by_id(action_id)
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
    return {"comments": deps.operational_action_service.list_comments(action_id)}


@router.post("/actions/{action_id}/comments")
def create_action_comment(action_id: str, request: ActionCommentRequest):
    action = deps.operational_action_repository.get_action_by_id(action_id)
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
    return deps.operational_action_service.add_comment(
        action_id,
        request.comment,
        request.created_by,
    )


@router.post("/actions/{action_id}/close")
def close_action(action_id: str):
    action = deps.operational_action_repository.get_action_by_id(action_id)
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
    return deps.operational_action_service.close_action(action_id)


@router.post("/actions/{action_id}/start")
def start_action(action_id: str):
    action = deps.operational_action_repository.get_action_by_id(action_id)
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
    return deps.operational_action_service.start_action(action_id)


@router.post("/actions/{action_id}/block")
def block_action(action_id: str):
    action = deps.operational_action_repository.get_action_by_id(action_id)
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
    return deps.operational_action_service.block_action(action_id)


@router.post("/actions/{action_id}/complete")
def complete_action(action_id: str):
    action = deps.operational_action_repository.get_action_by_id(action_id)
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
    return deps.operational_action_service.complete_action(action_id)


@router.post("/actions/{action_id}/escalate")
def escalate_action(action_id: str):
    action = deps.operational_action_repository.get_action_by_id(action_id)
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
    return deps.operational_action_service.escalate_action(action_id)


@router.post("/actions/{action_id}/assign")
def assign_action(action_id: str, request: ActionAssignRequest):
    action = deps.operational_action_repository.get_action_by_id(action_id)
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
    return deps.operational_action_service.assign_action(
        action_id,
        request.assigned_to,
    )


