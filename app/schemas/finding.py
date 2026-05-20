from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class Finding(BaseModel):
    report_id: str
    project_id: str

    finding_type: str
    severity: str

    title: str
    summary: str

    source_text: str

    status: str = "detected"

    metadata: dict[str, Any] = Field(default_factory=dict)

    created_at: datetime | None = None