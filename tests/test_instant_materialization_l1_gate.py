"""Gate L1 — instant draft materialization on DEFECT (COMPETITIVE-LAYER-TASKS.md)."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.exceptions.exceptions import ValidationError
from app.schemas.quality_issue import (
    IssueVisibility,
    QualityIssueEventType,
    QualityIssueStatus,
)
from app.services.quality_issue_materialization_service import (
    QualityIssueMaterializationService,
)
from tests.quality_issues_test_support import (
    InMemoryQualityIssueEventRepository,
    InMemoryQualityIssueRepository,
)
from tests.test_field_visit_reports import (
    FakeVisitReportLinePhotoRepository,
    FakeVisitReportLineRepository,
    FakeVisitReportRepository,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_l1_schema_and_api_wired() -> None:
    schema = (REPO_ROOT / "app" / "schemas" / "quality_issue.py").read_text(
        encoding="utf-8"
    )
    service = (
        REPO_ROOT / "app" / "services" / "quality_issue_materialization_service.py"
    ).read_text(encoding="utf-8")
    main = (REPO_ROOT / "app" / "main.py").read_text(encoding="utf-8")
    draft_ts = (
        REPO_ROOT / "orgflow-ui" / "lib" / "field-reports" / "checklist-defect-draft.ts"
    ).read_text(encoding="utf-8")

    assert "CREATED_FROM_FIELD" in schema
    assert "materialize_draft_from_defect" in service
    assert "/lines/{line_id}/draft-issue" in main
    assert "syncSupervisionDefectDraftsForReport" in draft_ts


def test_materialize_draft_from_defect_creates_draft_issue() -> None:
    reports = FakeVisitReportRepository()
    lines = FakeVisitReportLineRepository()
    events = InMemoryQualityIssueEventRepository()

    report = reports.create(
        organization_id="org-1",
        project_id="project-1",
        status="IN_PROGRESS",
        visit_date="2026-06-18",
        header_fields={},
    )
    report_id = str(report["id"])
    line = lines.create(
        {
            "report_id": report_id,
            "issue_id": "SUP-FIN-004",
            "description": "פוגות",
            "trade": "ריצוף",
            "location": "דירה 5",
            "group_key": "apartment:5",
            "group_label_he": "דירה 5",
            "standard_ref": 'ת"י 1555',
            "status": "NEEDS_ACTION",
        }
    )
    line_id = str(line["id"])

    service = QualityIssueMaterializationService(
        report_repository=reports,
        line_repository=lines,
        line_photo_repository=FakeVisitReportLinePhotoRepository(),
        issue_repository=InMemoryQualityIssueRepository(),
        event_repository=events,
    )

    first = service.materialize_draft_from_defect(
        organization_id="org-1",
        report_id=report_id,
        line_id=line_id,
        actor_id="user-1",
        checklist_item_id="checklist-SUP-FIN-004",
    )
    assert first.created is True
    assert first.visibility == IssueVisibility.DRAFT.value

    issue = service.issue_repository.get_for_organization(
        issue_id=first.issue_id,
        organization_id="org-1",
    )
    assert issue is not None
    assert issue["visibility"] == IssueVisibility.DRAFT.value
    assert issue["status"] == QualityIssueStatus.OPEN.value
    assert issue["catalog_issue_id"] == "SUP-FIN-004"
    assert issue["materialization_key"] == f"{report_id}:{line_id}"

    issue_events = events.list_by_issue_id(first.issue_id)
    assert len(issue_events) == 1
    assert issue_events[0]["event_type"] == QualityIssueEventType.CREATED_FROM_FIELD.value

    second = service.materialize_draft_from_defect(
        organization_id="org-1",
        report_id=report_id,
        line_id=line_id,
        actor_id="user-1",
        checklist_item_id="checklist-SUP-FIN-004",
    )
    assert second.created is False
    assert second.issue_id == first.issue_id


def test_materialize_draft_from_defect_rejects_closed_report() -> None:
    reports = FakeVisitReportRepository()
    lines = FakeVisitReportLineRepository()
    report = reports.create(
        organization_id="org-1",
        project_id="project-1",
        status="CLOSED",
        visit_date="2026-06-18",
        header_fields={},
    )
    report_id = str(report["id"])
    line = lines.create(
        {
            "report_id": report_id,
            "issue_id": "SUP-FIN-004",
            "description": "פוגות",
        }
    )
    line_id = str(line["id"])

    service = QualityIssueMaterializationService(
        report_repository=reports,
        line_repository=lines,
        line_photo_repository=FakeVisitReportLinePhotoRepository(),
        issue_repository=InMemoryQualityIssueRepository(),
    )

    with pytest.raises(ValidationError):
        service.materialize_draft_from_defect(
            organization_id="org-1",
            report_id=report_id,
            line_id=line_id,
        )
