from __future__ import annotations

from datetime import UTC, datetime
from typing import Any


class MigrationRepository:
    """Tracks applied database migrations."""

    def __init__(self) -> None:
        self._applied: dict[str, dict[str, Any]] = {}

    def list_applied(self) -> list[dict[str, Any]]:
        return sorted(
            self._applied.values(),
            key=lambda item: item["version"],
        )

    def is_applied(self, version: str) -> bool:
        return version in self._applied

    def record_applied(
        self,
        *,
        version: str,
        name: str,
        description: str,
    ) -> dict[str, Any]:
        record = {
            "version": version,
            "name": name,
            "description": description,
            "applied_at": datetime.now(UTC).isoformat(),
        }
        self._applied[version] = record
        return record
