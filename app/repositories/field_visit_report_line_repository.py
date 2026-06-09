from __future__ import annotations

from datetime import UTC, datetime

from postgrest.exceptions import APIError

from app.db.supabase_client import supabase
from app.repositories.postgrest_errors import (
    is_missing_column_error,
    is_missing_table_error,
    raise_if_missing_column_migration,
)

LINE_SYNC_MIGRATIONS = {
    "client_line_uuid": (
        "deploy/sql/2026060304_field_visit_report_client_uuids.sql"
    ),
    "group_key": (
        "deploy/sql/2026060301_field_visit_report_line_grouping.sql"
    ),
    "group_label_he": (
        "deploy/sql/2026060301_field_visit_report_line_grouping.sql"
    ),
    "block_id": (
        "deploy/sql/2026060301_field_visit_report_line_grouping.sql"
    ),
}


class FieldVisitReportLineRepository:
    TABLE = "field_visit_report_lines"

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
                .select("id")
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

    def list_by_report(self, report_id: str) -> list[dict]:
        if not self.is_storage_available():
            return []

        response = (
            self.client
            .table(self.TABLE)
            .select("*")
            .eq("report_id", report_id)
            .order("sort_order")
            .order("created_at")
            .execute()
        )
        return response.data or []

    def get_by_id(self, line_id: str) -> dict | None:
        if not self.is_storage_available():
            return None

        response = (
            self.client
            .table(self.TABLE)
            .select("*")
            .eq("id", line_id)
            .limit(1)
            .execute()
        )

        if not response.data:
            return None

        return response.data[0]

    def get_by_client_line_uuid(
        self,
        client_line_uuid: str,
    ) -> dict | None:
        if not self.is_storage_available() or not client_line_uuid:
            return None

        try:
            response = (
                self.client
                .table(self.TABLE)
                .select("*")
                .eq("client_line_uuid", client_line_uuid)
                .limit(1)
                .execute()
            )
        except APIError as error:
            raise_if_missing_column_migration(
                error,
                column="client_line_uuid",
                migration_file=LINE_SYNC_MIGRATIONS["client_line_uuid"],
            )

        if not response.data:
            return None

        return response.data[0]

    def next_sort_order(self, report_id: str) -> int:
        lines = self.list_by_report(report_id)
        if not lines:
            return 0
        return max(int(line.get("sort_order") or 0) for line in lines) + 1

    def _raise_line_write_migration_error(
        self,
        error: APIError,
        payload: dict,
    ) -> None:
        for column, migration_file in LINE_SYNC_MIGRATIONS.items():
            if column in payload and is_missing_column_error(
                error,
                column,
            ):
                raise_if_missing_column_migration(
                    error,
                    column=column,
                    migration_file=migration_file,
                )

        raise error

    def create(self, payload: dict) -> dict:
        if not self.is_storage_available():
            raise RuntimeError(
                f"Table {self.TABLE} is not available. "
                "Apply db/migrations/2026060103_field_visit_report_lines.sql"
            )

        now = datetime.now(UTC).isoformat()
        payload.setdefault("created_at", now)
        payload.setdefault("updated_at", now)

        try:
            response = (
                self.client
                .table(self.TABLE)
                .insert(payload)
                .execute()
            )
        except APIError as error:
            self._raise_line_write_migration_error(error, payload)

        return response.data[0]

    def update(self, line_id: str, payload: dict) -> dict | None:
        if not self.is_storage_available():
            raise RuntimeError(
                f"Table {self.TABLE} is not available. "
                "Apply db/migrations/2026060103_field_visit_report_lines.sql"
            )

        payload["updated_at"] = datetime.now(UTC).isoformat()

        try:
            response = (
                self.client
                .table(self.TABLE)
                .update(payload)
                .eq("id", line_id)
                .execute()
            )
        except APIError as error:
            self._raise_line_write_migration_error(error, payload)

        if not response.data:
            return None

        return response.data[0]

    def delete(self, line_id: str) -> bool:
        if not self.is_storage_available():
            raise RuntimeError(
                f"Table {self.TABLE} is not available. "
                "Apply db/migrations/2026060103_field_visit_report_lines.sql"
            )

        response = (
            self.client
            .table(self.TABLE)
            .delete()
            .eq("id", line_id)
            .execute()
        )
        return bool(response.data)
