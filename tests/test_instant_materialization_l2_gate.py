"""Gate L2 — C04 promote DRAFT→PUBLISHED (COMPETITIVE-LAYER-TASKS.md)."""

from __future__ import annotations

from pathlib import Path

from app.schemas.quality_issue import (
    IssueVisibility,
    QualityIssueEventType,
    QualityIssueStatus,
)
from app.services.field_report_finalize_steps import FieldReportFinalizeSteps
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


def _service(
    *,
    reports: FakeVisitReportRepository,
    lines: FakeVisitReportLineRepository,
    issues: InMemoryQualityIssueRepository,
    events: InMemoryQualityIssueEventRepository | None = None,
) -> QualityIssueMaterializationService:
    return QualityIssueMaterializationService(
        report_repository=reports,
        line_repository=lines,
        line_photo_repository=FakeVisitReportLinePhotoRepository(),
        issue_repository=issues,
        event_repository=events or InMemoryQualityIssueEventRepository(),
    )


def _create_line(
    lines: FakeVisitReportLineRepository,
    report_id: str,
    payload: dict,
) -> dict:
    return lines.create(
        {
            **payload,
            "sort_order": lines.next_sort_order(report_id),
        }
    )


def test_l2_schema_finalize_and_service_wired() -> None:
    schema = (REPO_ROOT / "app" / "schemas" / "quality_issue.py").read_text(
        encoding="utf-8"
    )
    service = (
        REPO_ROOT / "app" / "services" / "quality_issue_materialization_service.py"
    ).read_text(encoding="utf-8")
    steps = (
        REPO_ROOT / "app" / "services" / "field_report_finalize_steps.py"
    ).read_text(encoding="utf-8")

    assert "PUBLISHED_FROM_FINALIZE" in schema
    assert "promote_drafts_for_report" in service
    assert "promote_drafts_for_report" in steps
    assert "_materialize_issues_after_promote" in steps


def test_promote_drafts_for_report_publishes_existing_draft() -> None:
    reports = FakeVisitReportRepository()
    lines = FakeVisitReportLineRepository()
    issues = InMemoryQualityIssueRepository()
    events = InMemoryQualityIssueEventRepository()

    report = reports.create(
        organization_id="org-1",
        project_id="project-1",
        status="IN_PROGRESS",
        visit_date="2026-06-18",
        header_fields={},
        closed_at="2026-06-18T12:00:00+00:00",
    )
    report_id = str(report["id"])
    line = _create_line(
        lines,
        report_id,
        {
            "report_id": report_id,
            "issue_id": "SUP-FIN-004",
            "description": "פוגות",
            "trade": "ריצוף",
            "location": "דירה 5",
            "group_key": "apartment:5",
            "status": "NEEDS_ACTION",
        },
    )
    line_id = str(line["id"])

    service = _service(
        reports=reports,
        lines=lines,
        issues=issues,
        events=events,
    )

    draft = service.materialize_draft_from_defect(
        organization_id="org-1",
        report_id=report_id,
        line_id=line_id,
        actor_id="user-1",
    )
    reports.update(report_id, {"status": "CLOSED"})

    promote = service.promote_drafts_for_report(
        organization_id="org-1",
        report_id=report_id,
        actor_id="user-1",
    )
    assert promote.promoted_count == 1
    assert promote.promoted_issue_ids == [draft.issue_id]

    issue = issues.get_for_organization(
        issue_id=draft.issue_id,
        organization_id="org-1",
    )
    assert issue is not None
    assert issue["visibility"] == IssueVisibility.PUBLISHED.value
    assert issue["last_seen_report_id"] == report_id
    assert issue["last_seen_line_id"] == line_id

    issue_events = events.list_by_issue_id(draft.issue_id)
    event_types = [event["event_type"] for event in issue_events]
    assert QualityIssueEventType.CREATED_FROM_FIELD.value in event_types
    assert QualityIssueEventType.PUBLISHED_FROM_FINALIZE.value in event_types
    assert QualityIssueEventType.DETECTED.value not in event_types


def test_finalize_materialize_does_not_duplicate_promoted_draft() -> None:
    reports = FakeVisitReportRepository()
    lines = FakeVisitReportLineRepository()
    issues = InMemoryQualityIssueRepository()
    events = InMemoryQualityIssueEventRepository()

    report = reports.create(
        organization_id="org-1",
        project_id="project-1",
        status="IN_PROGRESS",
        visit_date="2026-06-18",
        header_fields={},
        closed_at="2026-06-18T12:00:00+00:00",
    )
    report_id = str(report["id"])
    line = _create_line(
        lines,
        report_id,
        {
            "report_id": report_id,
            "issue_id": "SUP-FIN-004",
            "description": "פוגות",
            "trade": "ריצוף",
            "location": "דירה 5",
            "status": "NEEDS_ACTION",
        },
    )
    line_id = str(line["id"])

    service = _service(
        reports=reports,
        lines=lines,
        issues=issues,
        events=events,
    )
    draft = service.materialize_draft_from_defect(
        organization_id="org-1",
        report_id=report_id,
        line_id=line_id,
        actor_id="user-1",
    )
    reports.update(report_id, {"status": "CLOSED"})

    promote = service.promote_drafts_for_report(
        organization_id="org-1",
        report_id=report_id,
        actor_id="user-1",
    )
    materialized = service.materialize_issues_from_report(
        organization_id="org-1",
        report_id=report_id,
        actor_id="user-1",
    )

    assert promote.promoted_count == 1
    assert materialized.created_count == 0
    assert materialized.skipped_count == 1
    assert len(issues.records) == 1
    assert str(issues.records[draft.issue_id]["visibility"]) == (
        IssueVisibility.PUBLISHED.value
    )


def test_finalize_materialize_creates_issues_for_lines_without_draft() -> None:
    reports = FakeVisitReportRepository()
    lines = FakeVisitReportLineRepository()
    issues = InMemoryQualityIssueRepository()
    events = InMemoryQualityIssueEventRepository()

    report = reports.create(
        organization_id="org-1",
        project_id="project-1",
        status="CLOSED",
        visit_date="2026-06-18",
        header_fields={},
        closed_at="2026-06-18T12:00:00+00:00",
    )
    report_id = str(report["id"])
    _create_line(
        lines,
        report_id,
        {
            "report_id": report_id,
            "description": "סדק בקיר",
            "location": "דירה 3",
            "status": "NEEDS_ACTION",
        },
    )

    service = _service(
        reports=reports,
        lines=lines,
        issues=issues,
        events=events,
    )
    promote = service.promote_drafts_for_report(
        organization_id="org-1",
        report_id=report_id,
        actor_id="user-1",
    )
    materialized = service.materialize_issues_from_report(
        organization_id="org-1",
        report_id=report_id,
        actor_id="user-1",
    )

    assert promote.promoted_count == 0
    assert materialized.created_count == 1
    issue = next(iter(issues.records.values()))
    assert issue["visibility"] == IssueVisibility.PUBLISHED.value
    assert issue["status"] == QualityIssueStatus.OPEN.value
    detected = [
        event
        for event in events.records.values()
        if event["event_type"] == QualityIssueEventType.DETECTED.value
    ]
    assert len(detected) == 1


def test_mixed_draft_and_new_lines_materialize_once_each() -> None:
    reports = FakeVisitReportRepository()
    lines = FakeVisitReportLineRepository()
    issues = InMemoryQualityIssueRepository()
    events = InMemoryQualityIssueEventRepository()

    report = reports.create(
        organization_id="org-1",
        project_id="project-1",
        status="IN_PROGRESS",
        visit_date="2026-06-18",
        header_fields={},
        closed_at="2026-06-18T12:00:00+00:00",
    )
    report_id = str(report["id"])
    draft_line = _create_line(
        lines,
        report_id,
        {
            "report_id": report_id,
            "issue_id": "SUP-FIN-004",
            "description": "פוגות",
            "location": "דירה 5",
            "status": "NEEDS_ACTION",
        },
    )
    _create_line(
        lines,
        report_id,
        {
            "report_id": report_id,
            "description": "איטום לקוי",
            "location": "מרפסת",
            "status": "NEEDS_ACTION",
        },
    )

    service = _service(
        reports=reports,
        lines=lines,
        issues=issues,
        events=events,
    )
    draft = service.materialize_draft_from_defect(
        organization_id="org-1",
        report_id=report_id,
        line_id=str(draft_line["id"]),
        actor_id="user-1",
    )
    reports.update(report_id, {"status": "CLOSED"})

    promote = service.promote_drafts_for_report(
        organization_id="org-1",
        report_id=report_id,
        actor_id="user-1",
    )
    materialized = service.materialize_issues_from_report(
        organization_id="org-1",
        report_id=report_id,
        actor_id="user-1",
    )

    assert promote.promoted_count == 1
    assert materialized.created_count == 1
    assert materialized.skipped_count == 1
    assert len(issues.records) == 2
    assert issues.records[draft.issue_id]["visibility"] == (
        IssueVisibility.PUBLISHED.value
    )


def test_promote_drafts_for_report_is_idempotent() -> None:
    reports = FakeVisitReportRepository()
    lines = FakeVisitReportLineRepository()
    issues = InMemoryQualityIssueRepository()

    report = reports.create(
        organization_id="org-1",
        project_id="project-1",
        status="IN_PROGRESS",
        visit_date="2026-06-18",
        header_fields={},
        closed_at="2026-06-18T12:00:00+00:00",
    )
    report_id = str(report["id"])
    line = _create_line(
        lines,
        report_id,
        {
            "report_id": report_id,
            "issue_id": "SUP-FIN-004",
            "description": "פוגות",
            "status": "NEEDS_ACTION",
        },
    )

    service = _service(reports=reports, lines=lines, issues=issues)
    service.materialize_draft_from_defect(
        organization_id="org-1",
        report_id=report_id,
        line_id=str(line["id"]),
    )
    reports.update(report_id, {"status": "CLOSED"})

    first = service.promote_drafts_for_report(
        organization_id="org-1",
        report_id=report_id,
    )
    second = service.promote_drafts_for_report(
        organization_id="org-1",
        report_id=report_id,
    )

    assert first.promoted_count == 1
    assert second.promoted_count == 0
    issue = issues.get_for_organization(
        issue_id=first.promoted_issue_ids[0],
        organization_id="org-1",
    )
    assert issue is not None
    assert issue["visibility"] == IssueVisibility.PUBLISHED.value


def test_c04_step_promotes_before_materialize() -> None:
    steps_source = (
        REPO_ROOT / "app" / "services" / "field_report_finalize_steps.py"
    ).read_text(encoding="utf-8")
    assert "promote_drafts_for_report" in steps_source
    assert FieldReportFinalizeSteps._step_c04_materialize_issues is not None
