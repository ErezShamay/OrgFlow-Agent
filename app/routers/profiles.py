"""Profile routes.

Extracted from app/main.py during the 2026-07 architecture-modularization
refactor. Shared service singletons live in app/dependencies.py; shared
request models live in app/schemas/api_requests.py.
"""
from __future__ import annotations

from fastapi import (
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
)

from fastapi import APIRouter
import app.dependencies as deps
import app.services.connection_managers as conn_mgrs
from app.schemas.api_requests import (
    NotificationCreateRequest,
    NotificationEscalationRequest,
    NotificationPreferenceRequest,
    NotificationReadSyncRequest,
)


router = APIRouter()


@router.get("/profiles/{profile_id}")
def get_profile(profile_id: str):

    profile = (
        deps.profile_service
        .get_profile(profile_id)
    )

    if not profile:

        raise HTTPException(
            status_code=404,
            detail="Profile not found"
        )

    return profile


@router.get("/profiles/{profile_id}/notifications")
def get_profile_notifications(profile_id: str, unread_only: bool = False):
    return deps.notification_service.get_notifications(profile_id, unread_only=unread_only)


@router.post("/profiles/{profile_id}/notifications")
async def create_profile_notification(profile_id: str, request: NotificationCreateRequest):
    payload = deps.notification_service.create_notification(
        profile_id=profile_id,
        title=request.title,
        message=request.message,
        notification_type=request.notification_type,
        channel=request.channel,
        channels=request.channels,
        category=request.category,
        priority=request.priority,
        banner=request.banner,
        max_attempts=request.max_attempts,
        force_fail_channels=request.force_fail_channels,
    )
    await conn_mgrs.notification_connection_manager.broadcast_notification(profile_id, payload)
    return payload


@router.websocket("/profiles/{profile_id}/notifications/stream")
async def stream_profile_notifications(profile_id: str, websocket: WebSocket):
    await conn_mgrs.notification_connection_manager.connect(profile_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        conn_mgrs.notification_connection_manager.disconnect(profile_id, websocket)


@router.get("/profiles/{profile_id}/notifications/unread")
def get_profile_unread_notifications(profile_id: str):
    items = deps.notification_service.get_unread_notifications(profile_id)
    return {"profile_id": profile_id, "total": len(items), "items": items}


@router.get("/profiles/{profile_id}/notifications/digest")
def get_profile_notification_digest(profile_id: str):
    return deps.notification_service.get_digest(profile_id)


@router.put("/profiles/{profile_id}/notifications/preferences")
def set_profile_notification_preferences(profile_id: str, request: NotificationPreferenceRequest):
    return deps.notification_service.set_preferences(
        profile_id=profile_id,
        channels=request.channels,
        categories=request.categories,
    )


@router.get("/profiles/{profile_id}/notifications/preferences")
def get_profile_notification_preferences(profile_id: str):
    return deps.notification_service.get_preferences(profile_id)


@router.get("/profiles/{profile_id}/notifications/categories")
def get_profile_notification_categories(profile_id: str):
    return deps.notification_service.list_categories(profile_id)


@router.get("/profiles/{profile_id}/notification-center")
def get_notification_center(profile_id: str):
    return deps.notification_service.get_notifications(profile_id, include_center=True)


@router.post("/profiles/{profile_id}/notifications/retry")
def retry_profile_notifications(profile_id: str):
    return deps.notification_service.retry_pending_notifications(profile_id)


@router.patch("/profiles/{profile_id}/notifications/read-sync")
def sync_profile_notification_read_state(profile_id: str, request: NotificationReadSyncRequest):
    return deps.notification_service.sync_read_state(profile_id, request.read_ids)


@router.post("/profiles/{profile_id}/notifications/escalation")
async def create_escalation_notification(profile_id: str, request: NotificationEscalationRequest):
    payload = deps.notification_service.create_escalation_notification(
        profile_id=profile_id,
        title=request.title,
        message=request.message,
        escalation_level=request.escalation_level,
    )
    await conn_mgrs.notification_connection_manager.broadcast_notification(profile_id, payload)
    return payload


@router.get("/profiles/{profile_id}/notifications/delivery-log")
def get_profile_notification_delivery_log(profile_id: str):
    return deps.notification_service.get_delivery_log(profile_id)


