"""Pure aggregation for project supervision dashboard (gate D1)."""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Literal

from app.repositories.project_apartment_repository import (
    build_apartment_group_key,
)
from app.schemas.project_supervision_dashboard import (
    ProjectSupervisionDashboardResponse,
    SupervisionApartmentProgress,
    SupervisionDashboardKpis,
    SupervisionOverallStatus,
    SupervisionPublicAreaProgress,
    SupervisionTradeDetailResponse,
    SupervisionTradeLineItem,
    SupervisionTradeProgress,
)
from app.schemas.quality_issue import (
    IssueVisibility,
    QualityIssueSeverity,
    QualityIssueStatus,
)

ELIGIBLE_REPORT_STATUSES = frozenset({"CLOSED", "LOCKED"})
CHECKLIST_BLOCK_KINDS = frozenset({"supervision_checklist", "checklist"})
COUNTABLE_CHECKLIST_STATUSES = frozenset({"OK", "DEFECT"})
IN_TREATMENT_ISSUE_STATUSES = frozenset(
    {
        QualityIssueStatus.IN_REMEDIATION.value,
        QualityIssueStatus.PENDING_VERIFICATION.value,
    }
)
OPEN_ISSUE_STATUSES = frozenset(
    status.value
    for status in QualityIssueStatus
    if status != QualityIssueStatus.CLOSED
)
UNKNOWN_TRADE_LABEL_HE = "ללא קטגוריה"

ItemBucket = Literal["completed", "with_defects", "in_treatment"]


@dataclass
class ProgressCounts:
    total: int = 0
    completed: int = 0
    with_defects: int = 0
    in_treatment: int = 0

    def add_bucket(self, bucket: ItemBucket) -> None:
        self.total += 1
        if bucket == "completed":
            self.completed += 1
        elif bucket == "with_defects":
            self.with_defects += 1
        elif bucket == "in_treatment":
            self.in_treatment += 1

    def merge(self, other: ProgressCounts) -> None:
        self.total += other.total
        self.completed += other.completed
        self.with_defects += other.with_defects
        self.in_treatment += other.in_treatment

    @property
    def progress_percent(self) -> int:
        if self.total <= 0:
            return 0
        return round(self.completed / self.total * 100)

    def to_kpis(self) -> SupervisionDashboardKpis:
        return SupervisionDashboardKpis(
            in_treatment=self.in_treatment,
            with_defects=self.with_defects,
            completed=self.completed,
            total_items=self.total,
            progress_percent=self.progress_percent,
        )


@dataclass
class AggregationState:
    project_counts: ProgressCounts = field(default_factory=ProgressCounts)
    trade_counts: dict[str, ProgressCounts] = field(
        default_factory=lambda: defaultdict(ProgressCounts)
    )
    trade_labels: dict[str, str] = field(default_factory=dict)
    apartment_counts: dict[str, ProgressCounts] = field(
        default_factory=lambda: defaultdict(ProgressCounts)
    )
    apartment_meta: dict[str, dict[str, Any]] = field(default_factory=dict)
    public_area_counts: dict[str, ProgressCounts] = field(
        default_factory=lambda: defaultdict(ProgressCounts)
    )
    public_area_meta: dict[str, dict[str, Any]] = field(default_factory=dict)
    counted_line_ids: set[str] = field(default_factory=set)
    counted_issue_ids: set[str] = field(default_factory=set)
    has_critical_open_issue: bool = False


def _report_timestamp(report: dict[str, Any]) -> str:
    for key in ("updated_at", "closed_at", "created_at"):
        value = str(report.get(key) or "").strip()
        if value:
            return value
    return ""


def _normalize_header_fields(report: dict[str, Any]) -> dict[str, Any]:
    raw = report.get("header_fields")
    return raw if isinstance(raw, dict) else {}


def _supervision_meta(report: dict[str, Any]) -> dict[str, Any]:
    meta = _normalize_header_fields(report).get("supervision_meta")
    return meta if isinstance(meta, dict) else {}


def report_apartment_number(report: dict[str, Any]) -> str | None:
    meta = _supervision_meta(report)
    apartment_number = str(meta.get("apartment_number") or "").strip()
    if apartment_number:
        return apartment_number

    for block in iter_checklist_blocks(report):
        block_number = str(block.get("apartment_number") or "").strip()
        if block_number:
            return block_number

    return None


def report_public_area_key(report: dict[str, Any]) -> tuple[str, str] | None:
    meta = _supervision_meta(report)
    visit_scope = str(meta.get("visit_scope") or "").strip().upper()
    if visit_scope != "PUBLIC_AREA":
        return None

    area_id = str(meta.get("public_area_id") or "").strip()
    label_he = str(meta.get("public_area_label_he") or "").strip()
    if area_id:
        return area_id, label_he or area_id
    if label_he:
        return label_he, label_he
    return None


def iter_checklist_blocks(report: dict[str, Any]) -> list[dict[str, Any]]:
    blocks = _normalize_header_fields(report).get("blocks")
    if not isinstance(blocks, list):
        return []

    return [
        block
        for block in blocks
        if isinstance(block, dict)
        and str(block.get("kind") or "") in CHECKLIST_BLOCK_KINDS
    ]


def iter_checklist_items(report: dict[str, Any]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for block in iter_checklist_blocks(report):
        block_items = block.get("items")
        if not isinstance(block_items, list):
            continue
        for item in block_items:
            if isinstance(item, dict):
                items.append(item)
    return items


def pick_latest_reports_by_apartment(
    reports: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}

    for report in reports:
        if str(report.get("status") or "") not in ELIGIBLE_REPORT_STATUSES:
            continue

        apartment_number = report_apartment_number(report)
        if not apartment_number:
            continue

        existing = latest.get(apartment_number)
        if existing is None or _report_timestamp(report) > _report_timestamp(
            existing
        ):
            latest[apartment_number] = report

    return latest


def pick_latest_reports_by_public_area(
    reports: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    labels: dict[str, str] = {}

    for report in reports:
        if str(report.get("status") or "") not in ELIGIBLE_REPORT_STATUSES:
            continue

        area = report_public_area_key(report)
        if area is None:
            continue

        area_key, label_he = area
        labels[area_key] = label_he
        existing = latest.get(area_key)
        if existing is None or _report_timestamp(report) > _report_timestamp(
            existing
        ):
            latest[area_key] = report

    return latest


def _slug_trade_key(raw: str) -> str:
    normalized = raw.strip().lower()
    normalized = re.sub(r"\s+", "-", normalized)
    normalized = re.sub(r"[^a-z0-9\u0590-\u05ff-]+", "", normalized)
    return normalized or "unknown"


def resolve_trade_label_he(
    item: dict[str, Any],
    *,
    issue: dict[str, Any] | None = None,
) -> str:
    if issue:
        trade = str(issue.get("trade") or "").strip()
        if trade:
            return trade

    category_name = str(item.get("category_name_he") or "").strip()
    if category_name:
        return category_name

    return UNKNOWN_TRADE_LABEL_HE


def resolve_trade_key(
    item: dict[str, Any],
    *,
    issue: dict[str, Any] | None = None,
) -> str:
    category_id = str(item.get("category_id") or "").strip()
    if category_id:
        return category_id.lower()

    return _slug_trade_key(resolve_trade_label_he(item, issue=issue))


def _is_published_issue(issue: dict[str, Any] | None) -> bool:
    if issue is None:
        return False
    visibility = str(issue.get("visibility") or IssueVisibility.PUBLISHED.value)
    return visibility.upper() == IssueVisibility.PUBLISHED.value


def _issue_for_line(
    line_id: str | None,
    issues_by_line_id: dict[str, dict[str, Any]],
) -> dict[str, Any] | None:
    if not line_id:
        return None
    return issues_by_line_id.get(str(line_id).strip())


def classify_checklist_item(
    item: dict[str, Any],
    *,
    issues_by_line_id: dict[str, dict[str, Any]],
) -> ItemBucket | None:
    status = str(item.get("status") or "").strip().upper()
    if status not in COUNTABLE_CHECKLIST_STATUSES:
        return None

    linked_line_id = str(item.get("linked_line_id") or "").strip() or None
    issue = _issue_for_line(linked_line_id, issues_by_line_id)

    if _is_published_issue(issue):
        issue_status = str(issue.get("status") or "").strip().upper()
        if issue_status == QualityIssueStatus.CLOSED.value:
            return "completed"
        if issue_status in IN_TREATMENT_ISSUE_STATUSES:
            return "in_treatment"
        return "with_defects"

    if status == "OK":
        return "completed"
    if status == "DEFECT":
        return "with_defects"

    return None


def build_issues_by_line_id(
    issues: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}

    for issue in issues:
        if not _is_published_issue(issue):
            continue

        for field in ("first_seen_line_id", "last_seen_line_id"):
            line_id = str(issue.get(field) or "").strip()
            if line_id:
                indexed[line_id] = issue

    return indexed


def count_open_issues_by_group_key(
    issues: list[dict[str, Any]],
) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)

    for issue in issues:
        if not _is_published_issue(issue):
            continue
        if str(issue.get("status") or "") not in OPEN_ISSUE_STATUSES:
            continue

        group_key = str(issue.get("group_key") or "").strip()
        if group_key:
            counts[group_key] += 1

    return counts


def track_critical_open_issues(
    issues: list[dict[str, Any]],
) -> bool:
    for issue in issues:
        if not _is_published_issue(issue):
            continue
        if str(issue.get("status") or "") not in OPEN_ISSUE_STATUSES:
            continue
        if (
            str(issue.get("severity") or "").strip().upper()
            == QualityIssueSeverity.CRITICAL.value
        ):
            return True
    return False


def _apply_checklist_item(
    state: AggregationState,
    *,
    item: dict[str, Any],
    issues_by_line_id: dict[str, dict[str, Any]],
    trade_counts: dict[str, ProgressCounts],
    trade_labels: dict[str, str],
    scope_counts: ProgressCounts,
) -> None:
    bucket = classify_checklist_item(
        item,
        issues_by_line_id=issues_by_line_id,
    )
    if bucket is None:
        return

    linked_line_id = str(item.get("linked_line_id") or "").strip() or None
    issue = _issue_for_line(linked_line_id, issues_by_line_id)

    trade_key = resolve_trade_key(item, issue=issue)
    trade_label = resolve_trade_label_he(item, issue=issue)
    trade_labels[trade_key] = trade_label

    scope_counts.add_bucket(bucket)
    trade_counts[trade_key].add_bucket(bucket)
    state.project_counts.add_bucket(bucket)

    if linked_line_id:
        state.counted_line_ids.add(linked_line_id)
    if issue and issue.get("id"):
        state.counted_issue_ids.add(str(issue["id"]))


def _apply_orphan_issues(
    state: AggregationState,
    *,
    issues: list[dict[str, Any]],
    scope_counts: ProgressCounts,
    group_key: str | None = None,
) -> None:
    for issue in issues:
        if not _is_published_issue(issue):
            continue

        issue_id = str(issue.get("id") or "")
        if issue_id and issue_id in state.counted_issue_ids:
            continue

        if group_key is not None:
            if str(issue.get("group_key") or "").strip() != group_key:
                continue

        line_ids = {
            str(issue.get(field) or "").strip()
            for field in ("first_seen_line_id", "last_seen_line_id")
        }
        line_ids.discard("")
        if line_ids.intersection(state.counted_line_ids):
            continue

        issue_status = str(issue.get("status") or "").strip().upper()
        if issue_status == QualityIssueStatus.CLOSED.value:
            continue

        if issue_status in IN_TREATMENT_ISSUE_STATUSES:
            bucket: ItemBucket = "in_treatment"
        else:
            bucket = "with_defects"

        trade_key = _slug_trade_key(
            str(issue.get("trade") or "").strip() or UNKNOWN_TRADE_LABEL_HE
        )
        trade_label = str(issue.get("trade") or "").strip() or UNKNOWN_TRADE_LABEL_HE
        state.trade_labels[trade_key] = trade_label

        scope_counts.add_bucket(bucket)
        state.trade_counts[trade_key].add_bucket(bucket)
        state.project_counts.add_bucket(bucket)

        if issue_id:
            state.counted_issue_ids.add(issue_id)


def aggregate_supervision_dashboard(
    *,
    project_id: str,
    project_name: str,
    apartments: list[dict[str, Any]],
    reports: list[dict[str, Any]],
    issues: list[dict[str, Any]],
) -> ProjectSupervisionDashboardResponse:
    state = AggregationState()
    state.has_critical_open_issue = track_critical_open_issues(issues)

    issues_by_line_id = build_issues_by_line_id(issues)
    open_issues_by_group = count_open_issues_by_group_key(issues)

    latest_by_apartment = pick_latest_reports_by_apartment(reports)
    latest_by_public_area = pick_latest_reports_by_public_area(reports)

    apartment_rows: list[SupervisionApartmentProgress] = []

    apartments_by_number = {
        str(row.get("apartment_number") or "").strip(): row
        for row in apartments
        if str(row.get("apartment_number") or "").strip()
    }

    seen_apartment_numbers: set[str] = set()

    for apartment_number, report in sorted(
        latest_by_apartment.items(),
        key=lambda item: item[0],
    ):
        seen_apartment_numbers.add(apartment_number)
        apartment_row = apartments_by_number.get(apartment_number, {})
        group_key = str(apartment_row.get("group_key") or "").strip() or (
            build_apartment_group_key(apartment_number)
        )

        scope_counts = ProgressCounts()
        trade_counts: dict[str, ProgressCounts] = defaultdict(ProgressCounts)
        trade_labels: dict[str, str] = {}

        for item in iter_checklist_items(report):
            _apply_checklist_item(
                state,
                item=item,
                issues_by_line_id=issues_by_line_id,
                trade_counts=trade_counts,
                trade_labels=trade_labels,
                scope_counts=scope_counts,
            )

        _apply_orphan_issues(
            state,
            issues=issues,
            scope_counts=scope_counts,
            group_key=group_key,
        )

        for trade_key, counts in trade_counts.items():
            state.trade_counts[trade_key].merge(counts)
            state.trade_labels[trade_key] = trade_labels[trade_key]

        state.apartment_counts[apartment_number] = scope_counts
        state.apartment_meta[apartment_number] = {
            "apartment_id": apartment_row.get("id"),
            "group_key": group_key,
            "last_visit_report_id": report.get("id"),
            "last_visit_at": _report_timestamp(report),
        }

        apartment_rows.append(
            SupervisionApartmentProgress(
                apartment_id=(
                    str(apartment_row.get("id"))
                    if apartment_row.get("id")
                    else None
                ),
                apartment_number=apartment_number,
                group_key=group_key,
                total_items=scope_counts.total,
                completed=scope_counts.completed,
                with_defects=scope_counts.with_defects,
                in_treatment=scope_counts.in_treatment,
                open_issues_count=open_issues_by_group.get(group_key, 0),
                progress_percent=scope_counts.progress_percent,
                last_visit_report_id=str(report.get("id") or "") or None,
                last_visit_at=_report_timestamp(report) or None,
            )
        )

    for apartment_number, apartment_row in sorted(
        apartments_by_number.items(),
        key=lambda item: item[0],
    ):
        if apartment_number in seen_apartment_numbers:
            continue

        group_key = str(apartment_row.get("group_key") or "").strip() or (
            build_apartment_group_key(apartment_number)
        )
        scope_counts = ProgressCounts()
        _apply_orphan_issues(
            state,
            issues=issues,
            scope_counts=scope_counts,
            group_key=group_key,
        )

        if scope_counts.total <= 0 and open_issues_by_group.get(group_key, 0) <= 0:
            apartment_rows.append(
                SupervisionApartmentProgress(
                    apartment_id=(
                        str(apartment_row.get("id"))
                        if apartment_row.get("id")
                        else None
                    ),
                    apartment_number=apartment_number,
                    group_key=group_key,
                    open_issues_count=open_issues_by_group.get(group_key, 0),
                )
            )
            continue

        state.apartment_counts[apartment_number] = scope_counts
        apartment_rows.append(
            SupervisionApartmentProgress(
                apartment_id=(
                    str(apartment_row.get("id"))
                    if apartment_row.get("id")
                    else None
                ),
                apartment_number=apartment_number,
                group_key=group_key,
                total_items=scope_counts.total,
                completed=scope_counts.completed,
                with_defects=scope_counts.with_defects,
                in_treatment=scope_counts.in_treatment,
                open_issues_count=open_issues_by_group.get(group_key, 0),
                progress_percent=scope_counts.progress_percent,
            )
        )

    public_area_rows: list[SupervisionPublicAreaProgress] = []
    for area_key, report in sorted(latest_by_public_area.items()):
        scope_counts = ProgressCounts()
        trade_counts: dict[str, ProgressCounts] = defaultdict(ProgressCounts)
        trade_labels: dict[str, str] = {}

        for item in iter_checklist_items(report):
            _apply_checklist_item(
                state,
                item=item,
                issues_by_line_id=issues_by_line_id,
                trade_counts=trade_counts,
                trade_labels=trade_labels,
                scope_counts=scope_counts,
            )

        area = report_public_area_key(report)
        label_he = area[1] if area else area_key

        for trade_key, counts in trade_counts.items():
            state.trade_counts[trade_key].merge(counts)
            state.trade_labels[trade_key] = trade_labels[trade_key]

        public_area_rows.append(
            SupervisionPublicAreaProgress(
                area_key=area_key,
                label_he=label_he,
                total_items=scope_counts.total,
                completed=scope_counts.completed,
                with_defects=scope_counts.with_defects,
                in_treatment=scope_counts.in_treatment,
                open_issues_count=open_issues_by_group.get(f"public_area:{area_key}", 0),
                progress_percent=scope_counts.progress_percent,
                last_visit_report_id=str(report.get("id") or "") or None,
                last_visit_at=_report_timestamp(report) or None,
            )
        )

    trades = [
        SupervisionTradeProgress(
            trade_key=trade_key,
            label_he=state.trade_labels.get(trade_key, trade_key),
            total_items=counts.total,
            completed=counts.completed,
            with_defects=counts.with_defects,
            in_treatment=counts.in_treatment,
            progress_percent=counts.progress_percent,
        )
        for trade_key, counts in sorted(
            state.trade_counts.items(),
            key=lambda item: (-item[1].total, state.trade_labels.get(item[0], item[0])),
        )
    ]

    overall_status = resolve_overall_status(
        counts=state.project_counts,
        has_critical_open_issue=state.has_critical_open_issue,
    )

    apartment_rows.sort(key=lambda row: row.apartment_number)

    return ProjectSupervisionDashboardResponse(
        project_id=project_id,
        project_name=project_name,
        overall_status=overall_status,
        kpis=state.project_counts.to_kpis(),
        trades=trades,
        apartments=apartment_rows,
        public_areas=public_area_rows,
    )


def resolve_overall_status(
    *,
    counts: ProgressCounts,
    has_critical_open_issue: bool,
) -> SupervisionOverallStatus:
    if has_critical_open_issue:
        return SupervisionOverallStatus.CRITICAL

    if counts.with_defects > 0 or counts.in_treatment > 0:
        return SupervisionOverallStatus.ATTENTION

    return SupervisionOverallStatus.HEALTHY


_BUCKET_STATUS_HE: dict[ItemBucket, str] = {
    "completed": "הושלם",
    "with_defects": "ליקוי",
    "in_treatment": "בטיפול",
}


def _bucket_status_he(bucket: ItemBucket) -> str:
    return _BUCKET_STATUS_HE[bucket]


def _collect_trade_items_from_report(
    report: dict[str, Any],
    *,
    trade_key: str,
    issues_by_line_id: dict[str, dict[str, Any]],
    scope_label_he: str,
    apartment_number: str | None = None,
    apartment_id: str | None = None,
) -> tuple[list[SupervisionTradeLineItem], ProgressCounts, str]:
    items: list[SupervisionTradeLineItem] = []
    counts = ProgressCounts()
    label_he = trade_key

    for item in iter_checklist_items(report):
        linked_line_id = str(item.get("linked_line_id") or "").strip() or None
        issue = _issue_for_line(linked_line_id, issues_by_line_id)
        item_trade_key = resolve_trade_key(item, issue=issue)
        if item_trade_key != trade_key:
            continue

        bucket = classify_checklist_item(
            item,
            issues_by_line_id=issues_by_line_id,
        )
        if bucket is None:
            continue

        label_he = resolve_trade_label_he(item, issue=issue)
        counts.add_bucket(bucket)
        items.append(
            SupervisionTradeLineItem(
                scope_label_he=scope_label_he,
                apartment_number=apartment_number,
                apartment_id=apartment_id,
                item_name_he=str(
                    item.get("issue_name_he")
                    or item.get("catalog_issue_id")
                    or "פריט"
                ).strip(),
                status=bucket,
                display_status_he=_bucket_status_he(bucket),
                linked_issue_id=(
                    str(issue.get("id")) if issue and issue.get("id") else None
                ),
            )
        )

    return items, counts, label_he


def aggregate_supervision_trade_detail(
    *,
    project_id: str,
    project_name: str,
    trade_key: str,
    apartments: list[dict[str, Any]],
    reports: list[dict[str, Any]],
    issues: list[dict[str, Any]],
) -> SupervisionTradeDetailResponse | None:
    normalized_trade_key = trade_key.strip().lower()
    if not normalized_trade_key:
        return None

    issues_by_line_id = build_issues_by_line_id(issues)
    apartments_by_number = {
        str(row.get("apartment_number") or "").strip(): row
        for row in apartments
        if str(row.get("apartment_number") or "").strip()
    }

    line_items: list[SupervisionTradeLineItem] = []
    trade_counts = ProgressCounts()
    label_he = normalized_trade_key

    for apartment_number, report in sorted(
        pick_latest_reports_by_apartment(reports).items(),
        key=lambda item: item[0],
    ):
        apartment_row = apartments_by_number.get(apartment_number, {})
        apartment_id = (
            str(apartment_row.get("id")) if apartment_row.get("id") else None
        )
        items, counts, resolved_label = _collect_trade_items_from_report(
            report,
            trade_key=normalized_trade_key,
            issues_by_line_id=issues_by_line_id,
            scope_label_he=f"דירה {apartment_number}",
            apartment_number=apartment_number,
            apartment_id=apartment_id,
        )
        if items:
            label_he = resolved_label
        line_items.extend(items)
        trade_counts.merge(counts)

    for area_key, report in sorted(pick_latest_reports_by_public_area(reports).items()):
        area = report_public_area_key(report)
        label = area[1] if area else area_key
        items, counts, resolved_label = _collect_trade_items_from_report(
            report,
            trade_key=normalized_trade_key,
            issues_by_line_id=issues_by_line_id,
            scope_label_he=label,
        )
        if items:
            label_he = resolved_label
        line_items.extend(items)
        trade_counts.merge(counts)

    if trade_counts.total <= 0:
        return None

    line_items.sort(
        key=lambda row: (row.scope_label_he, row.item_name_he),
    )

    return SupervisionTradeDetailResponse(
        project_id=project_id,
        project_name=project_name,
        trade_key=normalized_trade_key,
        label_he=label_he,
        kpis=trade_counts.to_kpis(),
        items=line_items,
    )
