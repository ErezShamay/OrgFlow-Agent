"""Recurring issue and subcontractor rankings - roadmap 6.2."""

from __future__ import annotations

from typing import Any

from app.schemas.quality_issue import (
    QualityContractorRecurringRankEntry,
    QualityIssueSeverity,
    QualityRecurringIssueRankEntry,
)

UNKNOWN_CONTRACTOR_LABEL = "ללא קבלן"
DEFAULT_RECURRING_RANKING_LIMIT = 10

_SEVERITY_RANK: dict[QualityIssueSeverity, int] = {
    QualityIssueSeverity.CRITICAL: 4,
    QualityIssueSeverity.HIGH: 3,
    QualityIssueSeverity.MEDIUM: 2,
    QualityIssueSeverity.LOW: 1,
}


def is_recurring_issue(issue: dict[str, Any]) -> bool:
    return int(issue.get("recurrence_count") or 0) > 0


def normalize_contractor_name(contractor_name: str | None) -> str:
    normalized = (contractor_name or "").strip()
    return normalized or UNKNOWN_CONTRACTOR_LABEL


def _severity_rank(severity_raw: str | None) -> int:
    try:
        severity = QualityIssueSeverity(str(severity_raw or ""))
    except ValueError:
        return 0
    return _SEVERITY_RANK.get(severity, 0)


def _project_lookup(projects: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    lookup: dict[str, dict[str, Any]] = {}
    for project in projects:
        project_id = str(project.get("id") or "")
        if project_id:
            lookup[project_id] = project
    return lookup


def build_recurring_issue_rankings(
    issues: list[dict[str, Any]],
    *,
    projects: list[dict[str, Any]],
    limit: int = DEFAULT_RECURRING_RANKING_LIMIT,
) -> list[QualityRecurringIssueRankEntry]:
    """Rank issues with recurrence_count > 0 by recurrence pressure."""
    projects_by_id = _project_lookup(projects)
    recurring = [issue for issue in issues if is_recurring_issue(issue)]

    recurring.sort(
        key=lambda issue: (
            int(issue.get("recurrence_count") or 0),
            _severity_rank(issue.get("severity")),
            str(issue.get("title") or "").casefold(),
        ),
        reverse=True,
    )

    entries: list[QualityRecurringIssueRankEntry] = []
    for issue in recurring[: max(limit, 0)]:
        project_id = str(issue.get("project_id") or "")
        project = projects_by_id.get(project_id, {})
        recurrence_count = int(issue.get("recurrence_count") or 0)
        if recurrence_count < 1:
            continue

        entries.append(
            QualityRecurringIssueRankEntry(
                issue_id=str(issue.get("id") or ""),
                title=str(issue.get("title") or ""),
                trade=issue.get("trade"),
                location=issue.get("location"),
                recurrence_count=recurrence_count,
                project_id=project_id,
                project_name=project.get("project_name"),
                contractor_name=normalize_contractor_name(
                    project.get("contractor_name")
                ),
                status=issue.get("status"),
                severity=issue.get("severity"),
            )
        )

    return entries


def build_contractor_recurring_rankings(
    issues: list[dict[str, Any]],
    *,
    projects: list[dict[str, Any]],
    limit: int = DEFAULT_RECURRING_RANKING_LIMIT,
) -> list[QualityContractorRecurringRankEntry]:
    """Rank subcontractors by recurring issue count and total recurrence events."""
    projects_by_id = _project_lookup(projects)
    per_contractor: dict[str, dict[str, Any]] = {}

    for issue in issues:
        if not is_recurring_issue(issue):
            continue

        project_id = str(issue.get("project_id") or "")
        project = projects_by_id.get(project_id, {})
        contractor = normalize_contractor_name(project.get("contractor_name"))
        bucket = per_contractor.setdefault(
            contractor,
            {
                "recurring_issue_count": 0,
                "total_recurrence_count": 0,
                "project_ids": set(),
            },
        )
        bucket["recurring_issue_count"] += 1
        bucket["total_recurrence_count"] += int(
            issue.get("recurrence_count") or 0
        )
        if project_id:
            bucket["project_ids"].add(project_id)

    entries = [
        QualityContractorRecurringRankEntry(
            contractor_name=contractor,
            recurring_issue_count=bucket["recurring_issue_count"],
            total_recurrence_count=bucket["total_recurrence_count"],
            project_count=len(bucket["project_ids"]),
        )
        for contractor, bucket in per_contractor.items()
    ]

    entries.sort(
        key=lambda entry: (
            entry.recurring_issue_count,
            entry.total_recurrence_count,
            entry.contractor_name.casefold(),
        ),
        reverse=True,
    )

    if limit <= 0:
        return entries
    return entries[:limit]
