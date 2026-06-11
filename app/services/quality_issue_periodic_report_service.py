"""Periodic QC portfolio report - roadmap 6.3."""

from __future__ import annotations

import csv
import io
from datetime import UTC, datetime, timedelta
from typing import Any

from app.schemas.quality_issue import (
    QualityIssueSeverity,
    QualityPeriodicReportIssueRow,
    QualityPeriodicReportProjectRow,
    QualityPeriodicReportResponse,
    QualityPeriodicReportSummary,
)

DEFAULT_PERIOD_DAYS = 30


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


def _project_lookup(projects: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    lookup: dict[str, dict[str, Any]] = {}
    for project in projects:
        project_id = str(project.get("id") or "")
        if project_id:
            lookup[project_id] = project
    return lookup


def resolve_period_bounds(
    *,
    period_days: int = DEFAULT_PERIOD_DAYS,
    now: datetime | None = None,
) -> tuple[datetime, datetime]:
    current = now or datetime.now(UTC)
    start = current - timedelta(days=max(1, period_days))
    return start, current


def issue_in_period(
    issue: dict[str, Any],
    *,
    period_start: datetime,
    period_end: datetime,
) -> bool:
    for field in ("last_seen_at", "first_seen_at", "updated_at", "created_at"):
        parsed = _parse_timestamp(issue.get(field))
        if parsed is not None and period_start <= parsed <= period_end:
            return True
    return False


def build_periodic_report_summary(
    issues: list[dict[str, Any]],
) -> QualityPeriodicReportSummary:
    open_statuses = {
        "OPEN",
        "IN_REMEDIATION",
        "PENDING_VERIFICATION",
        "REOPENED",
    }
    open_issues = [
        issue for issue in issues if issue.get("status") in open_statuses
    ]
    closed_issues = [
        issue for issue in issues if issue.get("status") == "CLOSED"
    ]
    recurring_issues = [
        issue for issue in issues if int(issue.get("recurrence_count") or 0) > 0
    ]

    return QualityPeriodicReportSummary(
        total_issues=len(issues),
        open_total=len(open_issues),
        open_critical=sum(
            1
            for issue in open_issues
            if issue.get("severity") == QualityIssueSeverity.CRITICAL.value
        ),
        closed_total=len(closed_issues),
        recurring_total=len(recurring_issues),
    )


def build_periodic_report_project_rows(
    issues: list[dict[str, Any]],
    *,
    projects: list[dict[str, Any]],
) -> list[QualityPeriodicReportProjectRow]:
    projects_by_id = _project_lookup(projects)
    per_project: dict[str, dict[str, int]] = {}

    for issue in issues:
        project_id = str(issue.get("project_id") or "")
        if not project_id:
            continue

        bucket = per_project.setdefault(
            project_id,
            {
                "issue_total": 0,
                "open_total": 0,
                "open_critical": 0,
                "recurring_total": 0,
            },
        )
        bucket["issue_total"] += 1

        status = str(issue.get("status") or "")
        if status in {
            "OPEN",
            "IN_REMEDIATION",
            "PENDING_VERIFICATION",
            "REOPENED",
        }:
            bucket["open_total"] += 1
            if issue.get("severity") == QualityIssueSeverity.CRITICAL.value:
                bucket["open_critical"] += 1

        if int(issue.get("recurrence_count") or 0) > 0:
            bucket["recurring_total"] += 1

    rows: list[QualityPeriodicReportProjectRow] = []
    seen: set[str] = set()

    for project in projects:
        project_id = str(project.get("id") or "")
        if not project_id:
            continue
        seen.add(project_id)
        stats = per_project.get(
            project_id,
            {
                "issue_total": 0,
                "open_total": 0,
                "open_critical": 0,
                "recurring_total": 0,
            },
        )
        rows.append(
            QualityPeriodicReportProjectRow(
                project_id=project_id,
                project_name=project.get("project_name"),
                contractor_name=project.get("contractor_name"),
                issue_total=stats["issue_total"],
                open_total=stats["open_total"],
                open_critical=stats["open_critical"],
                recurring_total=stats["recurring_total"],
            )
        )

    for project_id, stats in per_project.items():
        if project_id in seen:
            continue
        rows.append(
            QualityPeriodicReportProjectRow(
                project_id=project_id,
                project_name=None,
                contractor_name=None,
                issue_total=stats["issue_total"],
                open_total=stats["open_total"],
                open_critical=stats["open_critical"],
                recurring_total=stats["recurring_total"],
            )
        )

    rows.sort(
        key=lambda row: (
            row.open_critical,
            row.open_total,
            row.recurring_total,
            (row.project_name or "").casefold(),
        ),
        reverse=True,
    )
    return rows


def build_periodic_report_issue_rows(
    issues: list[dict[str, Any]],
    *,
    projects: list[dict[str, Any]],
) -> list[QualityPeriodicReportIssueRow]:
    projects_by_id = _project_lookup(projects)
    rows: list[QualityPeriodicReportIssueRow] = []

    for issue in issues:
        project_id = str(issue.get("project_id") or "")
        project = projects_by_id.get(project_id, {})
        rows.append(
            QualityPeriodicReportIssueRow(
                issue_id=str(issue.get("id") or ""),
                title=str(issue.get("title") or ""),
                project_id=project_id,
                project_name=project.get("project_name"),
                contractor_name=project.get("contractor_name"),
                status=str(issue.get("status") or ""),
                severity=str(issue.get("severity") or ""),
                trade=issue.get("trade"),
                location=issue.get("location"),
                standard_ref=issue.get("standard_ref"),
                catalog_issue_id=issue.get("catalog_issue_id"),
                recurrence_count=int(issue.get("recurrence_count") or 0),
                first_seen_at=_parse_timestamp(issue.get("first_seen_at")),
                last_seen_at=_parse_timestamp(issue.get("last_seen_at")),
            )
        )

    rows.sort(
        key=lambda row: (
            row.open_rank(),
            row.severity_rank(),
            row.recurrence_count,
            row.title.casefold(),
        ),
        reverse=True,
    )
    return rows


def build_periodic_report_response(
    *,
    organization_id: str,
    issues: list[dict[str, Any]],
    projects: list[dict[str, Any]],
    period_days: int = DEFAULT_PERIOD_DAYS,
    project_id: str | None = None,
    now: datetime | None = None,
) -> QualityPeriodicReportResponse:
    period_start, period_end = resolve_period_bounds(
        period_days=period_days,
        now=now,
    )
    filtered = [
        issue
        for issue in issues
        if issue_in_period(
            issue,
            period_start=period_start,
            period_end=period_end,
        )
    ]

    return QualityPeriodicReportResponse(
        organization_id=organization_id,
        project_id=project_id,
        period_days=period_days,
        period_start=period_start,
        period_end=period_end,
        generated_at=period_end,
        summary=build_periodic_report_summary(filtered),
        projects=build_periodic_report_project_rows(
            filtered,
            projects=projects,
        ),
        issues=build_periodic_report_issue_rows(
            filtered,
            projects=projects,
        ),
    )


def render_periodic_report_csv(
    report: QualityPeriodicReportResponse,
) -> str:
    buffer = io.StringIO()
    buffer.write("\ufeff")
    writer = csv.writer(buffer)

    writer.writerow(["דוח תקופתי - בקרת איכות"])
    writer.writerow(
        [
            "תקופה",
            f"{report.period_start.date().isoformat()} - {report.period_end.date().isoformat()}",
        ]
    )
    writer.writerow(["סה״כ ליקויים", report.summary.total_issues])
    writer.writerow(["פתוחים", report.summary.open_total])
    writer.writerow(["קריטיים פתוחים", report.summary.open_critical])
    writer.writerow(["סגורים", report.summary.closed_total])
    writer.writerow(["חוזרים", report.summary.recurring_total])
    writer.writerow([])

    writer.writerow(
        [
            "פרויקט",
            "קבלן",
            "סה״כ ליקויים",
            "פתוחים",
            "קריטיים פתוחים",
            "חוזרים",
        ]
    )
    for project in report.projects:
        writer.writerow(
            [
                project.project_name or project.project_id,
                project.contractor_name or "",
                project.issue_total,
                project.open_total,
                project.open_critical,
                project.recurring_total,
            ]
        )

    writer.writerow([])
    writer.writerow(
        [
            "כותרת",
            "פרויקט",
            "קבלן",
            "סטטוס",
            "חומרה",
            "מלאכה",
            "מיקום",
            "סעיף מפרט",
            "קטלוג",
            "חזרות",
            "גילוי ראשון",
            "צפייה אחרונה",
        ]
    )
    for issue in report.issues:
        writer.writerow(
            [
                issue.title,
                issue.project_name or issue.project_id,
                issue.contractor_name or "",
                issue.status,
                issue.severity,
                issue.trade or "",
                issue.location or "",
                issue.standard_ref or "",
                issue.catalog_issue_id or "",
                issue.recurrence_count,
                issue.first_seen_at.isoformat() if issue.first_seen_at else "",
                issue.last_seen_at.isoformat() if issue.last_seen_at else "",
            ]
        )

    return buffer.getvalue()
