"""Z3 — spatial bootstrap response models."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ProjectSpatialBootstrapResponse(BaseModel):
    apartments_created: int = 0
    public_areas: list[str] = Field(default_factory=list)
    skipped: bool = False
    floors: int | None = None
    units_per_floor: int | None = None
