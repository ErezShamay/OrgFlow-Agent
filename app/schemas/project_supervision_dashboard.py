"""Schemas for project supervision dashboard (gates D1–D2)."""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field


class SupervisionOverallStatus(StrEnum):
    HEALTHY = "healthy"
    ATTENTION = "attention"
    CRITICAL = "critical"


class SupervisionDashboardKpis(BaseModel):
    in_treatment: int = Field(ge=0, default=0)
    with_defects: int = Field(ge=0, default=0)
    completed: int = Field(ge=0, default=0)
    total_items: int = Field(ge=0, default=0)
    progress_percent: int = Field(ge=0, le=100, default=0)


class SupervisionTradeProgress(BaseModel):
    trade_key: str
    label_he: str
    total_items: int = Field(ge=0, default=0)
    completed: int = Field(ge=0, default=0)
    with_defects: int = Field(ge=0, default=0)
    in_treatment: int = Field(ge=0, default=0)
    progress_percent: int = Field(ge=0, le=100, default=0)


class SupervisionApartmentProgress(BaseModel):
    apartment_id: str | None = None
    apartment_number: str
    group_key: str
    total_items: int = Field(ge=0, default=0)
    completed: int = Field(ge=0, default=0)
    with_defects: int = Field(ge=0, default=0)
    in_treatment: int = Field(ge=0, default=0)
    open_issues_count: int = Field(ge=0, default=0)
    progress_percent: int = Field(ge=0, le=100, default=0)
    last_visit_report_id: str | None = None
    last_visit_at: str | None = None


class SupervisionPublicAreaProgress(BaseModel):
    area_key: str
    label_he: str
    total_items: int = Field(ge=0, default=0)
    completed: int = Field(ge=0, default=0)
    with_defects: int = Field(ge=0, default=0)
    in_treatment: int = Field(ge=0, default=0)
    open_issues_count: int = Field(ge=0, default=0)
    progress_percent: int = Field(ge=0, le=100, default=0)
    last_visit_report_id: str | None = None
    last_visit_at: str | None = None


class ProjectSupervisionDashboardResponse(BaseModel):
    project_id: str
    project_name: str
    overall_status: SupervisionOverallStatus
    kpis: SupervisionDashboardKpis
    trades: list[SupervisionTradeProgress] = Field(default_factory=list)
    apartments: list[SupervisionApartmentProgress] = Field(default_factory=list)
    public_areas: list[SupervisionPublicAreaProgress] = Field(
        default_factory=list
    )


class SupervisionTradeLineItem(BaseModel):
    scope_label_he: str
    apartment_number: str | None = None
    apartment_id: str | None = None
    item_name_he: str
    status: str
    display_status_he: str
    linked_issue_id: str | None = None


class SupervisionTradeDetailResponse(BaseModel):
    project_id: str
    project_name: str
    trade_key: str
    label_he: str
    kpis: SupervisionDashboardKpis
    items: list[SupervisionTradeLineItem] = Field(default_factory=list)


class SupervisionProjectSummary(BaseModel):
    project_id: str
    overall_status: SupervisionOverallStatus
    progress_percent: int = Field(ge=0, le=100, default=0)


class SupervisionProjectSummariesResponse(BaseModel):
    items: list[SupervisionProjectSummary] = Field(default_factory=list)


OverallStatusLiteral = Literal["healthy", "attention", "critical"]
