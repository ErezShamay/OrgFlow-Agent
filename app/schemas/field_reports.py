from datetime import date, datetime
from typing import Literal, Self

from pydantic import BaseModel, Field, model_validator

from app.schemas.field_report_document import (
    HEADER_FIELDS_DOC,
    warn_unknown_header_field_keys,
)


class FieldReportModuleStatus(BaseModel):
    organization_id: str
    is_enabled: bool
    enabled_at: datetime | None = None
    disabled_at: datetime | None = None
    enabled_by_profile_id: str | None = None
    storage_available: bool = True


class FieldReportModuleToggleRequest(BaseModel):
    is_enabled: bool


class FieldReportOrganizationProfile(BaseModel):
    organization_id: str
    organization_name: str
    contact_email: str | None = None
    report_phone: str | None = None
    report_address_line: str | None = None
    report_city: str | None = None
    report_tagline: str | None = None
    logo_storage_path: str | None = None
    logo_url: str | None = None


class FieldReportOrganizationProfileUpdateRequest(BaseModel):
    report_phone: str | None = Field(default=None, max_length=100)
    report_address_line: str | None = Field(
        default=None,
        max_length=255,
    )
    report_city: str | None = Field(default=None, max_length=120)
    report_tagline: str | None = Field(default=None, max_length=255)
    logo_storage_path: str | None = Field(
        default=None,
        max_length=1024,
    )


class FieldVisitReportCreateRequest(BaseModel):
    project_id: str
    visit_type: str = Field(
        description=(
            "STRUCTURE_SITE, FINISHING_APARTMENTS, or MIXED (סיור משולב)"
        )
    )
    visit_date: date
    header_fields: dict = Field(
        default_factory=dict,
        description=HEADER_FIELDS_DOC.strip(),
    )
    catalog_version: str | None = None
    client_report_uuid: str | None = Field(
        default=None,
        description=(
            "Optional stable UUID from the field device (offline-first sync)"
        ),
    )

    @model_validator(mode="after")
    def _warn_unknown_header_keys(self) -> Self:
        warn_unknown_header_field_keys(self.header_fields)
        return self


class FieldVisitReportSyncLineRequest(BaseModel):
    """שורת דוח לסנכרון bulk - `client_line_uuid` חובה (§7 ג.ב.2)."""

    client_line_uuid: str
    location: str | None = None
    trade: str | None = None
    status: str | None = None
    description: str | None = None
    notes: str | None = None
    severity: str | None = None
    standard_ref: str | None = None
    engineering_impact: str | None = None
    issue_id: str | None = None
    catalog_version: str | None = None
    top_family: str | None = None
    category_id: str | None = None
    category_name_he: str | None = None
    sort_order: int | None = None
    group_key: str | None = Field(default=None, max_length=120)
    group_label_he: str | None = Field(default=None, max_length=120)
    block_id: str | None = Field(default=None, max_length=120)
    linked_issue_id: str | None = None


class FieldVisitReportSyncRequest(BaseModel):
    """גוף `PUT /field-reports/visits/sync` - upsert לפי `client_report_uuid`."""

    client_report_uuid: str
    project_id: str
    visit_type: str
    visit_date: date
    header_fields: dict = Field(
        default_factory=dict,
        description=HEADER_FIELDS_DOC.strip(),
    )
    catalog_version: str | None = None
    organization_profile_snapshot: dict | None = None
    status: Literal["IN_PROGRESS", "CLOSED"] | None = None
    closed_at: datetime | str | None = None
    lines: list[FieldVisitReportSyncLineRequest] = Field(
        default_factory=list
    )

    @model_validator(mode="after")
    def _warn_unknown_header_keys(self) -> Self:
        warn_unknown_header_field_keys(self.header_fields)
        return self


class FieldVisitReportSyncResponse(BaseModel):
    created: bool
    client_report_uuid: str
    id: str
    report: dict


class FieldVisitReportUpdateRequest(BaseModel):
    visit_date: date | None = None
    header_fields: dict | None = Field(
        default=None,
        description=HEADER_FIELDS_DOC.strip(),
    )
    catalog_version: str | None = None

    @model_validator(mode="after")
    def _warn_unknown_header_keys(self) -> Self:
        warn_unknown_header_field_keys(self.header_fields)
        return self


class FieldVisitReportLineCreateRequest(BaseModel):
    location: str | None = None
    trade: str | None = None
    status: str | None = None
    description: str | None = None
    notes: str | None = None
    severity: str | None = None
    standard_ref: str | None = None
    engineering_impact: str | None = None
    issue_id: str | None = None
    catalog_version: str | None = None
    top_family: str | None = None
    category_id: str | None = None
    category_name_he: str | None = None
    target_elements: str | None = None
    sort_order: int | None = None
    group_key: str | None = Field(
        default=None,
        max_length=120,
        description="Stable row group key, e.g. apartment:3",
    )
    group_label_he: str | None = Field(
        default=None,
        max_length=120,
        description="Hebrew group label for PDF sub-headers",
    )
    block_id: str | None = Field(
        default=None,
        max_length=120,
        description="Optional link to header_fields.blocks[].id",
    )
    client_line_uuid: str | None = Field(
        default=None,
        description=(
            "Optional stable UUID from the field device (offline-first sync)"
        ),
    )
    linked_issue_id: str | None = Field(
        default=None,
        description="Optional link to an existing quality_issues.id (QC matching)",
    )


class FieldVisitReportLineUpdateRequest(BaseModel):
    location: str | None = None
    trade: str | None = None
    status: str | None = None
    description: str | None = None
    notes: str | None = None
    severity: str | None = None
    standard_ref: str | None = None
    engineering_impact: str | None = None
    issue_id: str | None = None
    catalog_version: str | None = None
    top_family: str | None = None
    category_id: str | None = None
    category_name_he: str | None = None
    sort_order: int | None = None
    group_key: str | None = Field(default=None, max_length=120)
    group_label_he: str | None = Field(default=None, max_length=120)
    block_id: str | None = Field(default=None, max_length=120)
    linked_issue_id: str | None = Field(
        default=None,
        description="Optional link to an existing quality_issues.id (QC matching)",
    )


class FieldVisitReportSummary(BaseModel):
    id: str
    client_report_uuid: str | None = None
    organization_id: str
    project_id: str
    project_name: str | None = None
    created_by_profile_id: str
    visit_type: str
    visit_type_label_he: str
    status: str
    status_label_he: str
    visit_date: date | str
    header_fields: dict = Field(default_factory=dict)
    catalog_version: str | None = None
    closed_at: datetime | None = None
    locked_at: datetime | None = None
    created_at: datetime | str | None = None
    updated_at: datetime | str | None = None
    lines: list[dict] = Field(default_factory=list)
    line_count: int = 0
    is_editable: bool = True
    can_reopen: bool = False
    can_send_to_core: bool = False
    was_closed: bool = False
    organization_profile_snapshot: dict | None = None


class FieldVisitReportClosePreview(BaseModel):
    line_count: int = 0
    empty_line_count: int = 0
    empty_line_ids: list[str] = Field(default_factory=list)
    catalog_warning_count: int = 0
    warnings: list[str] = Field(default_factory=list)


class FieldVisitReportLineSummary(BaseModel):
    id: str
    client_line_uuid: str | None = None
    report_id: str
    sort_order: int
    location: str | None = None
    trade: str | None = None
    status: str | None = None
    description: str | None = None
    notes: str | None = None
    severity: str | None = None
    standard_ref: str | None = None
    engineering_impact: str | None = None
    issue_id: str | None = None
    catalog_version: str | None = None
    top_family: str | None = None
    category_id: str | None = None
    category_name_he: str | None = None
    photo_storage_path: str | None = None
    has_photo: bool = False
    photo_url: str | None = None
    photo_ids: list[str] = Field(default_factory=list)
    photos: list[dict] = Field(
        default_factory=list,
        description="Per-photo metadata with id and url",
    )
    has_catalog_issue: bool = False
    group_key: str | None = None
    group_label_he: str | None = None
    block_id: str | None = None
    created_at: datetime | str | None = None
    updated_at: datetime | str | None = None


class OpenReportReminderDelivery(BaseModel):
    to: str | None = None
    status: str
    report_ids: list[str] = Field(default_factory=list)
    error: str | None = None


class OpenReportReminderResponse(BaseModel):
    """POST /portfolio/quality-alerts/open-reports - roadmap 4.3.2."""

    organization_id: str
    threshold_days: int = Field(ge=1)
    overdue_report_count: int = Field(ge=0)
    digest_count: int = Field(ge=0)
    skipped_report_ids: list[str] = Field(default_factory=list)
    deliveries: list[OpenReportReminderDelivery] = Field(default_factory=list)
