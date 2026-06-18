"""Z2 — project template schemas (spatial bootstrap metadata)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.config.field_report_project_scheme import (
    VALID_PROJECT_SCHEMES,
    is_valid_project_scheme,
)
from app.config.project_template_seed import is_known_public_area_id


class ProjectTemplate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    organization_id: str | None = None
    scheme: str
    template_name_he: str
    default_floors: int | None = None
    default_units_per_floor: int | None = None
    public_area_ids: list[str] = Field(default_factory=list)
    catalog_filter: dict[str, Any] | None = None
    is_active: bool = True
    created_at: datetime | None = None

    @field_validator("scheme")
    @classmethod
    def validate_scheme(cls, value: str) -> str:
        if not is_valid_project_scheme(value):
            raise ValueError("invalid project scheme")
        return value

    @field_validator("default_floors", "default_units_per_floor")
    @classmethod
    def validate_positive_ints(cls, value: int | None) -> int | None:
        if value is not None and value < 1:
            raise ValueError("must be a positive integer")
        return value

    @field_validator("public_area_ids")
    @classmethod
    def validate_public_area_ids(cls, values: list[str]) -> list[str]:
        normalized: list[str] = []
        for value in values:
            trimmed = value.strip()
            if not trimmed:
                continue
            if not is_known_public_area_id(trimmed):
                raise ValueError(f"unknown public area id: {trimmed}")
            if trimmed not in normalized:
                normalized.append(trimmed)
        return normalized

    @classmethod
    def from_record(cls, record: dict[str, Any]) -> ProjectTemplate:
        return cls.model_validate(record)


class ProjectTemplateResolveResponse(BaseModel):
    template: ProjectTemplate
    source: str = Field(
        description="organization | global | seed"
    )


VALID_PROJECT_SCHEME_VALUES: frozenset[str] = frozenset(VALID_PROJECT_SCHEMES)
