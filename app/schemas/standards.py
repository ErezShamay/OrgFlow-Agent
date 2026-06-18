"""L4 — standards_and_regulations schemas."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class StandardAndRegulation(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    standard_code: str = Field(min_length=1, max_length=50)
    category: str = Field(min_length=1, max_length=100)
    title: str = Field(min_length=1, max_length=255)
    raw_legal_text: str = Field(min_length=1)
    recommended_remedy: str | None = None
    version: str | None = Field(default=None, max_length=20)
    effective_from: date | str | None = None
    superseded_by: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @classmethod
    def from_record(cls, record: dict[str, Any]) -> StandardAndRegulation:
        return cls.model_validate(record)


class StandardResolveResult(BaseModel):
    """Resolved standard link for catalog issues or quality issues."""

    standard_id: str
    standard_code: str
    title: str
    category: str
    recommended_remedy: str | None = None
    matched_by: str = Field(
        description="standard_id | standard_code | standard_ref | ref_alias"
    )
    standard_ref: str | None = None
