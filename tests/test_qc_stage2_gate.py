"""Stage 2 gate validation (roadmap Gate שלב 2).

1. Visit 2 links issue from visit 1 (no duplicates)
2. Closing a linked issue in visit 2 updates the registry
3. Recurring issue is marked REOPENED
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
def stage2_gate_setup(
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[
    TestClient,
    FieldVisitReportService,
    InMemoryQualityIssueRepository,
    InMemoryQualityIssueEventRepository,
    FakeVisitReportRepository,
    FakeVisitReportLineRepository,
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

    monkeypatch.setattr("app.main.quality_issue_service", qc_service)
    monkeypatch.setattr("app.main.field_visit_report_service", visit_service)

    return (
        TestClient(app),
        visit_service,
        issues,
        events,
        reports,
        lines,
    )


def test_stage2_gate_visit_two_links_visit_one_issue_without_duplicates(
    stage2_gate_setup: tuple[
        TestClient,
        FieldVisitReportService,
        InMemoryQualityIssueRepository,
        InMemoryQualityIssueEventRepository,
        FakeVisitReportRepository,
        FakeVisitReportLineRepository,
    ],
) -> None:
    client, visit_service, issues, events, reports, lines = stage2_gate_setup

    reports.records["report-visit-1"] = {
        "id": "report-visit-1",
        "organization_id": "org-1",
        "project_id": "proj-1",
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
                            "id": "row-v1",
                            "description": "נזילה בחדר רחצה",
                            "location": "דירה 3",
                            "trade": "אינסטלציה",
                            "group_key": "bath",
                        }
                    ],
                }
            ]
        },
    }

    visit_one_close = visit_service.close_report(
        organization_id="org-1",
        report_id="report-visit-1",
        actor_id="profile-1",
    )
    assert visit_one_close["issue_materialization"]["created_count"] == 1
    assert visit_one_close["issue_materialization"]["linked_count"] == 0
    assert len(issues.records) == 1

    issue_id = next(iter(issues.records))
    issue_after_visit_one = issues.get_by_id(issue_id)
    assert issue_after_visit_one is not None
    assert issue_after_visit_one["first_seen_report_id"] == "report-visit-1"
    assert issue_after_visit_one["last_seen_report_id"] == "report-visit-1"

    list_after_visit_one = client.get(
        "/projects/proj-1/issues",
        headers=_auth_headers(),
    )
    assert list_after_visit_one.status_code == 200
    assert list_after_visit_one.json()["total"] == 1

    reports.records["report-visit-2"] = {
        "id": "report-visit-2",
        "organization_id": "org-1",
        "project_id": "proj-1",
        "status": "IN_PROGRESS",
        "visit_type": "FINISHING_APARTMENTS",
        "visit_date": "2026-06-08",
        "created_by_profile_id": "profile-1",
        "header_fields": {},
    }
    visit_two_line = lines.create(
        {
            "report_id": "report-visit-2",
            "sort_order": 0,
            "description": "נזילה חוזרת",
            "location": "דירה 3",
            "trade": "אינסטלציה",
            "group_key": "bath",
            "linked_issue_id": issue_id,
        }
    )

    visit_two_close = visit_service.close_report(
        organization_id="org-1",
        report_id="report-visit-2",
        actor_id="profile-1",
    )
    materialization = visit_two_close["issue_materialization"]
    assert materialization["created_count"] == 0
    assert materialization["linked_count"] == 1
    assert materialization["linked_issue_ids"] == [issue_id]
    assert len(issues.records) == 1

    issue_after_visit_two = issues.get_by_id(issue_id)
    assert issue_after_visit_two is not None
    assert issue_after_visit_two["first_seen_report_id"] == "report-visit-1"
    assert issue_after_visit_two["last_seen_report_id"] == "report-visit-2"
    assert issue_after_visit_two["last_seen_line_id"] == visit_two_line["id"]

    linked_events = [
        event
        for event in events.records.values()
        if event["event_type"] == QualityIssueEventType.LINKED.value
    ]
    assert len(linked_events) == 1
    assert linked_events[0]["issue_id"] == issue_id
    assert linked_events[0]["report_id"] == "report-visit-2"
    assert linked_events[0]["line_id"] == visit_two_line["id"]
    assert linked_events[0]["payload"]["match_source"] == "manual"

    list_after_visit_two = client.get(
        "/projects/proj-1/issues",
        headers=_auth_headers(),
    )
    assert list_after_visit_two.status_code == 200
    assert list_after_visit_two.json()["total"] == 1

    detail = client.get(
        f"/issues/{issue_id}",
        headers=_auth_headers(),
    )
    assert detail.status_code == 200
    detail_body = detail.json()
    assert detail_body["issue"]["id"] == issue_id
    event_types = [event["event_type"] for event in detail_body["events"]]
    assert event_types.count(QualityIssueEventType.DETECTED.value) == 1
    assert event_types.count(QualityIssueEventType.LINKED.value) == 1

    repeat = visit_service.materialization_service.materialize_issues_from_report(
        organization_id="org-1",
        report_id="report-visit-2",
        actor_id="profile-1",
    )
    assert repeat.created_count == 0
    assert repeat.linked_count == 1
    assert len(issues.records) == 1


def test_stage2_gate_visit_two_closes_linked_issue_updates_registry(
    stage2_gate_setup: tuple[
        TestClient,
        FieldVisitReportService,
        InMemoryQualityIssueRepository,
        InMemoryQualityIssueEventRepository,
        FakeVisitReportRepository,
        FakeVisitReportLineRepository,
    ],
) -> None:
    client, visit_service, issues, events, reports, lines = stage2_gate_setup

    reports.records["report-visit-1"] = {
        "id": "report-visit-1",
        "organization_id": "org-1",
        "project_id": "proj-1",
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
                            "id": "row-v1",
                            "description": "סדק בקיר",
                            "location": "דירה 5",
                            "trade": "טיח",
                        }
                    ],
                }
            ]
        },
    }

    visit_service.close_report(
        organization_id="org-1",
        report_id="report-visit-1",
        actor_id="profile-1",
    )
    issue_id = next(iter(issues.records))

    open_before_visit_two = client.get(
        "/projects/proj-1/issues/open",
        headers=_auth_headers(),
    )
    assert open_before_visit_two.status_code == 200
    assert open_before_visit_two.json()["total"] == 1

    reports.records["report-visit-2"] = {
        "id": "report-visit-2",
        "organization_id": "org-1",
        "project_id": "proj-1",
        "status": "IN_PROGRESS",
        "visit_type": "FINISHING_APARTMENTS",
        "visit_date": "2026-06-08",
        "created_by_profile_id": "profile-1",
        "header_fields": {},
    }
    visit_two_line = lines.create(
        {
            "report_id": "report-visit-2",
            "sort_order": 0,
            "description": "תוקן - אין סדק",
            "location": "דירה 5",
            "trade": "טיח",
            "linked_issue_id": issue_id,
        }
    )

    visit_service.close_report(
        organization_id="org-1",
        report_id="report-visit-2",
        actor_id="profile-1",
    )

    closed = client.patch(
        f"/issues/{issue_id}",
        headers=_auth_headers(),
        json={
            "status": "CLOSED",
            "last_seen_report_id": "report-visit-2",
            "last_seen_line_id": visit_two_line["id"],
        },
    )
    assert closed.status_code == 200
    closed_body = closed.json()
    assert closed_body["status"] == "CLOSED"
    assert closed_body["closed_by"] == "supervisor-1"
    assert closed_body["closed_at"] is not None
    assert closed_body["last_seen_report_id"] == "report-visit-2"
    assert closed_body["last_seen_line_id"] == visit_two_line["id"]

    open_after_close = client.get(
        "/projects/proj-1/issues/open",
        headers=_auth_headers(),
    )
    assert open_after_close.status_code == 200
    assert open_after_close.json()["total"] == 0

    summary = client.get(
        "/portfolio/quality-summary",
        headers=_auth_headers("DEVELOPER"),
    )
    assert summary.status_code == 200
    assert summary.json()["total_open"] == 0

    detail = client.get(
        f"/issues/{issue_id}",
        headers=_auth_headers(),
    )
    assert detail.status_code == 200
    detail_body = detail.json()
    assert detail_body["issue"]["status"] == "CLOSED"
    event_types = [event["event_type"] for event in detail_body["events"]]
    assert event_types.count(QualityIssueEventType.DETECTED.value) == 1
    assert event_types.count(QualityIssueEventType.LINKED.value) == 1
    assert event_types.count(QualityIssueEventType.VERIFIED_CLOSED.value) == 1

    verified = next(
        event
        for event in detail_body["events"]
        if event["event_type"] == QualityIssueEventType.VERIFIED_CLOSED.value
    )
    assert verified["report_id"] == "report-visit-2"
    assert verified["line_id"] == visit_two_line["id"]
    assert verified["payload"]["from_status"] == "OPEN"
    assert verified["payload"]["to_status"] == "CLOSED"
    assert verified["actor_id"] == "supervisor-1"

    diff = client.get(
        "/projects/proj-1/visits/report-visit-2/issue-diff",
        headers=_auth_headers(),
    )
    assert diff.status_code == 200
    diff_body = diff.json()
    assert diff_body["total_closed"] == 1
    assert diff_body["total_still_open"] == 0
    assert diff_body["total_new"] == 0
    assert {item["issue"]["id"] for item in diff_body["closed"]} == {issue_id}
    assert diff_body["closed"][0]["line_id"] == visit_two_line["id"]

    stored = issues.get_by_id(issue_id)
    assert stored is not None
    assert stored["status"] == "CLOSED"
    assert stored["closed_by"] == "supervisor-1"
    assert stored["closed_at"] is not None

    verified_events = [
        event
        for event in events.records.values()
        if event["event_type"] == QualityIssueEventType.VERIFIED_CLOSED.value
    ]
    assert len(verified_events) == 1
    assert verified_events[0]["issue_id"] == issue_id


def test_stage2_gate_recurring_issue_marked_reopened_in_visit_three(
    stage2_gate_setup: tuple[
        TestClient,
        FieldVisitReportService,
        InMemoryQualityIssueRepository,
        InMemoryQualityIssueEventRepository,
        FakeVisitReportRepository,
        FakeVisitReportLineRepository,
    ],
) -> None:
    client, visit_service, issues, events, reports, lines = stage2_gate_setup

    reports.records["report-visit-1"] = {
        "id": "report-visit-1",
        "organization_id": "org-1",
        "project_id": "proj-1",
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
                            "id": "row-v1",
                            "description": "רטיבות בקיר",
                            "location": "דירה 7",
                            "trade": "איטום",
                        }
                    ],
                }
            ]
        },
    }

    visit_service.close_report(
        organization_id="org-1",
        report_id="report-visit-1",
        actor_id="profile-1",
    )
    issue_id = next(iter(issues.records))

    reports.records["report-visit-2"] = {
        "id": "report-visit-2",
        "organization_id": "org-1",
        "project_id": "proj-1",
        "status": "IN_PROGRESS",
        "visit_type": "FINISHING_APARTMENTS",
        "visit_date": "2026-06-08",
        "created_by_profile_id": "profile-1",
        "header_fields": {},
    }
    visit_two_line = lines.create(
        {
            "report_id": "report-visit-2",
            "sort_order": 0,
            "description": "תוקן",
            "location": "דירה 7",
            "trade": "איטום",
            "linked_issue_id": issue_id,
        }
    )

    visit_service.close_report(
        organization_id="org-1",
        report_id="report-visit-2",
        actor_id="profile-1",
    )
    client.patch(
        f"/issues/{issue_id}",
        headers=_auth_headers(),
        json={
            "status": "CLOSED",
            "last_seen_report_id": "report-visit-2",
            "last_seen_line_id": visit_two_line["id"],
        },
    )

    closed_issue = issues.get_by_id(issue_id)
    assert closed_issue is not None
    assert closed_issue["status"] == "CLOSED"
    assert closed_issue["recurrence_count"] == 0

    reports.records["report-visit-3"] = {
        "id": "report-visit-3",
        "organization_id": "org-1",
        "project_id": "proj-1",
        "status": "IN_PROGRESS",
        "visit_type": "FINISHING_APARTMENTS",
        "visit_date": "2026-06-15",
        "created_by_profile_id": "profile-1",
        "header_fields": {},
    }
    visit_three_line = lines.create(
        {
            "report_id": "report-visit-3",
            "sort_order": 0,
            "description": "רטיבות חזרה",
            "location": "דירה 7",
            "trade": "איטום",
            "linked_issue_id": issue_id,
        }
    )

    visit_service.close_report(
        organization_id="org-1",
        report_id="report-visit-3",
        actor_id="profile-1",
    )

    reopened = client.patch(
        f"/issues/{issue_id}",
        headers=_auth_headers(),
        json={
            "status": "REOPENED",
            "last_seen_report_id": "report-visit-3",
            "last_seen_line_id": visit_three_line["id"],
        },
    )
    assert reopened.status_code == 200
    reopened_body = reopened.json()
    assert reopened_body["status"] == "REOPENED"
    assert reopened_body["recurrence_count"] == 1
    assert reopened_body["closed_at"] is None
    assert reopened_body["closed_by"] is None
    assert reopened_body["last_seen_report_id"] == "report-visit-3"
    assert reopened_body["last_seen_line_id"] == visit_three_line["id"]

    open_after_reopen = client.get(
        "/projects/proj-1/issues/open",
        headers=_auth_headers(),
    )
    assert open_after_reopen.status_code == 200
    open_body = open_after_reopen.json()
    assert open_body["total"] == 1
    assert open_body["items"][0]["id"] == issue_id
    assert open_body["items"][0]["status"] == "REOPENED"

    summary = client.get(
        "/portfolio/quality-summary",
        headers=_auth_headers("DEVELOPER"),
    )
    assert summary.status_code == 200
    assert summary.json()["total_open"] == 1

    detail = client.get(
        f"/issues/{issue_id}",
        headers=_auth_headers(),
    )
    assert detail.status_code == 200
    detail_body = detail.json()
    event_types = [event["event_type"] for event in detail_body["events"]]
    assert event_types.count(QualityIssueEventType.REOPENED.value) == 1

    reopened_event = next(
        event
        for event in detail_body["events"]
        if event["event_type"] == QualityIssueEventType.REOPENED.value
    )
    assert reopened_event["report_id"] == "report-visit-3"
    assert reopened_event["line_id"] == visit_three_line["id"]
    assert reopened_event["payload"]["from_status"] == "CLOSED"
    assert reopened_event["payload"]["to_status"] == "REOPENED"
    assert reopened_event["payload"]["recurrence_count"] == 1
    assert reopened_event["actor_id"] == "supervisor-1"

    diff = client.get(
        "/projects/proj-1/visits/report-visit-3/issue-diff",
        headers=_auth_headers(),
    )
    assert diff.status_code == 200
    diff_body = diff.json()
    assert diff_body["total_recurring"] == 1
    assert diff_body["total_closed"] == 0
    assert diff_body["total_still_open"] == 0
    assert {item["issue"]["id"] for item in diff_body["recurring"]} == {issue_id}
    assert diff_body["recurring"][0]["issue"]["status"] == "REOPENED"
    assert diff_body["recurring"][0]["line_id"] == visit_three_line["id"]

    stored = issues.get_by_id(issue_id)
    assert stored is not None
    assert stored["status"] == "REOPENED"
    assert stored["recurrence_count"] == 1

    reopened_events = [
        event
        for event in events.records.values()
        if event["event_type"] == QualityIssueEventType.REOPENED.value
    ]
    assert len(reopened_events) == 1
    assert reopened_events[0]["issue_id"] == issue_id
