from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

InviteStatus = Literal["none", "pending", "active"]


class ProjectApartmentRecord(BaseModel):
    id: str
    organization_id: str
    project_id: str
    apartment_number: str
    group_key: str
    owner_name: str
    phone: str | None = None
    email: str | None = None
    building: str | None = None
    entrance: str | None = None
    resident_profile_id: str | None = None
    invite_status: InviteStatus = "none"
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ProjectApartmentInput(BaseModel):
    apartment_number: str = Field(min_length=1, max_length=40)
    owner_name: str = Field(min_length=1, max_length=200)
    phone: str | None = Field(default=None, max_length=40)
    email: str | None = Field(default=None, max_length=200)
    building: str | None = Field(default=None, max_length=80)
    entrance: str | None = Field(default=None, max_length=40)


class BulkUpsertProjectApartmentsRequest(BaseModel):
    apartments: list[ProjectApartmentInput] = Field(min_length=1)


class BulkUpsertProjectApartmentsResponse(BaseModel):
    apartments: list[ProjectApartmentRecord]
    created: int
    updated: int


class ProjectApartmentListResponse(BaseModel):
    apartments: list[ProjectApartmentRecord]
    total: int


class InviteResidentResponse(BaseModel):
    apartment_id: str
    profile_id: str
    invite_status: InviteStatus
    email_status: str
    invite_link: str | None = None


class ResidentPortalProgressItem(BaseModel):
    description: str
    status: str
    completion_date: str
    report_id: str
    visit_date: str | None = None
    report_title: str | None = None


ReportSource = Literal["field_visit", "weekly", "legacy"]


class ResidentPortalReportLine(BaseModel):
    id: str
    report_id: str
    description: str | None = None
    status: str | None = None
    location: str | None = None
    visit_date: str | None = None
    report_title: str | None = None
    source: ReportSource = "field_visit"


class ResidentPortalReportSummary(BaseModel):
    id: str
    title: str | None = None
    visit_type: str | None = None
    visit_date: str | None = None
    status: str | None = None
    pdf_url: str | None = None
    line_count: int = 0
    source: ReportSource = "field_visit"


class ResidentPortalGanttMilestone(BaseModel):
    date: str
    label: str
    kind: Literal["progress", "inspection", "completion"]
    status: str | None = None


class ResidentPortalGanttRow(BaseModel):
    task_key: str
    label: str
    status: str = ""
    start_date: str | None = None
    end_date: str | None = None
    milestones: list[ResidentPortalGanttMilestone] = Field(default_factory=list)


class ResidentPortalIssueSummary(BaseModel):
    id: str
    title: str | None = None
    status: str | None = None
    tenant_view_status_he: str | None = None
    trade: str | None = None
    location: str | None = None
    severity: str | None = None
    catalog_issue_id: str | None = None
    standard_ref: str | None = None
    first_seen_at: str | None = None
    last_seen_at: str | None = None


ResidentPortalStatusLevel = Literal["green", "yellow", "red"]


class ResidentPortalStatusCard(BaseModel):
    card_key: str
    title: str
    level: ResidentPortalStatusLevel
    open_count: int = 0
    closed_count: int = 0
    critical_open_count: int = 0
    issue_count: int = 0


class ResidentPortalPdfDownload(BaseModel):
    report_id: str
    title: str | None = None
    visit_date: str | None = None
    pdf_url: str
    source: ReportSource = "field_visit"


class ResidentPortalPayload(BaseModel):
    apartment: ProjectApartmentRecord
    project_name: str | None = None
    default_view: Literal["trust_dashboard"] = "trust_dashboard"
    status_cards: list[ResidentPortalStatusCard] = Field(default_factory=list)
    pdf_downloads: list[ResidentPortalPdfDownload] = Field(default_factory=list)
    reports: list[ResidentPortalReportSummary]
    report_lines: list[ResidentPortalReportLine]
    issues: list[ResidentPortalIssueSummary]
    progress_timeline: list[ResidentPortalProgressItem]
    gantt_rows: list[ResidentPortalGanttRow] = Field(default_factory=list)
    read_only: bool = True
