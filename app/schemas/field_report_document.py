"""
Pydantic models for field visit report document structure (FR-0.3).

Mirrors TypeScript types in orgflow-ui/lib/field-reports/schema/types.ts.
Used for documentation, validation helpers, and future normalization - not
as a strict API envelope (header_fields remains a dict on requests).
"""

from __future__ import annotations

import warnings
from typing import Annotated, Literal

from pydantic import BaseModel, Field

ProjectScheme = Literal[
    "TAMA38_STRENGTHENING",
    "TAMA38_DEMOLITION_REBUILD",
    "TAMA38_RELOCATED_BUILD",
]

StakeholderRole = Literal[
    "developer",
    "project_manager",
    "site_manager",
    "contractor",
    "lawyer_tenants",
    "lawyer_accompanying",
    "architect",
]

FixedTextBlockKind = Literal[
    "safety_disclaimer",
    "non_conformance_disclaimer",
    "winter_recommendations",
    "agreement_notes",
    "custom",
]

ColumnPresetKey = Literal["rich", "simple", "finishing", "progress", "structure"]

BlockColumnId = Literal[
    "location",
    "trade",
    "status",
    "description",
    "notes",
    "photos",
    "completion_date",
    "checklist_item",
]

ReportBlockKind = Literal[
    "progress_table",
    "findings_table",
    "checklist",
    "free_text",
    "image",
]

# Legacy + new header_fields keys accepted by the API (backward compatible).
KNOWN_HEADER_FIELD_KEYS: frozenset[str] = frozenset(
    {
        # Legacy flat fields
        "site_address",
        "developer_name",
        "developer_pm_name",
        "lawyer_name",
        "accompanying_lawyer",
        "contractor_name",
        "architect_name",
        "project_updates",
        "winter_recommendations",
        "contractor_notes",
        "inspector_title",
        "inspector_license",
        "construction_progress",
        # Project metadata (flat or nested)
        "scheme",
        "scheme_label_he",
        "project_start_date",
        "project_end_date",
        "project_grace_end_date",
        "housing_units_count",
        "structure_documentation_date",
        "addressee_label_he",
        "gantt_forecast",
        "illustration_caption_he",
        "tenant_changes_notes",
        # New structured fields (FR-0.1+)
        "project_metadata",
        "stakeholders",
        "main_suppliers",
        "fixed_text_blocks",
        "include_fixed_text_blocks",
        "inspector_notes",
        "blocks",
        # Supervision checklist (field-supervision-checklist-spec §10.1)
        "supervision_meta",
    }
)


class ProjectMetadata(BaseModel):
    """מטא-דאטה של פרויקט בכותרת הדוח."""

    scheme: ProjectScheme | None = None
    scheme_label_he: str | None = None
    project_start_date: str | None = None
    project_end_date: str | None = None
    project_grace_end_date: str | None = None
    housing_units_count: int | None = None
    structure_documentation_date: str | None = None
    addressee_label_he: str | None = None
    architect_name: str | None = None
    gantt_forecast: str | None = None
    site_address: str | None = None
    illustration_caption_he: str | None = None
    illustration_source_he: str | None = None
    illustration_url: str | None = None
    tenant_changes_notes: str | None = None


class Stakeholder(BaseModel):
    """בעל עניין בדוח (יזם, עו\"ד, קבלן וכו')."""

    id: str
    role: StakeholderRole
    name: str
    label_he: str | None = None


class SupplierRow(BaseModel):
    """שורת ספק עיקרי (קטגוריה + vendor)."""

    id: str
    category_he: str
    vendor_name: str


class FixedTextBlock(BaseModel):
    """בלוק טקסט קבוע - disclaimer בטיחות, אי-התאמה, המלצות חורף."""

    id: str
    kind: FixedTextBlockKind
    title_he: str | None = None
    body_he: str
    enabled: bool = True
    sort_order: int | None = None


class BlockColumnDef(BaseModel):
    """הגדרת עמודה בטבלת בלוק."""

    id: BlockColumnId
    header_he: str
    width: int | str | None = None


class ProgressRow(BaseModel):
    """שורה בטבלת התקדמות."""

    id: str
    description: str = ""
    status: str = ""
    completion_date: str = ""
    sort_order: int | None = None


class FindingRow(BaseModel):
    """שורת ממצא - תואמת שורות lines קיימות."""

    id: str
    location: str | None = None
    trade: str | None = None
    status: str | None = None
    description: str | None = None
    notes: str | None = None
    severity: str | None = None
    standard_ref: str | None = None
    catalog_reference_id: str | None = None
    issue_id: str | None = None
    group_key: str | None = None
    group_label_he: str | None = None
    block_id: str | None = None
    linked_issue_id: str | None = None
    sort_order: int | None = None
    has_photo: bool = False
    photo_ids: list[str] | None = None


class ChecklistItem(BaseModel):
    """פריט בצ'קליסט גמר."""

    id: str
    label_he: str
    checked: bool = False
    notes: str | None = None
    sort_order: int | None = None


class ReportBlockBase(BaseModel):
    """שדות משותפים לכל בלוק בגוף הדוח."""

    id: str
    title_he: str
    sort_order: int | None = None


class ProgressTableBlock(ReportBlockBase):
    """בלוק טבלת התקדמות."""

    kind: Literal["progress_table"] = "progress_table"
    column_preset: ColumnPresetKey = "progress"
    rows: list[ProgressRow] = Field(default_factory=list)


class FindingsTableBlock(ReportBlockBase):
    """בלוק טבלת ממצאים."""

    kind: Literal["findings_table"] = "findings_table"
    column_preset: ColumnPresetKey = "rich"
    rows: list[FindingRow] = Field(default_factory=list)


class ChecklistBlock(ReportBlockBase):
    """בלוק צ'קליסט גמר."""

    kind: Literal["checklist"] = "checklist"
    items: list[ChecklistItem] = Field(default_factory=list)


class FreeTextBlock(ReportBlockBase):
    """בלוק טקסט חופשי."""

    kind: Literal["free_text"] = "free_text"
    body_he: str = ""


class ImageBlock(ReportBlockBase):
    """בלוק תמונה - הדמיית פרויקט."""

    kind: Literal["image"] = "image"
    caption_he: str | None = None
    image_url: str | None = None
    storage_path: str | None = None


ReportBlock = Annotated[
    ProgressTableBlock
    | FindingsTableBlock
    | ChecklistBlock
    | FreeTextBlock
    | ImageBlock,
    Field(discriminator="kind"),
]


class VisitReportDocument(BaseModel):
    """
    מסמך דוח ביקור - יעד הנורמליזציה.
    משלב metadata, stakeholders, blocks ושדות legacy.
    """

    id: str
    project_id: str
    visit_type: str
    visit_date: str
    visit_type_label_he: str | None = None
    project_name: str | None = None
    project_metadata: ProjectMetadata | None = None
    stakeholders: list[Stakeholder] = Field(default_factory=list)
    main_suppliers: list[SupplierRow] = Field(default_factory=list)
    fixed_text_blocks: list[FixedTextBlock] = Field(default_factory=list)
    blocks: list[ReportBlock] = Field(default_factory=list)
    header_fields_raw: dict | None = None
    lines: list[FindingRow] = Field(default_factory=list)
    catalog_version: str | None = None
    status: str | None = None
    organization_profile_snapshot: dict | None = None


HEADER_FIELDS_DOC = """
JSON object stored on field_visit_reports.header_fields.

Legacy flat keys (still accepted):
  site_address, developer_name, developer_pm_name, lawyer_name,
  accompanying_lawyer, contractor_name, architect_name,
  project_updates, winter_recommendations, contractor_notes,
  inspector_title, inspector_license, construction_progress[]

New structured keys (optional, dual-write with legacy during migration):
  project_metadata: ProjectMetadata
  stakeholders: Stakeholder[]
  main_suppliers: SupplierRow[]
  fixed_text_blocks: FixedTextBlock[]
  blocks: ReportBlock[]

Unknown keys are allowed for forward compatibility; use
warn_unknown_header_field_keys() to log warnings during development.
"""


def warn_unknown_header_field_keys(
    header_fields: dict | None,
    *,
    report_id: str | None = None,
) -> list[str]:
    """
    Emit warnings for header_fields keys not in KNOWN_HEADER_FIELD_KEYS.
    Does not raise - backward compatible with arbitrary client payloads.
    """
    if not header_fields:
        return []

    unknown = sorted(
        key for key in header_fields if key not in KNOWN_HEADER_FIELD_KEYS
    )
    if not unknown:
        return []

    prefix = f"field report {report_id}: " if report_id else ""
    warnings.warn(
        f"{prefix}unknown header_fields keys: {', '.join(unknown)}",
        stacklevel=2,
    )
    return unknown
