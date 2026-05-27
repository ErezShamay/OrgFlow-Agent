from datetime import datetime

from pydantic import BaseModel


class AIExecutionLog(
    BaseModel
):

    id: str

    project_id: str | None = None

    execution_type: str

    status: str

    confidence_score: int | None = None

    confidence_level: str | None = None

    details: dict | None = None

    created_at: datetime | None = None

    retry_count: int = 0

    last_retry_at: datetime | None = None

    next_retry_at: datetime | None = None

    replayable: bool = True

    dead_lettered: bool = False

    recovery_locked: bool = False

    recovery_locked_at: datetime | None = None

    failure_type: str | None = None

    severity: str | None = None
