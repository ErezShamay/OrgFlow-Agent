from datetime import datetime

from pydantic import BaseModel


class CircuitBreaker(
    BaseModel
):

    id: str

    breaker_key: str

    state: str

    failure_count: int = 0

    last_failure_at: datetime | None = None

    cooldown_until: datetime | None = None

    created_at: datetime | None = None