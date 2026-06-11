"""Portfolio KPI 4.1.3 - closed within 30 days percent."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from app.schemas.quality_issue import (
    QualityIssueStatus,
    QualityIssueUpdateRequest,
)
from app.services.quality_issue_portfolio_kpi import (
    CLOSED_WITHIN_DAYS_THRESHOLD,
    compute_closed_within_days_percent,
    count_closed_within_days,
    days_to_close_for_issue,
    is_closed_within_days,
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


def test_days_to_close_for_issue() -> None:
    issue = {
        "first_seen_at": NOW - timedelta(days=10),
        "closed_at": NOW,
    }

    assert days_to_close_for_issue(issue) == 10


def test_is_closed_within_days_boundary() -> None:
    within = {
        "first_seen_at": NOW - timedelta(days=30),
        "closed_at": NOW,
    }
    over = {
        "first_seen_at": NOW - timedelta(days=31),
        "closed_at": NOW,
    }

    assert is_closed_within_days(within)
    assert not is_closed_within_days(over)


def test_count_closed_within_days() -> None:
    closed_issues = [
        {
            "first_seen_at": NOW - timedelta(days=5),
            "closed_at": NOW,
        },
        {
            "first_seen_at": NOW - timedelta(days=40),
            "closed_at": NOW,
        },
        {
            "first_seen_at": NOW - timedelta(days=2),
            "closed_at": None,
        },
    ]

    assert count_closed_within_days(closed_issues) == 1


def test_compute_closed_within_days_percent() -> None:
    closed_issues = [
        {
            "first_seen_at": NOW - timedelta(days=5),
            "closed_at": NOW,
        },
        {
            "first_seen_at": NOW - timedelta(days=40),
            "closed_at": NOW,
        },
    ]

    assert compute_closed_within_days_percent(closed_issues) == 50.0
    assert compute_closed_within_days_percent([]) is None


def test_compute_closed_within_days_percent_uses_threshold_constant() -> None:
    assert CLOSED_WITHIN_DAYS_THRESHOLD == 30


@pytest.fixture
def portfolio_service() -> QualityIssueService:
    return QualityIssueService(
        issue_repository=InMemoryQualityIssueRepository(),
        event_repository=InMemoryQualityIssueEventRepository(),
        project_repository=FakeProjectRepository(),
    )


def test_portfolio_quality_summary_closed_within_30_days_kpi(
    portfolio_service: QualityIssueService,
) -> None:
    service = portfolio_service

    fast_close = service.create_issue(
        organization_id="org-1",
        project_id="proj-1",
        request=_create_request(
            title="נסגר מהר",
            first_seen_at=NOW - timedelta(days=7),
            materialization_key="k1",
        ),
        actor_role="SUPERVISOR",
    )
    slow_close = service.create_issue(
        organization_id="org-1",
        project_id="proj-1",
        request=_create_request(
            title="נסגר לאט",
            first_seen_at=NOW - timedelta(days=45),
            materialization_key="k2",
        ),
        actor_role="SUPERVISOR",
    )
    service.create_issue(
        organization_id="org-1",
        project_id="proj-2",
        request=_create_request(
            title="פתוח",
            materialization_key="k3",
        ),
        actor_role="SUPERVISOR",
    )

    for issue_id, closed_at in (
        (fast_close["id"], NOW - timedelta(days=2)),
        (slow_close["id"], NOW),
    ):
        service.update_issue(
            organization_id="org-1",
            issue_id=issue_id,
            request=QualityIssueUpdateRequest(
                status=QualityIssueStatus.CLOSED,
                last_seen_report_id="report-1",
                closed_at=closed_at,
            ),
            actor_role="SUPERVISOR",
            actor_id="supervisor-1",
        )

    summary = service.get_portfolio_quality_summary(
        organization_id="org-1",
        actor_role="SUPERVISOR",
    )

    assert summary.closed_within_30_days_percent == 50.0
