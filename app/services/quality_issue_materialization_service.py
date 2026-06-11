from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field

from app.exceptions.exceptions import NotFoundError, ValidationError
from app.repositories.field_visit_report_line_photo_repository import (
    FieldVisitReportLinePhotoRepository,
)
from app.repositories.field_visit_report_line_repository import (
    FieldVisitReportLineRepository,
)
from app.repositories.field_visit_report_repository import (
    FieldVisitReportRepository,
)
from app.repositories.quality_issue_repository import (
    QualityIssueEventRepository,
    QualityIssueRepository,
)
from app.schemas.field_report_document import FindingRow
from app.schemas.quality_issue import (
    QualityIssueCreateRequest,
    QualityIssueEventType,
    QualityIssueStatus,
    build_match_key,
    build_materialization_key,
    derive_issue_title,
    finding_row_qualifies_for_materialization,
    resolve_issue_severity,
    validate_event_fields,
)
from app.services.field_report_catalog_service import (
    FieldReportCatalogService,
)

LEGACY_LINE_PHOTO_ID = "legacy"
CLOSED_REPORT_STATUS = "CLOSED"


class MaterializationResult(BaseModel):
    """Outcome of materializing quality issues from a closed field report."""

    report_id: str
    project_id: str
    created_count: int = Field(ge=0)
    linked_count: int = Field(ge=0)
    skipped_count: int = Field(ge=0)
    created_issue_ids: list[str] = Field(default_factory=list)
    linked_issue_ids: list[str] = Field(default_factory=list)
    skipped_line_ids: list[str] = Field(default_factory=list)


@dataclass(frozen=True)
class _MaterializableRow:
    line_id: str
    description: str | None
    location: str | None
    trade: str | None
    group_key: str | None
    group_label_he: str | None
    standard_ref: str | None
    catalog_issue_id: str | None
    row_severity: str | None
    photo_ids: list[str]
    linked_issue_id: str | None = None


class QualityIssueMaterializationService:
    def __init__(
        self,
        report_repository: FieldVisitReportRepository | None = None,
        line_repository: FieldVisitReportLineRepository | None = None,
        line_photo_repository: FieldVisitReportLinePhotoRepository | None = None,
        issue_repository: QualityIssueRepository | None = None,
        event_repository: QualityIssueEventRepository | None = None,
        catalog_service: FieldReportCatalogService | None = None,
    ) -> None:
        self.report_repository = (
            report_repository or FieldVisitReportRepository()
        )
        self.line_repository = (
            line_repository or FieldVisitReportLineRepository()
        )
        self.line_photo_repository = (
            line_photo_repository or FieldVisitReportLinePhotoRepository()
        )
        self.issue_repository = (
            issue_repository or QualityIssueRepository()
        )
        self.event_repository = (
            event_repository or QualityIssueEventRepository()
        )
        self.catalog_service = (
            catalog_service or FieldReportCatalogService()
        )

    def materialize_issues_from_report(
        self,
        *,
        organization_id: str,
        report_id: str,
        actor_id: str | None = None,
    ) -> MaterializationResult:
        """
        Create quality issues from qualifying finding rows on a closed report.

        Idempotent per ``materialization_key`` ({report_id}:{line_id}).
        """
        record = self._get_closed_report(
            organization_id=organization_id,
            report_id=report_id,
        )
        project_id = str(record["project_id"])
        seen_at = _resolve_first_seen_at(record)
        lines = self._load_report_lines(report_id)
        rows = collect_materializable_finding_rows(
            header_fields=record.get("header_fields") or {},
            lines=lines,
        )

        created_issue_ids: list[str] = []
        linked_issue_ids: list[str] = []
        skipped_line_ids: list[str] = []

        for row in rows:
            if row.linked_issue_id:
                linked = self._link_existing_issue(
                    organization_id=organization_id,
                    project_id=project_id,
                    report_id=report_id,
                    row=row,
                    seen_at=seen_at,
                    actor_id=actor_id,
                )
                if linked is not None:
                    linked_issue_ids.append(linked)
                else:
                    skipped_line_ids.append(row.line_id)
                continue

            materialization_key = build_materialization_key(
                report_id,
                row.line_id,
            )
            existing = self.issue_repository.get_by_materialization_key(
                organization_id=organization_id,
                materialization_key=materialization_key,
            )
            if existing is not None:
                skipped_line_ids.append(row.line_id)
                continue

            catalog_issue = (
                self.catalog_service.find_issue(row.catalog_issue_id)
                if row.catalog_issue_id
                else None
            )
            catalog_issue_name = (
                catalog_issue.get("issue_name_he") if catalog_issue else None
            )
            catalog_severity = (
                catalog_issue.get("severity") if catalog_issue else None
            )
            standard_ref = row.standard_ref or (
                catalog_issue.get("standard_ref")
                or catalog_issue.get("category_standard_id")
                if catalog_issue
                else None
            )
            trade = row.trade or (
                catalog_issue.get("trade") if catalog_issue else None
            )
            description = row.description or (
                catalog_issue.get("description") if catalog_issue else None
            )

            request = QualityIssueCreateRequest(
                title=derive_issue_title(
                    description=description,
                    location=row.location,
                    trade=trade,
                    catalog_issue_name=catalog_issue_name,
                ),
                description=description,
                location=row.location,
                trade=trade,
                group_key=row.group_key,
                group_label_he=row.group_label_he,
                standard_ref=standard_ref,
                severity=resolve_issue_severity(
                    catalog_severity=catalog_severity,
                    row_severity=row.row_severity,
                ),
                catalog_issue_id=row.catalog_issue_id,
                first_seen_report_id=report_id,
                first_seen_line_id=row.line_id,
                first_seen_at=seen_at,
                last_seen_report_id=report_id,
                last_seen_line_id=row.line_id,
                last_seen_at=seen_at,
                photo_ids=row.photo_ids,
                materialization_key=materialization_key,
            )

            issue = self.issue_repository.create(
                organization_id=organization_id,
                project_id=project_id,
                request=request,
                status=QualityIssueStatus.OPEN.value,
            )
            self._append_detected_event(
                issue=issue,
                actor_id=actor_id,
            )
            created_issue_ids.append(str(issue["id"]))

        return MaterializationResult(
            report_id=report_id,
            project_id=project_id,
            created_count=len(created_issue_ids),
            linked_count=len(linked_issue_ids),
            skipped_count=len(skipped_line_ids),
            created_issue_ids=created_issue_ids,
            linked_issue_ids=linked_issue_ids,
            skipped_line_ids=skipped_line_ids,
        )

    def _link_existing_issue(
        self,
        *,
        organization_id: str,
        project_id: str,
        report_id: str,
        row: _MaterializableRow,
        seen_at: datetime,
        actor_id: str | None,
    ) -> str | None:
        issue_id = str(row.linked_issue_id or "").strip()
        if not issue_id:
            return None

        issue = self.issue_repository.get_for_organization(
            issue_id=issue_id,
            organization_id=organization_id,
        )
        if issue is None or str(issue.get("project_id")) != project_id:
            return None

        if self._has_linked_event(
            report_id=report_id,
            line_id=row.line_id,
            issue_id=issue_id,
        ):
            return issue_id

        previous_last_seen_at = issue.get("last_seen_at")
        merged_photos = list(dict.fromkeys(
            [*list(issue.get("photo_ids") or []), *row.photo_ids]
        ))
        self.issue_repository.update(
            issue_id,
            {
                "last_seen_report_id": report_id,
                "last_seen_line_id": row.line_id,
                "last_seen_at": seen_at.isoformat(),
                "photo_ids": merged_photos,
            },
        )

        match_key = build_match_key(
            location=row.location,
            trade=row.trade,
            group_key=row.group_key,
        )
        payload = validate_event_fields(
            event_type=QualityIssueEventType.LINKED,
            report_id=report_id,
            actor_id=actor_id,
            payload={
                "match_key": match_key,
                "match_source": "manual",
                "previous_last_seen_at": (
                    str(previous_last_seen_at)
                    if previous_last_seen_at
                    else None
                ),
            },
        )
        self.event_repository.create(
            issue_id=issue_id,
            event_type=QualityIssueEventType.LINKED.value,
            report_id=report_id,
            line_id=row.line_id,
            actor_id=actor_id,
            payload=payload,
        )
        return issue_id

    def _has_linked_event(
        self,
        *,
        report_id: str,
        line_id: str,
        issue_id: str,
    ) -> bool:
        for event in self.event_repository.list_by_report_id(report_id):
            if (
                str(event.get("issue_id")) == issue_id
                and str(event.get("line_id") or "") == line_id
                and event.get("event_type") == QualityIssueEventType.LINKED.value
            ):
                return True
        return False

    def _get_closed_report(
        self,
        *,
        organization_id: str,
        report_id: str,
    ) -> dict:
        record = self.report_repository.get_by_id(report_id)
        if (
            record is None
            or str(record.get("organization_id")) != organization_id
        ):
            raise NotFoundError(
                message="Field visit report not found",
                resource_type="field_visit_report",
                resource_id=report_id,
            )

        status = str(record.get("status") or "")
        if status != CLOSED_REPORT_STATUS:
            raise ValidationError(
                message="Issues can only be materialized from closed reports",
                details={"report_id": report_id, "status": status},
            )

        return record

    def _load_report_lines(self, report_id: str) -> list[dict]:
        if not self.line_repository.is_storage_available():
            return []

        serialized: list[dict] = []
        for line in self.line_repository.list_by_report(report_id):
            line_id = str(line["id"])
            photo_ids = self._photo_ids_for_line(line)
            serialized.append(
                {
                    "id": line_id,
                    "location": line.get("location"),
                    "trade": line.get("trade"),
                    "description": line.get("description"),
                    "notes": line.get("notes"),
                    "severity": line.get("severity"),
                    "standard_ref": line.get("standard_ref"),
                    "issue_id": line.get("issue_id"),
                    "group_key": line.get("group_key"),
                    "group_label_he": line.get("group_label_he"),
                    "linked_issue_id": line.get("linked_issue_id"),
                    "photo_ids": photo_ids,
                    "has_photo": bool(photo_ids),
                }
            )
        return serialized

    def _photo_ids_for_line(self, line: dict) -> list[str]:
        line_id = str(line["id"])
        if self.line_photo_repository.is_storage_available():
            photos = self.line_photo_repository.list_by_line(line_id)
            return [str(photo["id"]) for photo in photos]

        if line.get("photo_storage_path"):
            return [LEGACY_LINE_PHOTO_ID]
        return []

    def _append_detected_event(
        self,
        *,
        issue: dict,
        actor_id: str | None,
    ) -> None:
        payload = validate_event_fields(
            event_type=QualityIssueEventType.DETECTED,
            report_id=str(issue.get("first_seen_report_id") or ""),
            actor_id=actor_id,
            payload={
                "materialization_key": issue.get("materialization_key"),
                "severity": issue.get("severity"),
                "title": issue.get("title"),
                "catalog_issue_id": issue.get("catalog_issue_id"),
                "location": issue.get("location"),
                "trade": issue.get("trade"),
                "group_key": issue.get("group_key"),
            },
        )
        self.event_repository.create(
            issue_id=str(issue["id"]),
            event_type=QualityIssueEventType.DETECTED.value,
            report_id=str(issue.get("first_seen_report_id") or ""),
            line_id=issue.get("first_seen_line_id"),
            actor_id=actor_id,
            payload=payload,
        )


def collect_materializable_finding_rows(
    *,
    header_fields: dict[str, Any],
    lines: list[dict],
) -> list[_MaterializableRow]:
    """
    Merge findings_table block rows with normalized report lines.

    Lines from ``field_visit_report_lines`` take precedence when the same
    ``line_id`` appears in both sources (photos, catalog fields).
    """
    rows_by_id: dict[str, _MaterializableRow] = {}

    for block_row in extract_finding_rows_from_blocks(header_fields):
        rows_by_id[block_row.line_id] = block_row

    for line_row in materializable_rows_from_lines(lines):
        existing = rows_by_id.get(line_row.line_id)
        if existing is None:
            rows_by_id[line_row.line_id] = line_row
            continue

        rows_by_id[line_row.line_id] = _MaterializableRow(
            line_id=line_row.line_id,
            description=line_row.description or existing.description,
            location=line_row.location or existing.location,
            trade=line_row.trade or existing.trade,
            group_key=line_row.group_key or existing.group_key,
            group_label_he=line_row.group_label_he or existing.group_label_he,
            standard_ref=line_row.standard_ref or existing.standard_ref,
            catalog_issue_id=line_row.catalog_issue_id or existing.catalog_issue_id,
            row_severity=line_row.row_severity or existing.row_severity,
            photo_ids=line_row.photo_ids or existing.photo_ids,
            linked_issue_id=(
                line_row.linked_issue_id or existing.linked_issue_id
            ),
        )

    return list(rows_by_id.values())


def extract_finding_rows_from_blocks(
    header_fields: dict[str, Any],
) -> list[_MaterializableRow]:
    blocks = header_fields.get("blocks")
    if not isinstance(blocks, list):
        return []

    rows: list[_MaterializableRow] = []
    for block in blocks:
        if not isinstance(block, dict):
            continue
        if block.get("kind") != "findings_table":
            continue

        raw_rows = block.get("rows")
        if not isinstance(raw_rows, list):
            continue

        for index, raw_row in enumerate(raw_rows):
            if not isinstance(raw_row, dict):
                continue

            try:
                finding = FindingRow.model_validate(
                    _normalize_block_row(raw_row, index)
                )
            except Exception:
                continue

            materializable = _materializable_row_from_finding(finding)
            if materializable is not None:
                rows.append(materializable)

    return rows


def materializable_rows_from_lines(
    lines: list[dict],
) -> list[_MaterializableRow]:
    rows: list[_MaterializableRow] = []
    for index, line in enumerate(lines):
        if not isinstance(line, dict):
            continue

        try:
            finding = FindingRow.model_validate(
                _normalize_line_row(line, index)
            )
        except Exception:
            continue

        materializable = _materializable_row_from_finding(finding)
        if materializable is not None:
            rows.append(materializable)

    return rows


def _materializable_row_from_finding(
    finding: FindingRow,
) -> _MaterializableRow | None:
    photo_ids = list(finding.photo_ids or [])
    catalog_issue_id = _normalize_catalog_issue_id(finding.issue_id)

    if not finding_row_qualifies_for_materialization(
        description=finding.description,
        catalog_issue_id=catalog_issue_id,
        photo_ids=photo_ids,
    ):
        return None

    return _MaterializableRow(
        line_id=str(finding.id),
        description=finding.description,
        location=finding.location,
        trade=finding.trade,
        group_key=finding.group_key,
        group_label_he=finding.group_label_he,
        standard_ref=finding.standard_ref,
        catalog_issue_id=catalog_issue_id,
        row_severity=finding.severity,
        photo_ids=photo_ids,
        linked_issue_id=finding.linked_issue_id,
    )


def _normalize_block_row(raw_row: dict[str, Any], index: int) -> dict[str, Any]:
    normalized = dict(raw_row)
    if not normalized.get("id"):
        normalized["id"] = f"block-row-{index}"
    return normalized


def _normalize_line_row(line: dict[str, Any], index: int) -> dict[str, Any]:
    photo_ids = line.get("photo_ids")
    if photo_ids is None and line.get("has_photo"):
        photo_ids = []

    return {
        "id": line.get("id") or f"line-{index}",
        "location": line.get("location"),
        "trade": line.get("trade"),
        "status": line.get("status"),
        "description": line.get("description"),
        "notes": line.get("notes"),
        "severity": line.get("severity"),
        "standard_ref": line.get("standard_ref"),
        "issue_id": line.get("issue_id"),
        "group_key": line.get("group_key"),
        "group_label_he": line.get("group_label_he"),
        "linked_issue_id": line.get("linked_issue_id"),
        "photo_ids": photo_ids,
        "has_photo": bool(line.get("has_photo")),
    }


def _normalize_catalog_issue_id(value: str | None) -> str | None:
    if not value or not str(value).strip():
        return None
    return str(value).strip().upper()


def _resolve_first_seen_at(record: dict[str, Any]) -> datetime:
    for candidate in (record.get("closed_at"), record.get("visit_date")):
        parsed = _parse_timestamp(candidate)
        if parsed is not None:
            return parsed
    return datetime.now(UTC)


def _parse_timestamp(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value

    text = str(value).strip()
    if not text:
        return None

    normalized = text.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None

    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed
