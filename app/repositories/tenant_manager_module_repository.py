from __future__ import annotations

from datetime import UTC, datetime

from postgrest.exceptions import APIError

from app.db.supabase_client import supabase
from app.repositories.postgrest_errors import (
    is_missing_table_error,
)


class TenantManagerModuleRepository:
    TABLE = "organization_tenant_manager_modules"

    def __init__(self) -> None:
        self.client = supabase
        self._table_available: bool | None = None

    def is_storage_available(self) -> bool:
        if self._table_available is not None:
            return self._table_available

        try:
            (
                self.client
                .table(self.TABLE)
                .select("organization_id")
                .limit(1)
                .execute()
            )
            self._table_available = True
        except APIError as error:
            if is_missing_table_error(error, self.TABLE):
                self._table_available = False
            else:
                raise

        return self._table_available

    def get_by_organization_id(
        self,
        organization_id: str,
    ) -> dict | None:
        if not self.is_storage_available():
            return None

        response = (
            self.client
            .table(self.TABLE)
            .select("*")
            .eq("organization_id", organization_id)
            .limit(1)
            .execute()
        )

        if not response.data:
            return None

        return response.data[0]

    def list_all(self) -> list[dict]:
        if not self.is_storage_available():
            return []

        response = (
            self.client
            .table(self.TABLE)
            .select("*")
            .execute()
        )
        return response.data or []

    def upsert_status(
        self,
        *,
        organization_id: str,
        is_enabled: bool,
        enabled_by_profile_id: str | None,
    ) -> dict:
        if not self.is_storage_available():
            raise RuntimeError(
                f"Table {self.TABLE} is not available. "
                "Apply db/migrations/2026061101_organization_tenant_manager_module.sql"
            )

        now = datetime.now(UTC).isoformat()
        existing = self.get_by_organization_id(organization_id)

        payload = {
            "organization_id": organization_id,
            "is_enabled": is_enabled,
            "updated_at": now,
        }

        if is_enabled:
            payload["enabled_at"] = now
            payload["disabled_at"] = None
            payload["enabled_by_profile_id"] = enabled_by_profile_id
        else:
            payload["disabled_at"] = now
            if existing:
                payload["enabled_at"] = existing.get("enabled_at")

        response = (
            self.client
            .table(self.TABLE)
            .upsert(payload)
            .execute()
        )

        return response.data[0]
