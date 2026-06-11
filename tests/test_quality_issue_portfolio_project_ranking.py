"""Portfolio KPI 4.1.5 - project ranking by open_critical, open_total."""

from __future__ import annotations

from app.schemas.quality_issue import QualityPortfolioProjectSummary
from app.services.quality_issue_portfolio_kpi import (
    build_open_issues_per_project_summaries,
    count_projects_with_open_critical,
    rank_portfolio_projects_by_qc_pressure,
)


def _summary(
    project_id: str,
    *,
    project_name: str | None,
    open_total: int,
    open_critical: int,
) -> QualityPortfolioProjectSummary:
    return QualityPortfolioProjectSummary(
        project_id=project_id,
        project_name=project_name,
        open_total=open_total,
        open_critical=open_critical,
    )


def test_rank_portfolio_projects_by_qc_pressure() -> None:
    ranked = rank_portfolio_projects_by_qc_pressure(
        [
            _summary("proj-1", project_name="א", open_total=3, open_critical=1),
            _summary("proj-2", project_name="ב", open_total=5, open_critical=2),
            _summary("proj-3", project_name="ג", open_total=1, open_critical=2),
        ]
    )

    assert [item.project_id for item in ranked] == [
        "proj-2",
        "proj-3",
        "proj-1",
    ]


def test_rank_portfolio_projects_by_open_total_tiebreaker() -> None:
    ranked = rank_portfolio_projects_by_qc_pressure(
        [
            _summary("proj-1", project_name="א", open_total=2, open_critical=1),
            _summary("proj-2", project_name="ב", open_total=4, open_critical=1),
        ]
    )

    assert [item.project_id for item in ranked] == ["proj-2", "proj-1"]


def test_build_open_issues_per_project_summaries_uses_qc_ranking() -> None:
    summaries = build_open_issues_per_project_summaries(
        projects=[
            {"id": "proj-1", "project_name": "א"},
            {"id": "proj-2", "project_name": "ב"},
            {"id": "proj-3", "project_name": "ג"},
        ],
        open_counts_by_project={
            "proj-1": {"open_total": 2, "open_critical": 0},
            "proj-2": {"open_total": 1, "open_critical": 1},
        },
    )

    assert [item.project_id for item in summaries] == [
        "proj-2",
        "proj-1",
        "proj-3",
    ]


def test_count_projects_with_open_critical() -> None:
    summaries = [
        _summary("proj-1", project_name="א", open_total=2, open_critical=1),
        _summary("proj-2", project_name="ב", open_total=1, open_critical=0),
    ]

    assert count_projects_with_open_critical(summaries) == 1
