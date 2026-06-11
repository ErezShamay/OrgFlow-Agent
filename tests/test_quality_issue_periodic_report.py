"""Roadmap 6.3 - periodic QC report."""

from __future__ import annotations

from datetime import UTC, datetime

from app.schemas.quality_issue import QualityIssueUpdateRequest
from app.services.quality_issue_periodic_report_service import (
    build_periodic_report_response,
    issue_in_period,
    render_periodic_report_csv,
    resolve_period_bounds,
)
from app.services.quality_issue_service import QualityIssueService
from tests.quality_issues_test_support import (
    FakeProjectRepository,
    InMemoryQualityIssueEventRepository,
    InMemoryQualityIssueRepository,
    qc_create_request,
    qc_now,
)


def test_issue_in_period_uses_last_seen_at() -> None:
    period_start, period_end = resolve_period_bounds(
        period_days=30,
        now=datetime(2026, 6, 10, 12, 0, tzinfo=UTC),
    )
    assert issue_in_period(
        {"last_seen_at": "2026-06-05T10:00:00+00:00"},
        period_start=period_start,
        period_end=period_end,
    )
    assert not issue_in_period(
        {"last_seen_at": "2026-05-01T10:00:00+00:00"},
        period_start=period_start,
        period_end=period_end,
    )


def test_build_periodic_report_response_groups_projects_and_issues() -> None:
    projects = [
        {
            "id": "proj-1",
            "project_name": "א",
            "contractor_name": "קבלנות כהן",
        }
    ]
    issues = [
        {
            "id": "issue-1",
            "project_id": "proj-1",
            "title": "פתוח",
            "status": "OPEN",
            "severity": "CRITICAL",
            "trade": "אינסטלציה",
            "recurrence_count": 0,
            "first_seen_at": "2026-06-05T10:00:00+00:00",
            "last_seen_at": "2026-06-05T10:00:00+00:00",
        },
        {
            "id": "issue-2",
            "project_id": "proj-1",
            "title": "ישן",
            "status": "CLOSED",
            "severity": "LOW",
            "recurrence_count": 0,
            "first_seen_at": "2026-01-01T10:00:00+00:00",
            "last_seen_at": "2026-01-01T10:00:00+00:00",
        },
    ]

    report = build_periodic_report_response(
        organization_id="org-1",
        issues=issues,
        projects=projects,
        period_days=30,
        now=datetime(2026, 6, 10, 12, 0, tzinfo=UTC),
    )

    assert report.summary.total_issues == 1
    assert report.summary.open_total == 1
    assert report.projects[0].open_critical == 1
    assert report.issues[0].issue_id == "issue-1"


def test_render_periodic_report_csv_includes_hebrew_header() -> None:
    report = build_periodic_report_response(
        organization_id="org-1",
        issues=[
            {
                "id": "issue-1",
                "project_id": "proj-1",
                "title": "נזילה",
                "status": "OPEN",
                "severity": "HIGH",
                "trade": "אינסטלציה",
                "standard_ref": 'ת"י 1205',
                "recurrence_count": 0,
                "first_seen_at": "2026-06-05T10:00:00+00:00",
                "last_seen_at": "2026-06-05T10:00:00+00:00",
            }
        ],
        projects=[
            {
                "id": "proj-1",
                "project_name": "א",
                "contractor_name": "קבלן",
            }
        ],
        period_days=30,
        now=datetime(2026, 6, 10, 12, 0, tzinfo=UTC),
    )

    csv_content = render_periodic_report_csv(report)
    assert csv_content.startswith("\ufeff")
    assert "דוח תקופתי" in csv_content
    assert "נזילה" in csv_content


def test_service_portfolio_periodic_report_filters_project() -> None:
    service = QualityIssueService(
        issue_repository=InMemoryQualityIssueRepository(),
        event_repository=InMemoryQualityIssueEventRepository(),
        project_repository=FakeProjectRepository(),
    )

    service.create_issue(
        organization_id="org-1",
        project_id="proj-1",
        request=qc_create_request(
            title="א",
            materialization_key="periodic-1",
            first_seen_at=qc_now(),
        ),
        actor_role="SUPERVISOR",
    )
    service.create_issue(
        organization_id="org-1",
        project_id="proj-2",
        request=qc_create_request(
            title="ב",
            materialization_key="periodic-2",
            first_seen_at=qc_now(),
        ),
        actor_role="SUPERVISOR",
    )

    org_report = service.get_portfolio_periodic_report(
        organization_id="org-1",
        actor_role="DEVELOPER",
    )
    assert org_report.summary.total_issues == 2

    project_report = service.get_portfolio_periodic_report(
        organization_id="org-1",
        actor_role="DEVELOPER",
        project_id="proj-2",
    )
    assert project_report.project_id == "proj-2"
    assert project_report.summary.total_issues == 1
