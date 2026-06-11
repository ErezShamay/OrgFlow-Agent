"""Roadmap 6.1 - trade heatmap aggregation."""

from __future__ import annotations

from app.schemas.quality_issue import QualityIssueUpdateRequest
from app.services.quality_issue_service import QualityIssueService
from app.services.quality_issue_trade_heatmap import (
    UNKNOWN_TRADE_LABEL,
    build_trade_heatmap_cells,
    normalize_trade_label,
)
from tests.quality_issues_test_support import (
    FakeProjectRepository,
    InMemoryQualityIssueEventRepository,
    InMemoryQualityIssueRepository,
    qc_create_request,
)


def test_normalize_trade_label_uses_fallback_for_blank() -> None:
    assert normalize_trade_label(None) == UNKNOWN_TRADE_LABEL
    assert normalize_trade_label("  ") == UNKNOWN_TRADE_LABEL
    assert normalize_trade_label("אינסטלציה") == "אינסטלציה"


def test_build_trade_heatmap_cells_groups_by_trade_and_severity() -> None:
    cells = build_trade_heatmap_cells(
        [
            {
                "trade": "אינסטלציה",
                "severity": "CRITICAL",
            },
            {
                "trade": "אינסטלציה",
                "severity": "HIGH",
            },
            {
                "trade": " ",
                "severity": "MEDIUM",
            },
            {
                "trade": "חשמל",
                "severity": "LOW",
            },
        ]
    )

    assert [cell.trade for cell in cells] == [
        "אינסטלציה",
        "חשמל",
        UNKNOWN_TRADE_LABEL,
    ]
    assert cells[0].open_total == 2
    assert cells[0].open_critical == 1
    assert cells[0].open_high == 1
    assert cells[2].open_medium == 1
    assert cells[1].open_low == 1


def test_service_portfolio_trade_heatmap_filters_project_and_open_only() -> None:
    service = QualityIssueService(
        issue_repository=InMemoryQualityIssueRepository(),
        event_repository=InMemoryQualityIssueEventRepository(),
        project_repository=FakeProjectRepository(),
    )

    service.create_issue(
        organization_id="org-1",
        project_id="proj-1",
        request=qc_create_request(
            title="אינסטלציה פתוח",
            trade="אינסטלציה",
            severity="CRITICAL",
            materialization_key="trade-1",
        ),
        actor_role="SUPERVISOR",
    )
    service.create_issue(
        organization_id="org-1",
        project_id="proj-2",
        request=qc_create_request(
            title="חשמל פתוח",
            trade="חשמל",
            materialization_key="trade-2",
        ),
        actor_role="SUPERVISOR",
    )
    closed = service.create_issue(
        organization_id="org-1",
        project_id="proj-1",
        request=qc_create_request(
            title="סגור",
            trade="אינסטלציה",
            materialization_key="trade-3",
        ),
        actor_role="SUPERVISOR",
    )
    service.update_issue(
        organization_id="org-1",
        issue_id=closed["id"],
        request=QualityIssueUpdateRequest(
            status="CLOSED",
            last_seen_report_id="report-1",
        ),
        actor_role="SUPERVISOR",
        actor_id="supervisor-1",
    )

    org_heatmap = service.get_portfolio_trade_heatmap(
        organization_id="org-1",
        actor_role="DEVELOPER",
    )
    assert org_heatmap.total_open == 2
    assert [cell.trade for cell in org_heatmap.cells] == [
        "אינסטלציה",
        "חשמל",
    ]

    project_heatmap = service.get_portfolio_trade_heatmap(
        organization_id="org-1",
        actor_role="DEVELOPER",
        project_id="proj-1",
    )
    assert project_heatmap.project_id == "proj-1"
    assert project_heatmap.total_open == 1
    assert project_heatmap.cells[0].trade == "אינסטלציה"
    assert project_heatmap.cells[0].open_critical == 1
