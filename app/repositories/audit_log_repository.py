from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4


class AuditLogRepository:
    """In-memory audit log store for database change tracking."""

    def __init__(self) -> None:
        self._entries: list[dict[str, Any]] = []

    def append(
        self,
        *,
        table_name: str,
        record_id: str,
        action: str,
        organization_id: str | None,
        actor_id: str | None,
        before: dict | None = None,
        after: dict | None = None,
    ) -> dict[str, Any]:
        entry = {
            "id": str(uuid4()),
            "table_name": table_name,
            "record_id": record_id,
            "action": action,
            "organization_id": organization_id,
            "actor_id": actor_id,
            "before": before,
            "after": after,
            "created_at": datetime.now(UTC).isoformat(),
        }
        self._entries.append(entry)
        return entry

    def list_entries(
        self,
        *,
        table_name: str | None = None,
        organization_id: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        results = self._entries
        if table_name:
            results = [
                item for item in results if item["table_name"] == table_name
            ]
        if organization_id:
            results = [
                item
                for item in results
                if item.get("organization_id") == organization_id
            ]
        return list(reversed(results[-limit:]))
