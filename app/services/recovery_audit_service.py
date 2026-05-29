from datetime import datetime
from datetime import timezone
from uuid import uuid4


class RecoveryAuditService:
    def __init__(self):
        self._entries: list[dict] = []

    def record(
        self,
        action: str,
        execution_log_id: str,
        initiated_by: str,
        outcome: str,
        metadata: dict | None = None,
    ):
        entry = {
            "id": str(uuid4()),
            "action": action.upper(),
            "execution_log_id": execution_log_id,
            "initiated_by": initiated_by,
            "outcome": outcome.upper(),
            "metadata": metadata or {},
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self._entries.append(entry)
        return entry

    def list_entries(
        self,
        execution_log_id: str | None = None,
        action: str | None = None,
        limit: int = 100,
    ):
        entries = self._entries
        if execution_log_id:
            entries = [
                item
                for item in entries
                if item["execution_log_id"] == execution_log_id
            ]
        if action:
            entries = [
                item
                for item in entries
                if item["action"] == action.upper()
            ]
        return list(reversed(entries[-limit:]))
