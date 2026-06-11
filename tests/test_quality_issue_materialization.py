from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.exceptions.exceptions import NotFoundError, ValidationError
from app.schemas.quality_issue import QualityIssueEventType, QualityIssueStatus
from app.services.field_visit_report_service import FieldVisitReportService
from app.services.quality_issue_materialization_service import (
    MaterializationResult,
    QualityIssueMaterializationService,
    collect_materializable_finding_rows,
    extract_finding_rows_from_blocks,
    materializable_rows_from_lines,
)
from tests.quality_issues_test_support import (
    InMemoryQualityIssueEventRepository,
    InMemoryQualityIssueRepository,
    qc_create_request,
)
from tests.test_field_visit_reports import (
    FakeProjectRepository,
    FakeVisitReportLinePhotoRepository,
    FakeVisitReportLineRepository,
    FakeVisitReportRepository,
)


def _closed_report(
    *,
    report_id: str = "report-1",
    organization_id: str = "org-1",
    project_id: str = "project-1",
    header_fields: dict | None = None,
    closed_at: str = "2026-06-09T10:00:00+00:00",
) -> dict:
    return {
        "id": report_id,
        "organization_id": organization_id,
        "project_id": project_id,
        "status": "CLOSED",
        "visit_date": "2026-06-01",
        "closed_at": closed_at,
        "header_fields": header_fields or {},
    }


def _materialization_service(
    *,
    reports: FakeVisitReportRepository | None = None,
    lines: FakeVisitReportLineRepository | None = None,
    line_photos: FakeVisitReportLinePhotoRepository | None = None,
    issues: InMemoryQualityIssueRepository | None = None,
    events: InMemoryQualityIssueEventRepository | None = None,
) -> QualityIssueMaterializationService:
    return QualityIssueMaterializationService(
        report_repository=reports or FakeVisitReportRepository(),
        line_repository=lines or FakeVisitReportLineRepository(),
        line_photo_repository=line_photos or FakeVisitReportLinePhotoRepository(),
        issue_repository=issues or InMemoryQualityIssueRepository(),
        event_repository=events or InMemoryQualityIssueEventRepository(),
    )


def test_extract_finding_rows_from_blocks_filters_empty_rows() -> None:
    header_fields = {
        "blocks": [
            {
                "id": "findings-1",
                "kind": "findings_table",
                "title_he": "ממצאים",
                "rows": [
                    {
                        "id": "row-1",
                        "description": "סדק בקיר",
                        "location": "דירה 3",
                    },
                    {
                        "id": "row-2",
                        "location": "לובי",
                    },
                    {
                        "id": "row-3",
                        "issue_id": "STR-001",
                    },
                ],
            },
            {
                "id": "progress-1",
                "kind": "progress_table",
                "title_he": "התקדמות",
                "rows": [{"id": "p1", "description": "ביסוס"}],
            },
        ]
    }

    rows = extract_finding_rows_from_blocks(header_fields)

    assert [row.line_id for row in rows] == ["row-1", "row-3"]
    assert rows[0].description == "סדק בקיר"
    assert rows[1].catalog_issue_id == "STR-001"


def test_materializable_rows_from_lines_includes_photo_only_rows() -> None:
    rows = materializable_rows_from_lines(
        [
            {
                "id": "line-1",
                "description": "נזילה",
                "photo_ids": ["photo-1"],
            }
        ]
    )

    assert len(rows) == 1
    assert rows[0].line_id == "line-1"
    assert rows[0].photo_ids == ["photo-1"]


def test_collect_materializable_finding_rows_prefers_line_data() -> None:
    header_fields = {
        "blocks": [
            {
                "id": "findings-1",
                "kind": "findings_table",
                "title_he": "ממצאים",
                "rows": [
                    {
                        "id": "shared-row",
                        "description": "מתוך blocks",
                        "location": "לובי",
                    }
                ],
            }
        ]
    }
    lines = [
        {
            "id": "shared-row",
            "description": "מתוך lines",
            "photo_ids": ["photo-1"],
            "issue_id": "fin-001",
        },
        {
            "id": "line-only",
            "description": "שורה מ-lines בלבד",
        },
    ]

    rows = collect_materializable_finding_rows(
        header_fields=header_fields,
        lines=lines,
    )

    by_id = {row.line_id: row for row in rows}
    assert set(by_id) == {"shared-row", "line-only"}
    assert by_id["shared-row"].description == "מתוך lines"
    assert by_id["shared-row"].catalog_issue_id == "FIN-001"
    assert by_id["shared-row"].photo_ids == ["photo-1"]
    assert by_id["line-only"].description == "שורה מ-lines בלבד"


def test_materialize_issues_from_report_creates_issues_with_detected_events() -> None:
    reports = FakeVisitReportRepository()
    lines = FakeVisitReportLineRepository()
    issues = InMemoryQualityIssueRepository()
    events = InMemoryQualityIssueEventRepository()

    reports.records["report-1"] = _closed_report(
        header_fields={
            "blocks": [
                {
                    "id": "findings-1",
                    "kind": "findings_table",
                    "title_he": "ממצאים",
                    "rows": [
                        {
                            "id": "row-a",
                            "description": "סדק בטיח",
                            "location": "קומה 2",
                            "trade": "טיח",
                        },
                        {
                            "id": "row-b",
                            "description": "איטום לקוי",
                            "location": "מרפסת",
                        },
                    ],
                }
            ]
        }
    )

    service = _materialization_service(
        reports=reports,
        lines=lines,
        issues=issues,
        events=events,
    )
    result = service.materialize_issues_from_report(
        organization_id="org-1",
        report_id="report-1",
        actor_id="profile-1",
    )

    assert isinstance(result, MaterializationResult)
    assert result.created_count == 2
    assert result.skipped_count == 0
    assert len(result.created_issue_ids) == 2
    assert len(issues.records) == 2

    first_issue = issues.records[result.created_issue_ids[0]]
    assert first_issue["status"] == QualityIssueStatus.OPEN.value
    assert first_issue["first_seen_report_id"] == "report-1"
    assert first_issue["materialization_key"].startswith("report-1:")
    assert first_issue["project_id"] == "project-1"

    detected_events = [
        event
        for event in events.records.values()
        if event["event_type"] == QualityIssueEventType.DETECTED.value
    ]
    assert len(detected_events) == 2


def test_materialize_issues_from_report_is_idempotent() -> None:
    reports = FakeVisitReportRepository()
    issues = InMemoryQualityIssueRepository()
    reports.records["report-1"] = _closed_report(
        header_fields={
            "blocks": [
                {
                    "id": "findings-1",
                    "kind": "findings_table",
                    "title_he": "ממצאים",
                    "rows": [
                        {"id": "row-a", "description": "ליקוי א"},
                        {"id": "row-b", "description": "ליקוי ב"},
                    ],
                }
            ]
        }
    )

    service = _materialization_service(reports=reports, issues=issues)

    first = service.materialize_issues_from_report(
        organization_id="org-1",
        report_id="report-1",
    )
    second = service.materialize_issues_from_report(
        organization_id="org-1",
        report_id="report-1",
    )

    assert first.created_count == 2
    assert second.created_count == 0
    assert second.skipped_count == 2
    assert len(issues.records) == 2


def test_materialize_issues_from_report_links_catalog_issue_and_photos() -> None:
    reports = FakeVisitReportRepository()
    lines = FakeVisitReportLineRepository()
    line_photos = FakeVisitReportLinePhotoRepository()
    issues = InMemoryQualityIssueRepository()

    reports.records["report-1"] = _closed_report()
    lines.create(
        {
            "report_id": "report-1",
            "sort_order": 0,
            "description": "נזילה בצנרת",
            "location": "דירה 5",
            "issue_id": "STR-001",
            "severity": "High",
        }
    )
    line_id = next(iter(lines.records))
    line_photos.create(
        {
            "line_id": line_id,
            "report_id": "report-1",
            "storage_path": "photos/1.jpg",
            "sort_order": 0,
        }
    )
    photo_id = next(iter(line_photos.records))

    service = _materialization_service(
        reports=reports,
        lines=lines,
        line_photos=line_photos,
        issues=issues,
    )
    result = service.materialize_issues_from_report(
        organization_id="org-1",
        report_id="report-1",
    )

    assert result.created_count == 1
    issue = issues.records[result.created_issue_ids[0]]
    assert issue["catalog_issue_id"] == "STR-001"
    assert issue["severity"] == "HIGH"
    assert issue["photo_ids"] == [photo_id]
    assert issue["materialization_key"] == f"report-1:{line_id}"


def test_materialize_issues_from_report_rejects_open_report() -> None:
    reports = FakeVisitReportRepository()
    reports.records["report-1"] = {
        "id": "report-1",
        "organization_id": "org-1",
        "project_id": "project-1",
        "status": "IN_PROGRESS",
        "header_fields": {},
    }

    service = _materialization_service(reports=reports)

    with pytest.raises(ValidationError, match="closed reports"):
        service.materialize_issues_from_report(
            organization_id="org-1",
            report_id="report-1",
        )


def test_materialize_issues_from_report_rejects_foreign_org() -> None:
    reports = FakeVisitReportRepository()
    reports.records["report-1"] = _closed_report(organization_id="org-1")

    service = _materialization_service(reports=reports)

    with pytest.raises(NotFoundError):
        service.materialize_issues_from_report(
            organization_id="org-other",
            report_id="report-1",
        )


def test_materialize_issues_from_report_uses_closed_at_for_first_seen() -> None:
    reports = FakeVisitReportRepository()
    issues = InMemoryQualityIssueRepository()
    closed_at = datetime(2026, 6, 9, 8, 30, tzinfo=UTC)

    reports.records["report-1"] = _closed_report(
        closed_at=closed_at.isoformat(),
        header_fields={
            "blocks": [
                {
                    "id": "findings-1",
                    "kind": "findings_table",
                    "title_he": "ממצאים",
                    "rows": [{"id": "row-a", "description": "ליקוי"}],
                }
            ]
        },
    )

    service = _materialization_service(reports=reports, issues=issues)
    result = service.materialize_issues_from_report(
        organization_id="org-1",
        report_id="report-1",
    )

    issue = issues.records[result.created_issue_ids[0]]
    assert datetime.fromisoformat(
        str(issue["first_seen_at"]).replace("Z", "+00:00")
    ) == closed_at
    assert datetime.fromisoformat(
        str(issue["last_seen_at"]).replace("Z", "+00:00")
    ) == closed_at


def _visit_service_with_materialization(
    *,
    reports: FakeVisitReportRepository,
    lines: FakeVisitReportLineRepository | None = None,
    line_photos: FakeVisitReportLinePhotoRepository | None = None,
    issues: InMemoryQualityIssueRepository,
    events: InMemoryQualityIssueEventRepository | None = None,
) -> FieldVisitReportService:
    materialization = QualityIssueMaterializationService(
        report_repository=reports,
        line_repository=lines or FakeVisitReportLineRepository(),
        line_photo_repository=line_photos or FakeVisitReportLinePhotoRepository(),
        issue_repository=issues,
        event_repository=events or InMemoryQualityIssueEventRepository(),
    )
    return FieldVisitReportService(
        report_repository=reports,
        line_repository=lines or FakeVisitReportLineRepository(),
        line_photo_repository=line_photos or FakeVisitReportLinePhotoRepository(),
        project_repository=FakeProjectRepository(),
        materialization_service=materialization,
    )


def test_close_report_materializes_five_findings_from_blocks() -> None:
    reports = FakeVisitReportRepository()
    issues = InMemoryQualityIssueRepository()
    events = InMemoryQualityIssueEventRepository()

    reports.records["report-1"] = {
        "id": "report-1",
        "organization_id": "org-1",
        "project_id": "project-1",
        "status": "IN_PROGRESS",
        "visit_type": "FINISHING_APARTMENTS",
        "visit_date": "2026-06-01",
        "created_by_profile_id": "profile-1",
        "header_fields": {
            "blocks": [
                {
                    "id": "findings-1",
                    "kind": "findings_table",
                    "title_he": "ממצאים",
                    "rows": [
                        {
                            "id": f"row-{index}",
                            "description": f"ליקוי {index}",
                            "location": f"דירה {index}",
                        }
                        for index in range(1, 6)
                    ],
                }
            ]
        },
    }

    service = _visit_service_with_materialization(
        reports=reports,
        issues=issues,
        events=events,
    )
    closed = service.close_report(
        organization_id="org-1",
        report_id="report-1",
        actor_id="profile-1",
    )

    assert closed["status"] == "CLOSED"
    assert closed["issue_materialization"]["created_count"] == 5
    assert closed["issue_materialization"]["skipped_count"] == 0
    assert len(issues.records) == 5
    assert len(
        [
            event
            for event in events.records.values()
            if event["event_type"] == QualityIssueEventType.DETECTED.value
        ]
    ) == 5


def test_close_report_materialization_is_idempotent_on_repeat() -> None:
    reports = FakeVisitReportRepository()
    lines = FakeVisitReportLineRepository()
    issues = InMemoryQualityIssueRepository()

    reports.records["report-1"] = {
        "id": "report-1",
        "organization_id": "org-1",
        "project_id": "project-1",
        "status": "IN_PROGRESS",
        "visit_type": "STRUCTURE_SITE",
        "visit_date": "2026-06-01",
        "created_by_profile_id": "profile-1",
        "header_fields": {},
    }
    lines.create(
        {
            "report_id": "report-1",
            "sort_order": 0,
            "description": "סדק בקיר",
        }
    )

    service = _visit_service_with_materialization(
        reports=reports,
        lines=lines,
        issues=issues,
    )

    first_close = service.close_report(
        organization_id="org-1",
        report_id="report-1",
    )
    assert first_close["issue_materialization"]["created_count"] == 1

    repeat = service.materialization_service.materialize_issues_from_report(
        organization_id="org-1",
        report_id="report-1",
    )
    assert repeat.created_count == 0
    assert repeat.skipped_count == 1
    assert len(issues.records) == 1


def test_materialize_links_existing_issue_when_line_has_linked_issue_id() -> None:
    lines = FakeVisitReportLineRepository()
    issues = InMemoryQualityIssueRepository()
    events = InMemoryQualityIssueEventRepository()
    reports = FakeVisitReportRepository()

    existing = issues.create(
        organization_id="org-1",
        project_id="project-1",
        request=qc_create_request(
            title="נזילה קיימת",
            location="דירה 3",
            trade="אינסטלציה",
            group_key="bath",
            materialization_key="report-0:line-0",
        ),
        status=QualityIssueStatus.OPEN.value,
    )

    reports.records["report-1"] = _closed_report(
        report_id="report-1",
        project_id="project-1",
    )
    line = lines.create(
        {
            "report_id": "report-1",
            "sort_order": 0,
            "description": "נזילה חוזרת",
            "location": "דירה 3",
            "trade": "אינסטלציה",
            "group_key": "bath",
            "linked_issue_id": existing["id"],
        }
    )

    service = _materialization_service(
        reports=reports,
        lines=lines,
        issues=issues,
        events=events,
    )
    result = service.materialize_issues_from_report(
        organization_id="org-1",
        report_id="report-1",
        actor_id="supervisor-1",
    )

    assert result.created_count == 0
    assert result.linked_count == 1
    assert result.linked_issue_ids == [existing["id"]]
    assert len(issues.records) == 1

    updated = issues.get_by_id(existing["id"])
    assert updated is not None
    assert updated["last_seen_report_id"] == "report-1"
    assert updated["last_seen_line_id"] == line["id"]

    linked_events = [
        event
        for event in events.records.values()
        if event["event_type"] == QualityIssueEventType.LINKED.value
    ]
    assert len(linked_events) == 1
    assert linked_events[0]["line_id"] == line["id"]
    assert linked_events[0]["payload"]["match_source"] == "manual"
