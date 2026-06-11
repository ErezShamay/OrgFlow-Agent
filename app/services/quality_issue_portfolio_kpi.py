"""Portfolio QC KPI helpers - roadmap 4.1."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.schemas.quality_issue import (
    QualityIssueSeverity,
    QualityPortfolioProjectSummary,
)

CRITICAL_STALE_DAYS_THRESHOLD = 14
CLOSED_WITHIN_DAYS_THRESHOLD = 30
AVERAGE_OPEN_DAYS_HEALTHY_THRESHOLD = 14


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


def days_open_for_issue(
    issue: dict[str, Any],
    *,
    now: datetime,
) -> int | None:
    first_seen_at = _parse_timestamp(issue.get("first_seen_at"))
    if first_seen_at is None:
        return None
    return max(0, int((now - first_seen_at).total_seconds() // 86400))


def is_critical_open_over_days(
    issue: dict[str, Any],
    *,
    threshold: int = CRITICAL_STALE_DAYS_THRESHOLD,
    now: datetime,
) -> bool:
    severity = str(issue.get("severity") or "")
    if severity != QualityIssueSeverity.CRITICAL.value:
        return False
    days_open = days_open_for_issue(issue, now=now)
    if days_open is None:
        return False
    return days_open > threshold


def count_critical_open_over_days(
    open_issues: list[dict[str, Any]],
    *,
    threshold: int = CRITICAL_STALE_DAYS_THRESHOLD,
    now: datetime,
) -> int:
    """KPI 4.1.2 - open CRITICAL issues open longer than threshold days."""
    return sum(
        1
        for issue in open_issues
        if is_critical_open_over_days(issue, threshold=threshold, now=now)
    )


def aggregate_critical_stale_by_project(
    open_issues: list[dict[str, Any]],
    *,
    threshold: int = CRITICAL_STALE_DAYS_THRESHOLD,
    now: datetime,
) -> dict[str, int]:
    per_project: dict[str, int] = {}

    for issue in open_issues:
        if not is_critical_open_over_days(issue, threshold=threshold, now=now):
            continue

        project_id = str(issue.get("project_id") or "")
        if not project_id:
            continue

        per_project[project_id] = per_project.get(project_id, 0) + 1

    return per_project


def days_to_close_for_issue(issue: dict[str, Any]) -> int | None:
    first_seen_at = _parse_timestamp(issue.get("first_seen_at"))
    closed_at = _parse_timestamp(issue.get("closed_at"))
    if first_seen_at is None or closed_at is None:
        return None
    return max(0, int((closed_at - first_seen_at).total_seconds() // 86400))


def is_closed_within_days(
    issue: dict[str, Any],
    *,
    threshold: int = CLOSED_WITHIN_DAYS_THRESHOLD,
) -> bool:
    days_to_close = days_to_close_for_issue(issue)
    if days_to_close is None:
        return False
    return days_to_close <= threshold


def count_closed_within_days(
    closed_issues: list[dict[str, Any]],
    *,
    threshold: int = CLOSED_WITHIN_DAYS_THRESHOLD,
) -> int:
    """Count closed issues resolved within threshold days of first detection."""
    return sum(
        1
        for issue in closed_issues
        if is_closed_within_days(issue, threshold=threshold)
    )


def compute_closed_within_days_percent(
    closed_issues: list[dict[str, Any]],
    *,
    threshold: int = CLOSED_WITHIN_DAYS_THRESHOLD,
) -> float | None:
    """KPI 4.1.3 - share of closed issues resolved within threshold days."""
    if not closed_issues:
        return None

    closed_within = count_closed_within_days(
        closed_issues,
        threshold=threshold,
    )
    return round(closed_within / len(closed_issues) * 100, 1)


def collect_open_days_for_issues(
    open_issues: list[dict[str, Any]],
    *,
    now: datetime,
) -> list[int]:
    open_days: list[int] = []
    for issue in open_issues:
        days_open = days_open_for_issue(issue, now=now)
        if days_open is None:
            continue
        open_days.append(days_open)
    return open_days


def compute_average_open_days(
    open_issues: list[dict[str, Any]],
    *,
    now: datetime,
) -> float | None:
    """KPI 4.1.4 - average days open across currently open issues."""
    open_days = collect_open_days_for_issues(open_issues, now=now)
    if not open_days:
        return None
    return round(sum(open_days) / len(open_days), 1)


def aggregate_average_open_days_by_project(
    open_issues: list[dict[str, Any]],
    *,
    now: datetime,
) -> dict[str, float]:
    per_project_days: dict[str, list[int]] = {}

    for issue in open_issues:
        project_id = str(issue.get("project_id") or "")
        if not project_id:
            continue

        days_open = days_open_for_issue(issue, now=now)
        if days_open is None:
            continue

        per_project_days.setdefault(project_id, []).append(days_open)

    return {
        project_id: round(sum(days) / len(days), 1)
        for project_id, days in per_project_days.items()
        if days
    }


def aggregate_open_issue_counts_by_project(
    open_issues: list[dict[str, Any]],
) -> dict[str, dict[str, int]]:
    """Count open / open-critical issues grouped by project_id."""
    per_project: dict[str, dict[str, int]] = {}

    for issue in open_issues:
        project_id = str(issue.get("project_id") or "")
        if not project_id:
            continue

        stats = per_project.setdefault(
            project_id,
            {"open_total": 0, "open_critical": 0},
        )
        stats["open_total"] += 1

        severity = str(issue.get("severity") or "")
        if severity == QualityIssueSeverity.CRITICAL.value:
            stats["open_critical"] += 1

    return per_project


def build_open_issues_per_project_summaries(
    *,
    projects: list[dict[str, Any]],
    open_counts_by_project: dict[str, dict[str, int]],
    critical_stale_by_project: dict[str, int] | None = None,
    average_open_days_by_project: dict[str, float] | None = None,
) -> list[QualityPortfolioProjectSummary]:
    """
    KPI 4.1.1 - open issues per project for every org project.

    Projects without open issues appear with zeros. Sorted by severity pressure
    (open_critical desc, open_total desc, project name).
    """
    stale_by_project = critical_stale_by_project or {}
    average_by_project = average_open_days_by_project or {}
    summaries: list[QualityPortfolioProjectSummary] = []
    seen_project_ids: set[str] = set()

    for project in projects:
        project_id = str(project.get("id") or "")
        if not project_id:
            continue

        seen_project_ids.add(project_id)
        stats = open_counts_by_project.get(
            project_id,
            {"open_total": 0, "open_critical": 0},
        )
        summaries.append(
            QualityPortfolioProjectSummary(
                project_id=project_id,
                project_name=project.get("project_name"),
                open_total=stats["open_total"],
                open_critical=stats["open_critical"],
                critical_open_over_14_days=stale_by_project.get(project_id, 0),
                average_open_days=average_by_project.get(project_id),
            )
        )

    for project_id, stats in open_counts_by_project.items():
        if project_id in seen_project_ids:
            continue
        summaries.append(
            QualityPortfolioProjectSummary(
                project_id=project_id,
                project_name=None,
                open_total=stats["open_total"],
                open_critical=stats["open_critical"],
                critical_open_over_14_days=stale_by_project.get(project_id, 0),
                average_open_days=average_by_project.get(project_id),
            )
        )

    return rank_portfolio_projects_by_qc_pressure(summaries)


def rank_portfolio_projects_by_qc_pressure(
    projects: list[QualityPortfolioProjectSummary],
) -> list[QualityPortfolioProjectSummary]:
    """KPI 4.1.5 - rank projects by open_critical then open_total."""
    return sorted(
        projects,
        key=lambda item: (
            item.open_critical,
            item.open_total,
            (item.project_name or "").casefold(),
        ),
        reverse=True,
    )


def count_projects_with_open_critical(
    projects: list[QualityPortfolioProjectSummary],
) -> int:
    return sum(1 for project in projects if project.open_critical > 0)


def count_projects_with_open_issues(
    projects: list[QualityPortfolioProjectSummary],
) -> int:
    return sum(1 for project in projects if project.open_total > 0)
