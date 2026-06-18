"""
QC Spec 0.1–0.2 + API schemas (1.1.4) - QualityIssue registry.

See docs/PRODUCT-SPEC-LOCKED.md §5 and docs/FIELD-REPORT-FINALIZE-PIPELINE.md.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class QualityIssueSeverity(StrEnum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

    @property
    def rank(self) -> int:
        return _SEVERITY_RANK[self]

    @property
    def label_he(self) -> str:
        return _SEVERITY_LABELS_HE[self]


class IssueVisibility(StrEnum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"


class QualityIssueStatus(StrEnum):
    OPEN = "OPEN"
    IN_REMEDIATION = "IN_REMEDIATION"
    PENDING_VERIFICATION = "PENDING_VERIFICATION"
    CLOSED = "CLOSED"
    REOPENED = "REOPENED"

    @property
    def label_he(self) -> str:
        return _STATUS_LABELS_HE[self]

    @property
    def is_terminal(self) -> bool:
        return self == QualityIssueStatus.CLOSED


_SEVERITY_RANK: dict[QualityIssueSeverity, int] = {
    QualityIssueSeverity.CRITICAL: 4,
    QualityIssueSeverity.HIGH: 3,
    QualityIssueSeverity.MEDIUM: 2,
    QualityIssueSeverity.LOW: 1,
}

_SEVERITY_LABELS_HE: dict[QualityIssueSeverity, str] = {
    QualityIssueSeverity.CRITICAL: "קריטי",
    QualityIssueSeverity.HIGH: "גבוה",
    QualityIssueSeverity.MEDIUM: "בינוני",
    QualityIssueSeverity.LOW: "נמוך",
}

_STATUS_LABELS_HE: dict[QualityIssueStatus, str] = {
    QualityIssueStatus.OPEN: "פתוח",
    QualityIssueStatus.IN_REMEDIATION: "בטיפול",
    QualityIssueStatus.PENDING_VERIFICATION: "ממתין לאימות",
    QualityIssueStatus.CLOSED: "סגור",
    QualityIssueStatus.REOPENED: "נפתח מחדש",
}

_TENANT_VIEW_STATUS_HE_BY_STATUS: dict[QualityIssueStatus, str] = {
    QualityIssueStatus.OPEN: "הקבלן זומן לתיקון הליקוי",
    QualityIssueStatus.IN_REMEDIATION: "הקבלן זומן לתיקון הליקוי",
    QualityIssueStatus.REOPENED: "הקבלן זומן לתיקון הליקוי",
    QualityIssueStatus.PENDING_VERIFICATION: "הליקוי בבדיקה על ידי המפקח",
    QualityIssueStatus.CLOSED: "הליקוי טופל",
}


def resolve_tenant_view_status_he(
    status: QualityIssueStatus | str | None,
) -> str | None:
    if status is None:
        return None
    if isinstance(status, QualityIssueStatus):
        return _TENANT_VIEW_STATUS_HE_BY_STATUS.get(status)
    normalized = str(status).strip().upper()
    if not normalized:
        return None
    try:
        resolved = QualityIssueStatus(normalized)
    except ValueError:
        return None
    return _TENANT_VIEW_STATUS_HE_BY_STATUS.get(resolved)

CATALOG_SEVERITY_TO_REGISTRY: dict[str, QualityIssueSeverity] = {
    "critical": QualityIssueSeverity.CRITICAL,
    "high": QualityIssueSeverity.HIGH,
    "medium": QualityIssueSeverity.MEDIUM,
    "low": QualityIssueSeverity.LOW,
}

DEFAULT_QUALITY_ISSUE_SEVERITY = QualityIssueSeverity.MEDIUM
DEFAULT_QUALITY_ISSUE_STATUS = QualityIssueStatus.OPEN
DEFAULT_ISSUE_VISIBILITY = IssueVisibility.DRAFT


def is_visible_to_resident(visibility: IssueVisibility | str | None) -> bool:
    if visibility is None:
        return True
    normalized = (
        visibility.value
        if isinstance(visibility, IssueVisibility)
        else str(visibility).strip().upper()
    )
    return normalized == IssueVisibility.PUBLISHED.value

QUALITY_ISSUE_STATUS_TRANSITIONS: dict[
    QualityIssueStatus,
    frozenset[QualityIssueStatus],
] = {
    QualityIssueStatus.OPEN: frozenset(
        {
            QualityIssueStatus.IN_REMEDIATION,
            QualityIssueStatus.CLOSED,
        }
    ),
    QualityIssueStatus.IN_REMEDIATION: frozenset(
        {QualityIssueStatus.PENDING_VERIFICATION}
    ),
    QualityIssueStatus.PENDING_VERIFICATION: frozenset(
        {
            QualityIssueStatus.CLOSED,
            QualityIssueStatus.OPEN,
        }
    ),
    QualityIssueStatus.CLOSED: frozenset({QualityIssueStatus.REOPENED}),
    QualityIssueStatus.REOPENED: frozenset(
        {
            QualityIssueStatus.IN_REMEDIATION,
            QualityIssueStatus.CLOSED,
        }
    ),
}


def normalize_catalog_severity(
    value: str | None,
) -> QualityIssueSeverity | None:
    if not value or not str(value).strip():
        return None
    return CATALOG_SEVERITY_TO_REGISTRY.get(str(value).strip().lower())


def resolve_issue_severity(
    *,
    catalog_severity: str | None = None,
    row_severity: str | None = None,
) -> QualityIssueSeverity:
    for candidate in (catalog_severity, row_severity):
        resolved = normalize_catalog_severity(candidate)
        if resolved is not None:
            return resolved
    return DEFAULT_QUALITY_ISSUE_SEVERITY


def is_valid_status_transition(
    current: QualityIssueStatus,
    target: QualityIssueStatus,
) -> bool:
    if current == target:
        return True
    return target in QUALITY_ISSUE_STATUS_TRANSITIONS.get(current, frozenset())


def build_materialization_key(report_id: str, line_id: str) -> str:
    return f"{report_id}:{line_id}"


def build_upload_finding_materialization_key(
    report_id: str,
    finding_id: str,
) -> str:
    """Stable idempotency key for AI upload findings → quality_issues (stage 5.7)."""
    return f"upload:{report_id}:{finding_id}"


def build_match_key(
    *,
    location: str | None = None,
    trade: str | None = None,
    group_key: str | None = None,
) -> str:
    parts = (
        _normalize_match_component(location),
        _normalize_match_component(trade),
        _normalize_match_component(group_key),
    )
    return "|".join(parts)


def derive_issue_title(
    *,
    description: str | None = None,
    location: str | None = None,
    trade: str | None = None,
    catalog_issue_name: str | None = None,
    max_description_len: int = 80,
) -> str:
    if catalog_issue_name and catalog_issue_name.strip():
        return catalog_issue_name.strip()

    desc = (description or "").strip()
    if desc:
        if len(desc) <= max_description_len:
            return desc
        return desc[: max_description_len - 1].rstrip() + "…"

    location_part = (location or "").strip()
    trade_part = (trade or "").strip()
    if location_part and trade_part:
        return f"{location_part} - {trade_part}"
    if location_part:
        return location_part
    if trade_part:
        return trade_part

    return "ליקוי ללא תיאור"


def finding_row_qualifies_for_materialization(
    *,
    description: str | None = None,
    catalog_issue_id: str | None = None,
    photo_ids: list[str] | None = None,
) -> bool:
    if catalog_issue_id and str(catalog_issue_id).strip():
        return True
    if (description or "").strip():
        return True
    return bool(photo_ids)


def _normalize_match_component(value: str | None) -> str:
    if not value:
        return ""
    return " ".join(str(value).strip().lower().split())


class QualityIssue(BaseModel):
    """Issue registry entity - lives across field visits."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    project_id: str

    title: str
    description: str | None = None
    location: str | None = None
    trade: str | None = None
    group_key: str | None = None
    group_label_he: str | None = None
    standard_ref: str | None = None
    standard_id: str | None = None

    severity: QualityIssueSeverity = DEFAULT_QUALITY_ISSUE_SEVERITY
    status: QualityIssueStatus = DEFAULT_QUALITY_ISSUE_STATUS
    tenant_view_status_he: str | None = None
    visibility: IssueVisibility = DEFAULT_ISSUE_VISIBILITY

    catalog_issue_id: str | None = None
    catalog_reference_id: str | None = None

    first_seen_report_id: str
    first_seen_line_id: str | None = None
    first_seen_at: datetime
    last_seen_report_id: str
    last_seen_line_id: str | None = None
    last_seen_at: datetime
    closed_at: datetime | None = None
    closed_by: str | None = None
    recurrence_count: int = Field(default=0, ge=0)

    photo_ids: list[str] = Field(default_factory=list)
    materialization_key: str

    created_at: datetime | None = None
    updated_at: datetime | None = None


class QualityIssueEventType(StrEnum):
    DETECTED = "DETECTED"
    CREATED_FROM_FIELD = "CREATED_FROM_FIELD"
    PUBLISHED_FROM_FINALIZE = "PUBLISHED_FROM_FINALIZE"
    LINKED = "LINKED"
    REMEDIATION_SUBMITTED = "REMEDIATION_SUBMITTED"
    VERIFIED_CLOSED = "VERIFIED_CLOSED"
    REOPENED = "REOPENED"
    STATUS_CHANGED = "STATUS_CHANGED"

    @property
    def label_he(self) -> str:
        return _EVENT_TYPE_LABELS_HE[self]


_EVENT_TYPE_LABELS_HE: dict[QualityIssueEventType, str] = {
    QualityIssueEventType.DETECTED: "התגלות",
    QualityIssueEventType.CREATED_FROM_FIELD: "נוצר משטח",
    QualityIssueEventType.PUBLISHED_FROM_FINALIZE: "פורסם ב-Finalize",
    QualityIssueEventType.LINKED: "קישור לליקוי קיים",
    QualityIssueEventType.REMEDIATION_SUBMITTED: "הוגש תיקון",
    QualityIssueEventType.VERIFIED_CLOSED: "אושר ונסגר",
    QualityIssueEventType.REOPENED: "נפתח מחדש",
    QualityIssueEventType.STATUS_CHANGED: "שינוי סטטוס",
}

_EVENT_TYPES_REQUIRING_ACTOR: frozenset[QualityIssueEventType] = frozenset(
    {
        QualityIssueEventType.REMEDIATION_SUBMITTED,
        QualityIssueEventType.VERIFIED_CLOSED,
        QualityIssueEventType.STATUS_CHANGED,
    }
)

_EVENT_TYPES_REQUIRING_REPORT: frozenset[QualityIssueEventType] = frozenset(
    {
        QualityIssueEventType.DETECTED,
        QualityIssueEventType.CREATED_FROM_FIELD,
        QualityIssueEventType.PUBLISHED_FROM_FINALIZE,
        QualityIssueEventType.LINKED,
        QualityIssueEventType.VERIFIED_CLOSED,
        QualityIssueEventType.REOPENED,
    }
)


class DetectedEventPayload(BaseModel):
    materialization_key: str
    severity: QualityIssueSeverity
    title: str
    catalog_issue_id: str | None = None
    location: str | None = None
    trade: str | None = None
    group_key: str | None = None
    source: str | None = None
    finding_id: str | None = None
    finding_type: str | None = None


class CreatedFromFieldEventPayload(BaseModel):
    materialization_key: str
    severity: QualityIssueSeverity
    title: str
    catalog_issue_id: str | None = None
    checklist_item_id: str | None = None
    location: str | None = None
    trade: str | None = None
    group_key: str | None = None


class PublishedFromFinalizeEventPayload(BaseModel):
    materialization_key: str
    previous_visibility: IssueVisibility = IssueVisibility.DRAFT
    severity: QualityIssueSeverity
    title: str
    catalog_issue_id: str | None = None
    location: str | None = None
    trade: str | None = None
    group_key: str | None = None


class LinkedEventPayload(BaseModel):
    match_key: str | None = None
    match_source: str = "manual"
    previous_last_seen_at: datetime | None = None

    @field_validator("match_source")
    @classmethod
    def validate_match_source(cls, value: str) -> str:
        normalized = (value or "manual").strip().lower()
        if normalized not in {"auto", "manual"}:
            raise ValueError("match_source must be 'auto' or 'manual'")
        return normalized


class RemediationSubmittedEventPayload(BaseModel):
    from_status: QualityIssueStatus
    to_status: QualityIssueStatus
    photo_ids: list[str] = Field(default_factory=list)
    notes: str | None = None


class VerifiedClosedEventPayload(BaseModel):
    from_status: QualityIssueStatus
    to_status: QualityIssueStatus = QualityIssueStatus.CLOSED
    notes: str | None = None

    @field_validator("to_status")
    @classmethod
    def validate_to_status_closed(
        cls,
        value: QualityIssueStatus,
    ) -> QualityIssueStatus:
        if value != QualityIssueStatus.CLOSED:
            raise ValueError("VERIFIED_CLOSED payload to_status must be CLOSED")
        return value


class ReopenedEventPayload(BaseModel):
    from_status: QualityIssueStatus = QualityIssueStatus.CLOSED
    to_status: QualityIssueStatus = QualityIssueStatus.REOPENED
    recurrence_count: int = Field(ge=1)
    previous_closed_at: datetime | None = None
    match_key: str | None = None


class StatusChangedEventPayload(BaseModel):
    from_status: QualityIssueStatus
    to_status: QualityIssueStatus
    reason: str | None = None


_EVENT_PAYLOAD_MODELS: dict[QualityIssueEventType, type[BaseModel]] = {
    QualityIssueEventType.DETECTED: DetectedEventPayload,
    QualityIssueEventType.CREATED_FROM_FIELD: CreatedFromFieldEventPayload,
    QualityIssueEventType.PUBLISHED_FROM_FINALIZE: PublishedFromFinalizeEventPayload,
    QualityIssueEventType.LINKED: LinkedEventPayload,
    QualityIssueEventType.REMEDIATION_SUBMITTED: RemediationSubmittedEventPayload,
    QualityIssueEventType.VERIFIED_CLOSED: VerifiedClosedEventPayload,
    QualityIssueEventType.REOPENED: ReopenedEventPayload,
    QualityIssueEventType.STATUS_CHANGED: StatusChangedEventPayload,
}


class QualityIssueEvent(BaseModel):
    """Append-only audit entry for a quality issue."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    issue_id: str
    event_type: QualityIssueEventType
    report_id: str | None = None
    line_id: str | None = None
    actor_id: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None


class QualityIssueCreateRequest(BaseModel):
    """POST /projects/{id}/issues - manual or materialization follow-up."""

    title: str = Field(min_length=1, max_length=500)
    description: str | None = None
    location: str | None = Field(default=None, max_length=500)
    trade: str | None = Field(default=None, max_length=200)
    group_key: str | None = Field(default=None, max_length=120)
    group_label_he: str | None = Field(default=None, max_length=200)
    standard_ref: str | None = Field(default=None, max_length=200)
    severity: QualityIssueSeverity = DEFAULT_QUALITY_ISSUE_SEVERITY
    visibility: IssueVisibility = DEFAULT_ISSUE_VISIBILITY
    catalog_issue_id: str | None = Field(default=None, max_length=120)
    catalog_reference_id: str | None = Field(default=None, max_length=120)
    first_seen_report_id: str
    first_seen_line_id: str | None = None
    first_seen_at: datetime
    last_seen_report_id: str | None = None
    last_seen_line_id: str | None = None
    last_seen_at: datetime | None = None
    photo_ids: list[str] = Field(default_factory=list)
    materialization_key: str = Field(min_length=1, max_length=200)

    @model_validator(mode="before")
    @classmethod
    def _default_last_seen_from_first(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        normalized = dict(data)
        if not normalized.get("last_seen_report_id") and normalized.get(
            "first_seen_report_id"
        ):
            normalized["last_seen_report_id"] = normalized["first_seen_report_id"]
        if not normalized.get("last_seen_line_id") and normalized.get(
            "first_seen_line_id"
        ):
            normalized["last_seen_line_id"] = normalized["first_seen_line_id"]
        if not normalized.get("last_seen_at") and normalized.get("first_seen_at"):
            normalized["last_seen_at"] = normalized["first_seen_at"]
        return normalized


class QualityIssueUpdateRequest(BaseModel):
    """PATCH /issues/{id} - partial update including status transitions."""

    title: str | None = Field(default=None, min_length=1, max_length=500)
    description: str | None = None
    location: str | None = Field(default=None, max_length=500)
    trade: str | None = Field(default=None, max_length=200)
    group_key: str | None = Field(default=None, max_length=120)
    group_label_he: str | None = Field(default=None, max_length=200)
    standard_ref: str | None = Field(default=None, max_length=200)
    severity: QualityIssueSeverity | None = None
    status: QualityIssueStatus | None = None
    catalog_issue_id: str | None = Field(default=None, max_length=120)
    last_seen_report_id: str | None = None
    last_seen_line_id: str | None = None
    last_seen_at: datetime | None = None
    closed_at: datetime | None = None
    closed_by: str | None = None
    photo_ids: list[str] | None = None
    notes: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def _require_at_least_one_field(self) -> Self:
        if not self.model_dump(exclude_unset=True):
            raise ValueError("At least one field must be provided")
        return self


class QualityIssueStatusUpdateRequest(BaseModel):
    """Focused status transition - used by verify/remediate flows."""

    status: QualityIssueStatus
    report_id: str | None = None
    line_id: str | None = None
    notes: str | None = Field(default=None, max_length=2000)
    photo_ids: list[str] | None = None


class QualityIssueListQuery(BaseModel):
    """GET /projects/{id}/issues query parameters."""

    status: list[QualityIssueStatus] | None = None
    severity: list[QualityIssueSeverity] | None = None
    trade: str | None = Field(default=None, max_length=200)
    search: str | None = Field(default=None, max_length=200)
    limit: int = Field(default=50, ge=1, le=200)
    offset: int = Field(default=0, ge=0)


class QualityIssueEventCreateRequest(BaseModel):
    """Internal - append audit event when issue state changes."""

    event_type: QualityIssueEventType
    report_id: str | None = None
    line_id: str | None = None
    actor_id: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _validate_event_requirements(self) -> Self:
        validate_event_fields(
            event_type=self.event_type,
            report_id=self.report_id,
            actor_id=self.actor_id,
            payload=self.payload,
        )
        return self


class QualityIssueListResponse(BaseModel):
    project_id: str
    total: int
    limit: int
    offset: int
    items: list[QualityIssue]


class QualityIssueOrgListResponse(BaseModel):
    """GET /issues - cross-project list for contractor / supervisor views."""

    organization_id: str
    total: int
    limit: int
    offset: int
    items: list[QualityIssue]


class FindingMatchInput(BaseModel):
    """Finding row fields used for open-issue matching (QC spec §7)."""

    location: str | None = Field(default=None, max_length=500)
    trade: str | None = Field(default=None, max_length=200)
    group_key: str | None = Field(default=None, max_length=120)
    catalog_issue_id: str | None = Field(default=None, max_length=120)


class QualityIssueMatchCandidate(BaseModel):
    """Ranked open issue that matches a finding row by match_key."""

    issue: QualityIssue
    match_key: str
    score: float = Field(ge=0.0, le=1.0)


class QualityIssueSuggestMatchesRequest(BaseModel):
    """POST /projects/{id}/issues/suggest-matches - finding row for matching."""

    location: str | None = Field(default=None, max_length=500)
    trade: str | None = Field(default=None, max_length=200)
    group_key: str | None = Field(default=None, max_length=120)
    catalog_issue_id: str | None = Field(default=None, max_length=120)
    limit: int = Field(default=5, ge=1, le=20)

    def to_finding_input(self) -> FindingMatchInput:
        return FindingMatchInput(
            location=self.location,
            trade=self.trade,
            group_key=self.group_key,
            catalog_issue_id=self.catalog_issue_id,
        )


class QualityIssueSuggestMatchesResponse(BaseModel):
    """Ranked open-issue matches for a finding row."""

    project_id: str
    match_key: str
    total: int = Field(ge=0)
    candidates: list[QualityIssueMatchCandidate] = Field(default_factory=list)


class QualityIssueOpenListResponse(BaseModel):
    """GET /projects/{id}/issues/open - active issues for field-report matching."""

    project_id: str
    total: int = Field(ge=0)
    items: list[QualityIssue] = Field(default_factory=list)


class QualityIssueVisitDiffCategory(StrEnum):
    """Issue change category for a single field visit."""

    NEW = "new"
    CLOSED = "closed"
    STILL_OPEN = "still_open"
    RECURRING = "recurring"

    @property
    def label_he(self) -> str:
        return _VISIT_DIFF_CATEGORY_LABELS_HE[self]


_VISIT_DIFF_CATEGORY_LABELS_HE: dict[QualityIssueVisitDiffCategory, str] = {
    QualityIssueVisitDiffCategory.NEW: "חדש",
    QualityIssueVisitDiffCategory.CLOSED: "נסגר",
    QualityIssueVisitDiffCategory.STILL_OPEN: "עדיין פתוח",
    QualityIssueVisitDiffCategory.RECURRING: "חוזר",
}


class QualityIssueVisitDiffEntry(BaseModel):
    """Issue appearing in a visit diff bucket."""

    issue: QualityIssue
    line_id: str | None = None
    category: QualityIssueVisitDiffCategory


class QualityIssueVisitDiffResponse(BaseModel):
    """GET /projects/{id}/visits/{report_id}/issue-diff - visit issue changes."""

    project_id: str
    report_id: str
    new: list[QualityIssueVisitDiffEntry] = Field(default_factory=list)
    closed: list[QualityIssueVisitDiffEntry] = Field(default_factory=list)
    still_open: list[QualityIssueVisitDiffEntry] = Field(default_factory=list)
    recurring: list[QualityIssueVisitDiffEntry] = Field(default_factory=list)
    total_new: int = Field(default=0, ge=0)
    total_closed: int = Field(default=0, ge=0)
    total_still_open: int = Field(default=0, ge=0)
    total_recurring: int = Field(default=0, ge=0)


class QualityIssueDetailResponse(BaseModel):
    issue: QualityIssue
    events: list[QualityIssueEvent] = Field(default_factory=list)
    catalog_link: QualityIssueCatalogLink | None = None


class QualityPortfolioProjectSummary(BaseModel):
    project_id: str
    project_name: str | None = None
    open_total: int = Field(ge=0)
    open_critical: int = Field(ge=0)
    critical_open_over_14_days: int = Field(default=0, ge=0)
    average_open_days: float | None = None


class QualityPortfolioSummaryResponse(BaseModel):
    organization_id: str
    total_open: int = Field(ge=0)
    total_open_critical: int = Field(ge=0)
    critical_open_over_14_days: int = Field(ge=0)
    average_open_days: float | None = None
    closed_within_30_days_percent: float | None = None
    last_report_at: datetime | None = None
    projects: list[QualityPortfolioProjectSummary] = Field(default_factory=list)


class QualityPortfolioLiveSnapshot(BaseModel):
    """Lightweight portfolio counters for R1 live updates."""

    organization_id: str
    total_open: int = Field(ge=0)
    total_open_critical: int = Field(ge=0)
    updated_at: datetime


class QualityTradeHeatmapCell(BaseModel):
    """Open-issue counts for a single trade row."""

    trade: str
    open_total: int = Field(default=0, ge=0)
    open_critical: int = Field(default=0, ge=0)
    open_high: int = Field(default=0, ge=0)
    open_medium: int = Field(default=0, ge=0)
    open_low: int = Field(default=0, ge=0)


class QualityTradeHeatmapResponse(BaseModel):
    """GET /portfolio/quality-trade-heatmap - roadmap 6.1."""

    organization_id: str
    project_id: str | None = None
    total_open: int = Field(ge=0)
    cells: list[QualityTradeHeatmapCell] = Field(default_factory=list)


class QualityRecurringIssueRankEntry(BaseModel):
    """Single recurring issue row for portfolio analytics - roadmap 6.2."""

    issue_id: str
    title: str
    trade: str | None = None
    location: str | None = None
    recurrence_count: int = Field(ge=1)
    project_id: str
    project_name: str | None = None
    contractor_name: str | None = None
    status: QualityIssueStatus
    severity: QualityIssueSeverity


class QualityContractorRecurringRankEntry(BaseModel):
    """Subcontractor pressure from recurring issues - roadmap 6.2."""

    contractor_name: str
    recurring_issue_count: int = Field(ge=0)
    total_recurrence_count: int = Field(ge=0)
    project_count: int = Field(ge=0)


class QualityRecurringRankingsResponse(BaseModel):
    """GET /portfolio/quality-recurring-rankings - roadmap 6.2."""

    organization_id: str
    project_id: str | None = None
    total_recurring: int = Field(ge=0)
    issues: list[QualityRecurringIssueRankEntry] = Field(default_factory=list)
    contractors: list[QualityContractorRecurringRankEntry] = Field(
        default_factory=list
    )


class QualityPeriodicReportSummary(BaseModel):
    """KPI block for periodic developer report - roadmap 6.3."""

    total_issues: int = Field(ge=0)
    open_total: int = Field(ge=0)
    open_critical: int = Field(ge=0)
    closed_total: int = Field(ge=0)
    recurring_total: int = Field(ge=0)


class QualityPeriodicReportProjectRow(BaseModel):
    project_id: str
    project_name: str | None = None
    contractor_name: str | None = None
    issue_total: int = Field(ge=0)
    open_total: int = Field(ge=0)
    open_critical: int = Field(ge=0)
    recurring_total: int = Field(ge=0)


class QualityPeriodicReportIssueRow(BaseModel):
    issue_id: str
    title: str
    project_id: str
    project_name: str | None = None
    contractor_name: str | None = None
    status: str
    severity: str
    trade: str | None = None
    location: str | None = None
    standard_ref: str | None = None
    catalog_issue_id: str | None = None
    recurrence_count: int = Field(default=0, ge=0)
    first_seen_at: datetime | None = None
    last_seen_at: datetime | None = None

    def open_rank(self) -> int:
        return 1 if self.status in {
            "OPEN",
            "IN_REMEDIATION",
            "PENDING_VERIFICATION",
            "REOPENED",
        } else 0

    def severity_rank(self) -> int:
        order = {
            QualityIssueSeverity.CRITICAL.value: 4,
            QualityIssueSeverity.HIGH.value: 3,
            QualityIssueSeverity.MEDIUM.value: 2,
            QualityIssueSeverity.LOW.value: 1,
        }
        return order.get(self.severity, 0)


class QualityPeriodicReportResponse(BaseModel):
    """GET /portfolio/quality-periodic-report - roadmap 6.3."""

    organization_id: str
    project_id: str | None = None
    period_days: int = Field(ge=1)
    period_start: datetime
    period_end: datetime
    generated_at: datetime
    summary: QualityPeriodicReportSummary
    projects: list[QualityPeriodicReportProjectRow] = Field(default_factory=list)
    issues: list[QualityPeriodicReportIssueRow] = Field(default_factory=list)


class QualityIssueCatalogLink(BaseModel):
    """Resolved catalog section for a quality issue - roadmap 6.5."""

    issue_id: str
    issue_name_he: str
    top_family: str
    category_id: str
    category_name_he: str
    standard_ref: str | None = None
    category_standard_id: str | None = None
    standard_id: str | None = None


class QualityIssuePhotoUploadResponse(BaseModel):
    """POST /issues/{id}/photos - remediation photo stored for contractor."""

    issue_id: str
    photo_id: str
    url: str


class QualityCriticalStaleAlertDelivery(BaseModel):
    to: str | None = None
    status: str
    issue_ids: list[str] = Field(default_factory=list)
    error: str | None = None


class QualityCriticalStaleAlertResponse(BaseModel):
    """POST /portfolio/quality-alerts/critical-stale - roadmap 4.3.1."""

    organization_id: str
    threshold_days: int = Field(ge=1)
    stale_issue_count: int = Field(ge=0)
    digest_count: int = Field(ge=0)
    skipped_issue_ids: list[str] = Field(default_factory=list)
    deliveries: list[QualityCriticalStaleAlertDelivery] = Field(
        default_factory=list
    )


class NewCriticalIssueAlertResponse(BaseModel):
    """Per-report CRITICAL issue alerts from Finalize (N02)."""

    organization_id: str
    project_id: str
    report_id: str
    critical_issue_count: int = Field(ge=0)
    digest_count: int = Field(ge=0)
    skipped_issue_ids: list[str] = Field(default_factory=list)
    deliveries: list[QualityCriticalStaleAlertDelivery] = Field(
        default_factory=list
    )


def parse_quality_issue_row(row: dict[str, Any]) -> QualityIssue:
    return QualityIssue.model_validate(_normalize_db_row(row))


def parse_quality_issue_event_row(row: dict[str, Any]) -> QualityIssueEvent:
    return QualityIssueEvent.model_validate(_normalize_db_row(row))


def validate_status_update(
    *,
    current_status: QualityIssueStatus,
    target_status: QualityIssueStatus,
) -> None:
    if not is_valid_status_transition(current_status, target_status):
        raise ValueError(
            f"Invalid status transition: {current_status.value} → {target_status.value}"
        )


def _normalize_db_row(row: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(row)
    if normalized.get("photo_ids") is None:
        normalized["photo_ids"] = []
    if normalized.get("payload") is None:
        normalized["payload"] = {}
    if normalized.get("visibility") is None:
        normalized["visibility"] = IssueVisibility.PUBLISHED.value
    return normalized


def preferred_event_type_for_transition(
    from_status: QualityIssueStatus | None,
    to_status: QualityIssueStatus,
) -> QualityIssueEventType:
    if from_status is None and to_status == QualityIssueStatus.OPEN:
        return QualityIssueEventType.DETECTED
    if (
        from_status == QualityIssueStatus.CLOSED
        and to_status == QualityIssueStatus.REOPENED
    ):
        return QualityIssueEventType.REOPENED
    if (
        from_status == QualityIssueStatus.IN_REMEDIATION
        and to_status == QualityIssueStatus.PENDING_VERIFICATION
    ):
        return QualityIssueEventType.REMEDIATION_SUBMITTED
    if to_status == QualityIssueStatus.CLOSED:
        return QualityIssueEventType.VERIFIED_CLOSED
    return QualityIssueEventType.STATUS_CHANGED


def validate_event_payload(
    event_type: QualityIssueEventType,
    payload: dict[str, Any] | None,
) -> dict[str, Any]:
    model = _EVENT_PAYLOAD_MODELS[event_type]
    parsed = model.model_validate(payload or {})
    result = parsed.model_dump(mode="json", exclude_none=True)
    _validate_payload_status_transitions(event_type, parsed)
    return result


def validate_event_fields(
    *,
    event_type: QualityIssueEventType,
    report_id: str | None = None,
    actor_id: str | None = None,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    validated_payload = validate_event_payload(event_type, payload)

    if event_type in _EVENT_TYPES_REQUIRING_REPORT and not (report_id or "").strip():
        raise ValueError(f"{event_type.value} requires report_id")

    if event_type in _EVENT_TYPES_REQUIRING_ACTOR and not (actor_id or "").strip():
        raise ValueError(f"{event_type.value} requires actor_id")

    return validated_payload


def _validate_payload_status_transitions(
    event_type: QualityIssueEventType,
    payload: BaseModel,
) -> None:
    if event_type in {
        QualityIssueEventType.DETECTED,
        QualityIssueEventType.CREATED_FROM_FIELD,
        QualityIssueEventType.PUBLISHED_FROM_FINALIZE,
    }:
        return

    from_status = getattr(payload, "from_status", None)
    to_status = getattr(payload, "to_status", None)
    if from_status is None or to_status is None:
        return

    if not is_valid_status_transition(from_status, to_status):
        raise ValueError(
            f"Invalid status transition in {event_type.value} payload: "
            f"{from_status.value} → {to_status.value}"
        )
