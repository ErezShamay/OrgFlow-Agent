"""Portfolio KPI 4.1.4 - average open days."""

from __future__ import annotations

from datetime import timedelta

import pytest

from app.schemas.quality_issue import (
    QualityIssueSeverity,
    QualityIssueStatus,
    QualityIssueUpdateRequest,
)
from app.services.quality_issue_portfolio_kpi import (
    AVERAGE_OPEN_DAYS_HEALTHY_THRESHOLD,
    aggregate_average_open_days_by_project,
    build_open_issues_per_project_summaries,
    collect_open_days_for_issues,
    compute_average_open_days,
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


def test_collect_open_days_for_issues() -> None:
    open_issues = [
        {"first_seen_at": NOW - timedelta(days=10)},
        {"first_seen_at": NOW - timedelta(days=20)},
        {"first_seen_at": None},
    ]

    assert collect_open_days_for_issues(open_issues, now=NOW) == [10, 20]


def test_compute_average_open_days() -> None:
    open_issues = [
        {"first_seen_at": NOW - timedelta(days=10)},
        {"first_seen_at": NOW - timedelta(days=20)},
    ]

    assert compute_average_open_days(open_issues, now=NOW) == 15.0
    assert compute_average_open_days([], now=NOW) is None


def test_aggregate_average_open_days_by_project() -> None:
    open_issues = [
        {
            "project_id": "proj-1",
            "first_seen_at": NOW - timedelta(days=10),
        },
        {
            "project_id": "proj-1",
            "first_seen_at": NOW - timedelta(days=20),
        },
        {
            "project_id": "proj-2",
            "first_seen_at": NOW - timedelta(days=4),
        },
    ]

    assert aggregate_average_open_days_by_project(open_issues, now=NOW) == {
        "proj-1": 15.0,
        "proj-2": 4.0,
    }


def test_build_open_issues_per_project_summaries_includes_average_open_days() -> None:
    summaries = build_open_issues_per_project_summaries(
        projects=[
            {"id": "proj-1", "project_name": "א"},
            {"id": "proj-2", "project_name": "ב"},
        ],
        open_counts_by_project={
            "proj-1": {"open_total": 2, "open_critical": 0},
            "proj-2": {"open_total": 0, "open_critical": 0},
        },
        average_open_days_by_project={"proj-1": 12.5},
    )

    proj_one = next(item for item in summaries if item.project_id == "proj-1")
    proj_two = next(item for item in summaries if item.project_id == "proj-2")

    assert proj_one.average_open_days == 12.5
    assert proj_two.average_open_days is None


def test_average_open_days_healthy_threshold_constant() -> None:
    assert AVERAGE_OPEN_DAYS_HEALTHY_THRESHOLD == 14


@pytest.fixture
def portfolio_service() -> QualityIssueService:
    return QualityIssueService(
        issue_repository=InMemoryQualityIssueRepository(),
        event_repository=InMemoryQualityIssueEventRepository(),
        project_repository=FakeProjectRepository(),
    )


def test_portfolio_quality_summary_average_open_days_kpi(
    portfolio_service: QualityIssueService,
) -> None:
    service = portfolio_service

    service.create_issue(
        organization_id="org-1",
        project_id="proj-1",
        request=_create_request(
            title="פתוח קצר",
            first_seen_at=NOW - timedelta(days=5),
            materialization_key="k1",
        ),
        actor_role="SUPERVISOR",
    )
    service.create_issue(
        organization_id="org-1",
        project_id="proj-1",
        request=_create_request(
            title="פתוח ארוך",
            first_seen_at=NOW - timedelta(days=25),
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

    assert summary.average_open_days == 15.0
    assert summary.projects[0].project_id == "proj-1"
    assert summary.projects[0].average_open_days == 15.0
