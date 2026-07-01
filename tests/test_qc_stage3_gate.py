"""Stage 3 gate validation (roadmap Gate שלב 3).

מפקח מסיים ביקור מהיר בשטח: צילום → שורת ממצא → סגירת דוח → ליקוי ב-registry.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.auth.jwt_service import JWTService
from app.main import app
from app.schemas.quality_issue import QualityIssueEventType
from app.services.field_visit_report_service import FieldVisitReportService
from app.services.quality_issue_materialization_service import (
    QualityIssueMaterializationService,
)
from app.services.quality_issue_service import QualityIssueService
from tests.quality_issues_test_support import (
    FakeProjectRepository,
    InMemoryQualityIssueEventRepository,
    InMemoryQualityIssueRepository,
)
from tests.test_field_visit_reports import (
    FakeVisitReportLinePhotoRepository,
    FakeVisitReportLineRepository,
    FakeVisitReportRepository,
)

QUICK_FINDING_DESCRIPTION = "ממצא מתמונה"


def _build_access_token(role: str = "SUPERVISOR") -> str:
    return JWTService().issue_access_token(
        user_id="supervisor-1",
        org_id="org-1",
        role=role,
        token_id="token-qc",
    )


def _auth_headers(role: str = "SUPERVISOR") -> dict[str, str]:
    return {
        "Authorization": f"Bearer {_build_access_token(role=role)}",
        "X-Organization-ID": "org-1",
    }


@pytest.fixture
def stage3_gate_setup(
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[
    TestClient,
    FieldVisitReportService,
    InMemoryQualityIssueRepository,
    InMemoryQualityIssueEventRepository,
    FakeVisitReportRepository,
    FakeVisitReportLineRepository,
    FakeVisitReportLinePhotoRepository,
]:
    issues = InMemoryQualityIssueRepository()
    events = InMemoryQualityIssueEventRepository()
    reports = FakeVisitReportRepository()
    lines = FakeVisitReportLineRepository()
    line_photos = FakeVisitReportLinePhotoRepository()
    projects = FakeProjectRepository()

    materialization = QualityIssueMaterializationService(
        report_repository=reports,
        line_repository=lines,
        line_photo_repository=line_photos,
        issue_repository=issues,
        event_repository=events,
    )
    visit_service = FieldVisitReportService(
        report_repository=reports,
        line_repository=lines,
        line_photo_repository=line_photos,
        project_repository=projects,
        materialization_service=materialization,
    )
    qc_service = QualityIssueService(
        issue_repository=issues,
        event_repository=events,
        project_repository=projects,
        report_repository=reports,
    )

    monkeypatch.setattr("app.dependencies.quality_issue_service", qc_service)
    monkeypatch.setattr("app.dependencies.field_visit_report_service", visit_service)

    return (
        TestClient(app),
        visit_service,
        issues,
        events,
        reports,
        lines,
        line_photos,
    )


def test_stage3_gate_quick_photo_line_close_materializes_issue_with_photo(
    stage3_gate_setup: tuple[
        TestClient,
        FieldVisitReportService,
        InMemoryQualityIssueRepository,
        InMemoryQualityIssueEventRepository,
        FakeVisitReportRepository,
        FakeVisitReportLineRepository,
        FakeVisitReportLinePhotoRepository,
    ],
) -> None:
    """צילום מהיר → שורה → סגירה → issue אחד עם תמונה."""
    client, visit_service, issues, events, reports, lines, line_photos = (
        stage3_gate_setup
    )

    reports.records["report-quick-field"] = {
        "id": "report-quick-field",
        "organization_id": "org-1",
        "project_id": "proj-1",
        "status": "IN_PROGRESS",
        "visit_type": "STRUCTURE_SITE",
        "visit_date": "2026-06-09",
        "created_by_profile_id": "profile-1",
        "header_fields": {},
    }

    quick_line = lines.create(
        {
            "report_id": "report-quick-field",
            "sort_order": 0,
            "description": QUICK_FINDING_DESCRIPTION,
            "location": "קומה 4",
            "group_key": "floor:4",
            "group_label_he": "קומה 4",
            "has_photo": True,
        }
    )
    line_photos.create(
        {
            "id": "photo-quick-1",
            "line_id": quick_line["id"],
            "report_id": "report-quick-field",
            "sort_order": 0,
            "storage_path": "photos/quick-1.jpg",
        }
    )

    closed = visit_service.close_report(
        organization_id="org-1",
        report_id="report-quick-field",
        actor_id="profile-1",
    )

    assert closed["status"] == "CLOSED"
    assert closed["issue_materialization"]["created_count"] == 0
    materialization = (
        visit_service.materialization_service.materialize_issues_from_report(
            organization_id="org-1",
            report_id="report-quick-field",
            actor_id="profile-1",
        )
    )
    assert materialization.created_count == 1
    assert materialization.linked_count == 0
    assert len(issues.records) == 1

    issue_id = next(iter(issues.records))
    issue = issues.get_by_id(issue_id)
    assert issue is not None
    assert issue["title"] == QUICK_FINDING_DESCRIPTION
    assert issue["description"] == QUICK_FINDING_DESCRIPTION
    assert issue["location"] == "קומה 4"
    assert issue["group_key"] == "floor:4"
    assert issue["first_seen_report_id"] == "report-quick-field"
    assert issue["first_seen_line_id"] == quick_line["id"]
    assert issue["photo_ids"] == ["photo-quick-1"]

    detected_events = [
        event
        for event in events.records.values()
        if event["issue_id"] == issue_id
        and event["event_type"] == QualityIssueEventType.DETECTED.value
    ]
    assert len(detected_events) == 1
    assert detected_events[0]["line_id"] == quick_line["id"]

    list_response = client.get(
        "/projects/proj-1/issues",
        headers=_auth_headers(),
    )
    assert list_response.status_code == 200
    body = list_response.json()
    assert body["total"] == 1
    assert body["items"][0]["title"] == QUICK_FINDING_DESCRIPTION
    assert body["items"][0]["photo_ids"] == ["photo-quick-1"]


def test_stage3_gate_close_is_idempotent_for_quick_field_visit(
    stage3_gate_setup: tuple[
        TestClient,
        FieldVisitReportService,
        InMemoryQualityIssueRepository,
        InMemoryQualityIssueEventRepository,
        FakeVisitReportRepository,
        FakeVisitReportLineRepository,
        FakeVisitReportLinePhotoRepository,
    ],
) -> None:
    _client, visit_service, issues, _events, reports, lines, line_photos = (
        stage3_gate_setup
    )

    reports.records["report-quick-idempotent"] = {
        "id": "report-quick-idempotent",
        "organization_id": "org-1",
        "project_id": "proj-1",
        "status": "IN_PROGRESS",
        "visit_type": "STRUCTURE_SITE",
        "visit_date": "2026-06-09",
        "created_by_profile_id": "profile-1",
        "header_fields": {},
    }
    quick_line = lines.create(
        {
            "report_id": "report-quick-idempotent",
            "sort_order": 0,
            "description": QUICK_FINDING_DESCRIPTION,
            "location": "דירה 12",
            "group_key": "apartment:12",
            "group_label_he": "דירה 12",
            "has_photo": True,
        }
    )
    line_photos.create(
        {
            "id": "photo-quick-idempotent",
            "line_id": quick_line["id"],
            "report_id": "report-quick-idempotent",
            "sort_order": 0,
            "storage_path": "photos/quick-idempotent.jpg",
        }
    )

    first_close = visit_service.close_report(
        organization_id="org-1",
        report_id="report-quick-idempotent",
        actor_id="profile-1",
    )
    assert first_close["issue_materialization"]["created_count"] == 0

    first_publish = (
        visit_service.materialization_service.materialize_issues_from_report(
            organization_id="org-1",
            report_id="report-quick-idempotent",
            actor_id="profile-1",
        )
    )
    assert first_publish.created_count == 1

    repeat = visit_service.materialization_service.materialize_issues_from_report(
        organization_id="org-1",
        report_id="report-quick-idempotent",
        actor_id="profile-1",
    )
    assert repeat.created_count == 0
    assert repeat.skipped_count == 1
    assert len(issues.records) == 1
