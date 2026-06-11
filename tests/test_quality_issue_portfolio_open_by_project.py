"""Portfolio KPI 4.1.1 - open issues per project."""

from __future__ import annotations

import pytest

from app.schemas.quality_issue import (
    QualityIssueSeverity,
    QualityIssueStatus,
    QualityIssueUpdateRequest,
)
from app.services.quality_issue_portfolio_kpi import (
    aggregate_open_issue_counts_by_project,
    build_open_issues_per_project_summaries,
    count_projects_with_open_issues,
)
from app.services.quality_issue_service import QualityIssueService
from tests.quality_issues_test_support import (
    FakeProjectRepository,
    InMemoryQualityIssueEventRepository,
    InMemoryQualityIssueRepository,
    qc_create_request,
)


def _create_request(**overrides):
    return qc_create_request(**overrides)


def test_aggregate_open_issue_counts_by_project() -> None:
    counts = aggregate_open_issue_counts_by_project(
        [
            {
                "project_id": "proj-1",
                "severity": "CRITICAL",
            },
            {
                "project_id": "proj-1",
                "severity": "MEDIUM",
            },
            {
                "project_id": "proj-2",
                "severity": "LOW",
            },
        ]
    )

    assert counts["proj-1"] == {"open_total": 2, "open_critical": 1}
    assert counts["proj-2"] == {"open_total": 1, "open_critical": 0}


def test_build_open_issues_per_project_summaries_includes_zero_open_projects() -> None:
    summaries = build_open_issues_per_project_summaries(
        projects=[
            {"id": "proj-1", "project_name": "א"},
            {"id": "proj-2", "project_name": "ב"},
            {"id": "proj-3", "project_name": "ג"},
        ],
        open_counts_by_project={
            "proj-1": {"open_total": 2, "open_critical": 1},
            "proj-3": {"open_total": 1, "open_critical": 0},
        },
    )

    assert [item.project_id for item in summaries] == [
        "proj-1",
        "proj-3",
        "proj-2",
    ]
    assert summaries[0].open_total == 2
    assert summaries[1].open_total == 1
    assert summaries[2].open_total == 0
    assert summaries[2].open_critical == 0


def test_count_projects_with_open_issues() -> None:
    summaries = build_open_issues_per_project_summaries(
        projects=[
            {"id": "proj-1", "project_name": "א"},
            {"id": "proj-2", "project_name": "ב"},
        ],
        open_counts_by_project={
            "proj-1": {"open_total": 1, "open_critical": 0},
        },
    )

    assert count_projects_with_open_issues(summaries) == 1


@pytest.fixture
def portfolio_service() -> QualityIssueService:
    return QualityIssueService(
        issue_repository=InMemoryQualityIssueRepository(),
        event_repository=InMemoryQualityIssueEventRepository(),
        project_repository=FakeProjectRepository(),
    )


def test_portfolio_quality_summary_lists_open_issues_per_project_kpi(
    portfolio_service: QualityIssueService,
) -> None:
    service = portfolio_service

    service.create_issue(
        organization_id="org-1",
        project_id="proj-1",
        request=_create_request(
            title="קריטי",
            severity=QualityIssueSeverity.CRITICAL,
            materialization_key="k1",
        ),
        actor_role="SUPERVISOR",
    )
    service.create_issue(
        organization_id="org-1",
        project_id="proj-1",
        request=_create_request(
            title="פתוח",
            severity=QualityIssueSeverity.MEDIUM,
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

    assert len(summary.projects) == 2
    assert summary.projects[0].project_id == "proj-1"
    assert summary.projects[0].open_total == 2
    assert summary.projects[0].open_critical == 1
    assert summary.projects[1].project_id == "proj-2"
    assert summary.projects[1].open_total == 0
    assert summary.projects[1].open_critical == 0
