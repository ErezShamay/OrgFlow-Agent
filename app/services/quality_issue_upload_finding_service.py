from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel

from app.repositories.project_repository import ProjectRepository
from app.repositories.quality_issue_repository import (
    QualityIssueEventRepository,
    QualityIssueRepository,
)
from app.schemas.quality_issue import (
    QualityIssueCreateRequest,
    QualityIssueEventType,
    QualityIssueStatus,
    build_upload_finding_materialization_key,
    derive_issue_title,
    resolve_issue_severity,
    validate_event_fields,
)

_UPLOAD_FINDING_TYPE_LABELS_HE: dict[str, str] = {
    "SAFETY": "בטיחות",
    "QUALITY": "איכות",
    "DELAY": "לוח זמנים",
    "BUDGET": "תקציב",
    "GENERAL": "כללי",
}


class UploadFindingMaterializationResult(BaseModel):
    finding_id: str
    issue_id: str | None = None
    created: bool = False
    skipped: bool = False
    materialization_key: str = ""


class QualityIssueUploadFindingService:
    """Bridge legacy AI upload ``findings`` rows into ``quality_issues`` (5.7)."""

    def __init__(
        self,
        issue_repository: QualityIssueRepository | None = None,
        event_repository: QualityIssueEventRepository | None = None,
        project_repository: ProjectRepository | None = None,
    ) -> None:
        self.issue_repository = issue_repository or QualityIssueRepository()
        self.event_repository = event_repository or QualityIssueEventRepository()
        self.project_repository = project_repository or ProjectRepository()

    def materialize_from_upload_finding(
        self,
        *,
        project_id: str,
        report_id: str,
        finding: dict[str, Any],
        organization_id: str | None = None,
        actor_id: str | None = None,
    ) -> UploadFindingMaterializationResult | None:
        finding_id = str(finding.get("id") or "").strip()
        if not finding_id:
            return None

        org_id = (organization_id or "").strip() or self._resolve_organization_id(
            project_id
        )
        if not org_id:
            return None

        summary = str(finding.get("summary") or "").strip()
        title = str(finding.get("title") or "").strip()
        if not summary and not title:
            return None

        materialization_key = build_upload_finding_materialization_key(
            report_id,
            finding_id,
        )
        existing = self.issue_repository.get_by_materialization_key(
            organization_id=org_id,
            materialization_key=materialization_key,
        )
        if existing is not None:
            return UploadFindingMaterializationResult(
                finding_id=finding_id,
                issue_id=str(existing["id"]),
                skipped=True,
                materialization_key=materialization_key,
            )

        seen_at = _parse_timestamp(finding.get("created_at")) or datetime.now(UTC)
        finding_type = str(finding.get("finding_type") or "").strip().upper() or None
        trade = _upload_finding_type_to_trade(finding_type)
        group_label = (
            _UPLOAD_FINDING_TYPE_LABELS_HE.get(finding_type or "", finding_type)
            if finding_type
            else None
        )

        request = QualityIssueCreateRequest(
            title=derive_issue_title(
                description=summary or title,
                trade=trade,
            ),
            description=summary or title or None,
            trade=trade,
            group_key=finding_type.lower() if finding_type else None,
            group_label_he=group_label,
            severity=resolve_issue_severity(
                row_severity=str(finding.get("severity") or "").strip() or None,
            ),
            first_seen_report_id=report_id,
            first_seen_line_id=finding_id,
            first_seen_at=seen_at,
            last_seen_report_id=report_id,
            last_seen_line_id=finding_id,
            last_seen_at=seen_at,
            materialization_key=materialization_key,
        )

        issue = self.issue_repository.create(
            organization_id=org_id,
            project_id=project_id,
            request=request,
            status=QualityIssueStatus.OPEN.value,
        )
        self._append_detected_event(
            issue=issue,
            finding_id=finding_id,
            finding_type=finding_type,
            actor_id=actor_id,
        )

        return UploadFindingMaterializationResult(
            finding_id=finding_id,
            issue_id=str(issue["id"]),
            created=True,
            materialization_key=materialization_key,
        )

    def _resolve_organization_id(self, project_id: str) -> str | None:
        project = self.project_repository.get_project_by_id(project_id)
        if not project:
            return None
        org_id = project.get("organization_id")
        return str(org_id).strip() if org_id else None

    def _append_detected_event(
        self,
        *,
        issue: dict[str, Any],
        finding_id: str,
        finding_type: str | None,
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
                "source": "ai_upload",
                "finding_id": finding_id,
                "finding_type": finding_type,
            },
        )
        self.event_repository.create(
            issue_id=str(issue["id"]),
            event_type=QualityIssueEventType.DETECTED.value,
            report_id=str(issue.get("first_seen_report_id") or ""),
            line_id=finding_id,
            actor_id=actor_id,
            payload=payload,
        )


def _upload_finding_type_to_trade(finding_type: str | None) -> str | None:
    if not finding_type:
        return None
    return _UPLOAD_FINDING_TYPE_LABELS_HE.get(finding_type, finding_type)


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
