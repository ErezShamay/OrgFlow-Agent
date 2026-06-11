from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.repositories.quality_issue_repository import QualityIssueRepository
from app.schemas.quality_issue import (
    FindingMatchInput,
    QualityIssue,
    QualityIssueMatchCandidate,
    QualityIssueSeverity,
    build_match_key,
    parse_quality_issue_row,
)

DEFAULT_MATCH_LIMIT = 5
EXACT_MATCH_SCORE = 1.0


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


def match_key_for_finding(finding: FindingMatchInput) -> str:
    return build_match_key(
        location=finding.location,
        trade=finding.trade,
        group_key=finding.group_key,
    )


def match_key_for_issue(issue: QualityIssue | dict[str, Any]) -> str:
    if isinstance(issue, QualityIssue):
        return build_match_key(
            location=issue.location,
            trade=issue.trade,
            group_key=issue.group_key,
        )
    return build_match_key(
        location=issue.get("location"),
        trade=issue.get("trade"),
        group_key=issue.get("group_key"),
    )


def _catalog_id(value: str | None) -> str:
    return str(value).strip().lower() if value and str(value).strip() else ""


def _candidate_sort_key(
    candidate: QualityIssueMatchCandidate,
    *,
    finding_catalog_issue_id: str | None,
) -> tuple[int, int, float, str]:
    issue = candidate.issue
    severity_rank = issue.severity.rank
    finding_catalog = _catalog_id(finding_catalog_issue_id)
    issue_catalog = _catalog_id(issue.catalog_issue_id)
    catalog_boost = int(
        bool(finding_catalog) and finding_catalog == issue_catalog
    )
    last_seen = _parse_timestamp(issue.last_seen_at)
    last_seen_epoch = last_seen.timestamp() if last_seen else 0.0
    return (
        -severity_rank,
        -catalog_boost,
        -last_seen_epoch,
        issue.title,
    )


def rank_match_candidates(
    candidates: list[QualityIssueMatchCandidate],
    *,
    finding_catalog_issue_id: str | None = None,
) -> list[QualityIssueMatchCandidate]:
    return sorted(
        candidates,
        key=lambda candidate: _candidate_sort_key(
            candidate,
            finding_catalog_issue_id=finding_catalog_issue_id,
        ),
    )


class QualityIssueMatchingService:
    """Match finding rows to open registry issues by location + trade + group_key."""

    def __init__(
        self,
        issue_repository: QualityIssueRepository | None = None,
    ) -> None:
        self.issue_repository = issue_repository or QualityIssueRepository()

    def find_matches(
        self,
        *,
        finding: FindingMatchInput,
        open_issues: list[QualityIssue] | list[dict[str, Any]],
        limit: int = DEFAULT_MATCH_LIMIT,
    ) -> list[QualityIssueMatchCandidate]:
        target_key = match_key_for_finding(finding)
        candidates: list[QualityIssueMatchCandidate] = []

        for raw_issue in open_issues:
            issue = (
                raw_issue
                if isinstance(raw_issue, QualityIssue)
                else parse_quality_issue_row(raw_issue)
            )
            issue_key = match_key_for_issue(issue)
            if issue_key != target_key:
                continue
            candidates.append(
                QualityIssueMatchCandidate(
                    issue=issue,
                    match_key=issue_key,
                    score=EXACT_MATCH_SCORE,
                )
            )

        ranked = rank_match_candidates(
            candidates,
            finding_catalog_issue_id=finding.catalog_issue_id,
        )
        return ranked[: max(limit, 0)]

    def find_matches_for_project(
        self,
        *,
        organization_id: str,
        project_id: str,
        finding: FindingMatchInput,
        limit: int = DEFAULT_MATCH_LIMIT,
    ) -> list[QualityIssueMatchCandidate]:
        rows = self.issue_repository.list_open_by_project(
            organization_id=organization_id,
            project_id=project_id,
        )
        return self.find_matches(
            finding=finding,
            open_issues=rows,
            limit=limit,
        )
