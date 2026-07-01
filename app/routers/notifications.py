"""Notifications & workspace activity routes (incl. WebSocket).

Extracted from app/main.py during the 2026-07 architecture-modularization
refactor. Shared service singletons live in app/dependencies.py; shared
request models live in app/schemas/api_requests.py.
"""
from __future__ import annotations

from app.auth import require_permission
from fastapi import Depends

from fastapi import APIRouter
import app.dependencies as deps
from app.schemas.api_requests import (
    CrossProjectWorkspaceRequest,
)


router = APIRouter()


@router.post("/workspace/cross-project")
def get_cross_project_workspace(request: CrossProjectWorkspaceRequest, _: object = Depends(require_permission("projects:read"))):
    valid_projects: list[str] = []
    for project_id in request.project_ids:
        project = deps.project_repository.get_project_by_id(project_id)
        if project:
            valid_projects.append(project_id)
    return deps.workspace_activity_service.list_cross_project_activities(valid_projects, limit=request.limit)


@router.patch("/notifications/{notification_id}/read")
def mark_notification_as_read(notification_id: str):

    return (
        deps.notification_service
        .mark_as_read(notification_id)
    )


