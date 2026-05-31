from __future__ import annotations

from datetime import UTC, datetime

from app.db.schema_registry import TABLES


class SoftDeleteService:
    def apply_soft_delete(
        self,
        *,
        table_name: str,
        record: dict,
        actor_id: str | None = None,
    ) -> dict:
        schema = TABLES.get(table_name)
        if not schema:
            raise ValueError(f"Unknown table: {table_name}")
        if not schema.soft_delete_column:
            raise ValueError(f"Table {table_name} does not support soft delete")

        column = schema.soft_delete_column
        if record.get(column):
            return {
                "table": table_name,
                "already_deleted": True,
                "record": record,
            }

        updated = dict(record)
        updated[column] = datetime.now(UTC).isoformat()
        if actor_id:
            updated["deleted_by"] = actor_id
        return {
            "table": table_name,
            "already_deleted": False,
            "record": updated,
            "deleted_at_column": column,
        }

    def restore(self, *, table_name: str, record: dict) -> dict:
        schema = TABLES.get(table_name)
        if not schema or not schema.soft_delete_column:
            raise ValueError(f"Table {table_name} does not support soft delete")

        column = schema.soft_delete_column
        updated = dict(record)
        updated[column] = None
        updated.pop("deleted_by", None)
        return {
            "table": table_name,
            "restored": True,
            "record": updated,
        }

    def filter_active(self, records: list[dict], table_name: str) -> dict:
        schema = TABLES.get(table_name)
        if not schema or not schema.soft_delete_column:
            return {
                "table": table_name,
                "active": records,
                "deleted": [],
            }

        column = schema.soft_delete_column
        active = [item for item in records if not item.get(column)]
        deleted = [item for item in records if item.get(column)]
        return {
            "table": table_name,
            "active": active,
            "deleted": deleted,
            "active_count": len(active),
            "deleted_count": len(deleted),
        }

    def get_supported_tables(self) -> dict:
        tables = [
            name
            for name, schema in TABLES.items()
            if schema.soft_delete_column
        ]
        return {"tables": tables, "count": len(tables)}
