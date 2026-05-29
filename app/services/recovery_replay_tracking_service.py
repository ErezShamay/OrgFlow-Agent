from datetime import datetime
from datetime import timezone
from uuid import uuid4


class RecoveryReplayTrackingService:
    def __init__(self):
        self._replays: list[dict] = []

    def start_replay(
        self,
        execution_log_id: str,
        replay_type: str,
        initiated_by: str,
    ):
        replay = {
            "id": str(uuid4()),
            "execution_log_id": execution_log_id,
            "replay_type": replay_type.upper(),
            "initiated_by": initiated_by,
            "status": "IN_PROGRESS",
            "started_at": datetime.now(timezone.utc).isoformat(),
            "completed_at": None,
            "error": None,
        }
        self._replays.append(replay)
        return replay

    def complete_replay(
        self,
        replay_id: str,
        status: str,
        error: str | None = None,
    ):
        for replay in self._replays:
            if replay["id"] != replay_id:
                continue
            replay["status"] = status.upper()
            replay["completed_at"] = datetime.now(timezone.utc).isoformat()
            replay["error"] = error
            return replay
        raise LookupError(f"Replay '{replay_id}' not found")

    def list_replays(
        self,
        execution_log_id: str | None = None,
        limit: int = 100,
    ):
        entries = self._replays
        if execution_log_id:
            entries = [
                item
                for item in entries
                if item["execution_log_id"] == execution_log_id
            ]
        return list(reversed(entries[-limit:]))

    def get_summary(self):
        total = len(self._replays)
        completed = len(
            [
                item
                for item in self._replays
                if item["status"] == "COMPLETED"
            ]
        )
        failed = len(
            [
                item
                for item in self._replays
                if item["status"] == "FAILED"
            ]
        )
        in_progress = len(
            [
                item
                for item in self._replays
                if item["status"] == "IN_PROGRESS"
            ]
        )
        return {
            "total_replays": total,
            "completed": completed,
            "failed": failed,
            "in_progress": in_progress,
        }
