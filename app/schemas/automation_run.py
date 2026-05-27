from datetime import datetime

from pydantic import BaseModel


class AutomationRun(
    BaseModel
):

    id: str

    job_name: str

    started_at: datetime

    completed_at: datetime | None = None

    status: str

    processed_count: int = 0

    error_count: int = 0

    metadata: dict | None = None