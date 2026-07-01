"""Shared WebSocket connection-manager singletons.

Moved out of app/main.py so both the FastAPI entrypoint and the
app/routers/*.py modules with websocket endpoints can import them
without a circular import.
"""
from __future__ import annotations

from fastapi import WebSocket


class WorkspaceConnectionManager:
    def __init__(self):
        self._project_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, project_id: str, websocket: WebSocket):
        await websocket.accept()
        self._project_connections.setdefault(project_id, []).append(websocket)

    def disconnect(self, project_id: str, websocket: WebSocket):
        sockets = self._project_connections.get(project_id, [])
        self._project_connections[project_id] = [
            candidate for candidate in sockets if candidate is not websocket
        ]

    async def broadcast_activity(self, project_id: str, activity: dict):
        sockets = list(self._project_connections.get(project_id, []))
        disconnected: list[WebSocket] = []
        for websocket in sockets:
            try:
                await websocket.send_json(
                    {
                        "event": "workspace.activity.created",
                        "project_id": project_id,
                        "activity": activity,
                    }
                )
            except RuntimeError:
                disconnected.append(websocket)
        for websocket in disconnected:
            self.disconnect(project_id, websocket)


class NotificationConnectionManager:
    def __init__(self):
        self._profile_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, profile_id: str, websocket: WebSocket):
        await websocket.accept()
        self._profile_connections.setdefault(profile_id, []).append(websocket)

    def disconnect(self, profile_id: str, websocket: WebSocket):
        sockets = self._profile_connections.get(profile_id, [])
        self._profile_connections[profile_id] = [
            candidate for candidate in sockets if candidate is not websocket
        ]

    async def broadcast_notification(self, profile_id: str, notification: dict):
        sockets = list(self._profile_connections.get(profile_id, []))
        disconnected: list[WebSocket] = []
        for websocket in sockets:
            try:
                await websocket.send_json(
                    {
                        "event": "notification.created",
                        "profile_id": profile_id,
                        "notification": notification,
                    }
                )
            except RuntimeError:
                disconnected.append(websocket)
        for websocket in disconnected:
            self.disconnect(profile_id, websocket)


workspace_connection_manager = (
    WorkspaceConnectionManager()
)

notification_connection_manager = (
    NotificationConnectionManager()
)


def get_workspace_connection_manager():
    return workspace_connection_manager


def get_notification_connection_manager():
    return notification_connection_manager


