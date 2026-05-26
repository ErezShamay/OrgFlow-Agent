from datetime import datetime

from pydantic import BaseModel


class AILog(BaseModel):

    provider: str

    model_name: str

    prompt_name: str | None = None

    prompt: str

    response: str | None = None

    success: bool = True

    error_message: str | None = None

    duration_ms: int | None = None

    created_at: datetime | None = None