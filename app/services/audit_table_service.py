from __future__ import annotations

from app.db.schema_registry import TABLES
from app.repositories.audit_log_repository import AuditLogRepository


class AuditTableService:
    def __init__(
        self,
        audit_repository: AuditLogRepository | None = None,
    ):
        self.audit_repository = audit_repository or AuditLogRepository()

    def get_audited_tables(self) -> dict:
        audited = [
            name for name, schema in TABLES.items() if schema.audited
        ]
        return {
            "audited_tables": audited,
            "count": len(audited),
        }

    def record_change(
        self,
        *,
        table_name: str,
        record_id: str,
        action: str,
        organization_id: str | None = None,
        actor_id: str | None = None,
        before: dict | None = None,
        after: dict | None = None,
    ) -> dict:
        schema = TABLES.get(table_name)
        if schema and not schema.audited:
            return {
                "recorded": False,
                "reason": "TABLE_NOT_AUDITED",
                "table": table_name,
            }
        entry = self.audit_repository.append(
            table_name=table_name,
            record_id=record_id,
            action=action,
            organization_id=organization_id,
            actor_id=actor_id,
            before=before,
            after=after,
        )
        return {"recorded": True, "entry": entry}

    def get_audit_log(
        self,
        *,
        table_name: str | None = None,
        organization_id: str | None = None,
        limit: int = 100,
    ) -> dict:
        entries = self.audit_repository.list_entries(
            table_name=table_name,
            organization_id=organization_id,
            limit=limit,
        )
        return {
            "entries": entries,
            "count": len(entries),
        }
