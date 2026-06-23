"""Gate D1 — project supervision dashboard aggregation."""

from __future__ import annotations

from app.lib.supervision_dashboard_aggregation import (
    aggregate_supervision_dashboard,
    classify_checklist_item,
    pick_latest_reports_by_apartment,
    resolve_overall_status,
)
from app.schemas.project_supervision_dashboard import SupervisionOverallStatus
from app.schemas.quality_issue import (
    IssueVisibility,
    QualityIssueStatus,
)
from app.services.project_supervision_dashboard_service import (
    ProjectSupervisionDashboardService,
)
from tests.quality_issues_test_support import qc_published_issue_payload
from tests.test_project_zero_setup_gate import (
    InMemoryProjectApartmentRepository,
    InMemoryProjectRepository,
)


def _checklist_item(
    *,
    item_id: str,
    status: str,
    category_name_he: str,
    category_id: str,
    linked_line_id: str | None = None,
) -> dict:
    return {
        "id": item_id,
        "catalog_issue_id": f"CAT-{item_id}",
        "issue_name_he": f"פריט {item_id}",
        "category_id": category_id,
        "category_name_he": category_name_he,
        "top_family": "FINISHING",
        "standard_ref": 'ת"י 1',
        "status": status,
        "photo_ids": [],
        "linked_line_id": linked_line_id,
        "sort_order": 0,
    }


def _report(
    *,
    report_id: str,
    apartment_number: str,
    items: list[dict],
    updated_at: str,
    status: str = "CLOSED",
) -> dict:
    return {
        "id": report_id,
        "project_id": "proj-d1",
        "organization_id": "org-d1",
        "status": status,
        "updated_at": updated_at,
        "header_fields": {
            "supervision_meta": {
                "construction_stage": "FINISHING",
                "visit_scope": "APARTMENT",
                "apartment_number": apartment_number,
            },
            "blocks": [
                {
                    "id": "checklist-main",
                    "kind": "supervision_checklist",
                    "title_he": f"דירה {apartment_number}",
                    "apartment_number": apartment_number,
                    "items": items,
                }
            ],
        },
    }


def test_pick_latest_reports_by_apartment_uses_newest_closed_report() -> None:
    reports = [
        _report(
            report_id="old",
            apartment_number="5",
            items=[],
            updated_at="2026-06-01T10:00:00Z",
        ),
        _report(
            report_id="new",
            apartment_number="5",
            items=[],
            updated_at="2026-06-10T10:00:00Z",
        ),
        _report(
            report_id="ignored",
            apartment_number="5",
            items=[],
            updated_at="2026-06-20T10:00:00Z",
            status="IN_PROGRESS",
        ),
    ]

    latest = pick_latest_reports_by_apartment(reports)

    assert latest["5"]["id"] == "new"


def test_classify_checklist_item_prefers_published_issue_status() -> None:
    line_id = "line-1"
    issue = qc_published_issue_payload(
        id="issue-1",
        status=QualityIssueStatus.IN_REMEDIATION.value,
        first_seen_line_id=line_id,
    )
    issues_by_line_id = {line_id: issue}

    bucket = classify_checklist_item(
        _checklist_item(
            item_id="1",
            status="DEFECT",
            category_name_he="אינסטלציה",
            category_id="PLUMBING",
            linked_line_id=line_id,
        ),
        issues_by_line_id=issues_by_line_id,
    )

    assert bucket == "in_treatment"


def test_aggregate_supervision_dashboard_computes_calculation_g() -> None:
    line_defect = "line-defect"
    line_ok = "line-ok"

    reports = [
        _report(
            report_id="visit-5",
            apartment_number="5",
            updated_at="2026-06-10T10:00:00Z",
            items=[
                _checklist_item(
                    item_id="ok",
                    status="OK",
                    category_name_he="חשמל",
                    category_id="ELECTRICAL",
                    linked_line_id=line_ok,
                ),
                _checklist_item(
                    item_id="defect",
                    status="DEFECT",
                    category_name_he="אינסטלציה",
                    category_id="PLUMBING",
                    linked_line_id=line_defect,
                ),
                _checklist_item(
                    item_id="unchecked",
                    status="UNCHECKED",
                    category_name_he="חללים",
                    category_id="SPACES",
                ),
            ],
        ),
        _report(
            report_id="visit-6",
            apartment_number="6",
            updated_at="2026-06-11T10:00:00Z",
            items=[
                _checklist_item(
                    item_id="ok-6",
                    status="OK",
                    category_name_he="חשמל",
                    category_id="ELECTRICAL",
                ),
            ],
        ),
    ]

    issues = [
        qc_published_issue_payload(
            id="issue-defect",
            status=QualityIssueStatus.OPEN.value,
            trade="אינסטלציה",
            group_key="apartment:5",
            first_seen_line_id=line_defect,
            severity="HIGH",
        ),
        qc_published_issue_payload(
            id="issue-orphan",
            status=QualityIssueStatus.OPEN.value,
            trade="חשמל",
            group_key="apartment:7",
            materialization_key="orphan-7",
            severity="CRITICAL",
        ),
    ]

    apartments = [
        {
            "id": "apt-5",
            "apartment_number": "5",
            "group_key": "apartment:5",
        },
        {
            "id": "apt-6",
            "apartment_number": "6",
            "group_key": "apartment:6",
        },
        {
            "id": "apt-7",
            "apartment_number": "7",
            "group_key": "apartment:7",
        },
    ]

    dashboard = aggregate_supervision_dashboard(
        project_id="proj-d1",
        project_name="פרויקט בדיקה",
        apartments=apartments,
        reports=reports,
        issues=issues,
    )

    assert dashboard.overall_status == SupervisionOverallStatus.CRITICAL
    assert dashboard.kpis.total_items == 4
    assert dashboard.kpis.completed == 2
    assert dashboard.kpis.with_defects == 2
    assert dashboard.kpis.in_treatment == 0
    assert dashboard.kpis.progress_percent == 50

    trades = {trade.trade_key: trade for trade in dashboard.trades}
    assert trades["electrical"].total_items == 2
    assert trades["electrical"].completed == 2
    assert trades["plumbing"].with_defects == 1

    apartments_by_number = {
        row.apartment_number: row for row in dashboard.apartments
    }
    assert apartments_by_number["5"].progress_percent == 50
    assert apartments_by_number["5"].open_issues_count == 1
    assert apartments_by_number["6"].progress_percent == 100
    assert apartments_by_number["7"].with_defects == 1
    assert apartments_by_number["7"].open_issues_count == 1


def test_resolve_overall_status_levels() -> None:
    from app.lib.supervision_dashboard_aggregation import ProgressCounts

    healthy = resolve_overall_status(
        counts=ProgressCounts(),
        has_critical_open_issue=False,
    )
    attention = resolve_overall_status(
        counts=ProgressCounts(with_defects=1, total=1),
        has_critical_open_issue=False,
    )
    critical = resolve_overall_status(
        counts=ProgressCounts(),
        has_critical_open_issue=True,
    )

    assert healthy == SupervisionOverallStatus.HEALTHY
    assert attention == SupervisionOverallStatus.ATTENTION
    assert critical == SupervisionOverallStatus.CRITICAL


def test_service_build_dashboard_uses_repositories() -> None:
    project_repo = InMemoryProjectRepository()
    apartment_repo = InMemoryProjectApartmentRepository()
    project = project_repo.create_project(
        organization_id="org-d1",
        project_name="שם פרויקט",
    )
    apartment_repo.bulk_create_apartments(
        organization_id="org-d1",
        project_id=project["id"],
        apartments=[{"apartment_number": "3"}],
    )

    class FakeReportRepository:
        def list_by_organization(self, organization_id, *, project_id, include_hidden=False):
            assert organization_id == "org-d1"
            assert project_id == project["id"]
            return [
                _report(
                    report_id="visit-3",
                    apartment_number="3",
                    updated_at="2026-06-10T10:00:00Z",
                    items=[
                        _checklist_item(
                            item_id="ok",
                            status="OK",
                            category_name_he="חשמל",
                            category_id="ELECTRICAL",
                        ),
                    ],
                )
            ]

    class FakeIssueRepository:
        def list_by_project(self, *, organization_id, project_id, query=None):
            return []

    service = ProjectSupervisionDashboardService(
        project_repository=project_repo,
        report_repository=FakeReportRepository(),
        issue_repository=FakeIssueRepository(),
        apartment_repository=apartment_repo,
    )

    dashboard = service.build_dashboard(
        organization_id="org-d1",
        project_id=project["id"],
    )

    assert dashboard.project_name == "שם פרויקט"
    assert dashboard.kpis.total_items == 1
    assert dashboard.kpis.progress_percent == 100
    assert dashboard.apartments[0].apartment_number == "3"
