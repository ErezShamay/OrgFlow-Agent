"""Portfolio KPI 4.1.2 - critical open issues over 14 days."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from app.schemas.quality_issue import (
    QualityIssueSeverity,
    QualityIssueStatus,
    QualityIssueUpdateRequest,
)
from app.services.quality_issue_portfolio_kpi import (
    CRITICAL_STALE_DAYS_THRESHOLD,
    aggregate_critical_stale_by_project,
    build_open_issues_per_project_summaries,
    count_critical_open_over_days,
    days_open_for_issue,
    is_critical_open_over_days,
)
from app.services.quality_issue_service import QualityIssueService
from tests.quality_issues_test_support import (
    FakeProjectRepository,
    InMemoryQualityIssueEventRepository,
    InMemoryQualityIssueRepository,
    qc_create_request,
    qc_now,
)


def _create_request(**overrides):
    return qc_create_request(**overrides)


NOW = qc_now()


def test_days_open_for_issue() -> None:
    issue = {"first_seen_at": NOW - timedelta(days=15)}

    assert days_open_for_issue(issue, now=NOW) == 15


def test_is_critical_open_over_days_requires_critical_severity() -> None:
    issue = {
        "severity": "HIGH",
        "first_seen_at": NOW - timedelta(days=20),
    }

    assert not is_critical_open_over_days(
        issue,
        threshold=CRITICAL_STALE_DAYS_THRESHOLD,
        now=NOW,
    )


def test_is_critical_open_over_days_boundary() -> None:
    exactly_14 = {
        "severity": "CRITICAL",
        "first_seen_at": NOW - timedelta(days=14),
    }
    over_14 = {
        "severity": "CRITICAL",
        "first_seen_at": NOW - timedelta(days=15),
    }

    assert not is_critical_open_over_days(exactly_14, now=NOW)
    assert is_critical_open_over_days(over_14, now=NOW)


def test_count_critical_open_over_days() -> None:
    open_issues = [
        {
            "project_id": "proj-1",
            "severity": "CRITICAL",
            "first_seen_at": NOW - timedelta(days=20),
        },
        {
            "project_id": "proj-1",
            "severity": "CRITICAL",
            "first_seen_at": NOW - timedelta(days=3),
        },
        {
            "project_id": "proj-2",
            "severity": "MEDIUM",
            "first_seen_at": NOW - timedelta(days=30),
        },
    ]

    assert count_critical_open_over_days(open_issues, now=NOW) == 1


def test_aggregate_critical_stale_by_project() -> None:
    open_issues = [
        {
            "project_id": "proj-1",
            "severity": "CRITICAL",
            "first_seen_at": NOW - timedelta(days=20),
        },
        {
            "project_id": "proj-1",
            "severity": "CRITICAL",
            "first_seen_at": NOW - timedelta(days=16),
        },
        {
            "project_id": "proj-2",
            "severity": "CRITICAL",
            "first_seen_at": NOW - timedelta(days=2),
        },
    ]

    assert aggregate_critical_stale_by_project(open_issues, now=NOW) == {
        "proj-1": 2,
    }


def test_build_open_issues_per_project_summaries_includes_stale_critical() -> None:
    summaries = build_open_issues_per_project_summaries(
        projects=[
            {"id": "proj-1", "project_name": "א"},
            {"id": "proj-2", "project_name": "ב"},
        ],
        open_counts_by_project={
            "proj-1": {"open_total": 2, "open_critical": 2},
            "proj-2": {"open_total": 1, "open_critical": 1},
        },
        critical_stale_by_project={"proj-1": 1},
    )

    proj_one = next(item for item in summaries if item.project_id == "proj-1")
    proj_two = next(item for item in summaries if item.project_id == "proj-2")

    assert proj_one.critical_open_over_14_days == 1
    assert proj_two.critical_open_over_14_days == 0
    assert summaries[0].project_id == "proj-1"


@pytest.fixture
def portfolio_service() -> QualityIssueService:
    return QualityIssueService(
        issue_repository=InMemoryQualityIssueRepository(),
        event_repository=InMemoryQualityIssueEventRepository(),
        project_repository=FakeProjectRepository(),
    )


def test_portfolio_quality_summary_critical_stale_kpi(
    portfolio_service: QualityIssueService,
) -> None:
    service = portfolio_service
    stale_seen = datetime(2026, 5, 20, 12, 0, tzinfo=UTC)

    service.create_issue(
        organization_id="org-1",
        project_id="proj-1",
        request=_create_request(
            title="קריטי ישן",
            severity=QualityIssueSeverity.CRITICAL,
            first_seen_at=stale_seen,
            materialization_key="k1",
        ),
        actor_role="SUPERVISOR",
    )
    service.create_issue(
        organization_id="org-1",
        project_id="proj-1",
        request=_create_request(
            title="קריטי חדש",
            severity=QualityIssueSeverity.CRITICAL,
            materialization_key="k2",
        ),
        actor_role="SUPERVISOR",
    )
    closed = service.create_issue(
        organization_id="org-1",
        project_id="proj-2",
        request=_create_request(
            title="סגור",
            materialization_key="k3",
        ),
        actor_role="SUPERVISOR",
    )
    service.update_issue(
        organization_id="org-1",
        issue_id=closed["id"],
        request=QualityIssueUpdateRequest(
            status=QualityIssueStatus.CLOSED,
            last_seen_report_id="report-1",
        ),
        actor_role="SUPERVISOR",
        actor_id="supervisor-1",
    )

    summary = service.get_portfolio_quality_summary(
        organization_id="org-1",
        actor_role="SUPERVISOR",
    )

    assert summary.critical_open_over_14_days == 1
    assert summary.projects[0].project_id == "proj-1"
    assert summary.projects[0].critical_open_over_14_days == 1
