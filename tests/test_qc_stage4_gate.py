"""Stage 4 gate validation (roadmap Gate שלב 4).

1. Developer sees portfolio with projects highlighted by critical open issues
2. Contractor uploads remediation photo → supervisor approves on next visit
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.auth.jwt_service import JWTService
from app.main import app
from app.schemas.quality_issue import QualityIssueEventType
from app.services.quality_issue_photo_service import QualityIssuePhotoService
from app.services.quality_issue_service import QualityIssueService
from tests.quality_issues_test_support import (
    FakeProjectRepository,
    InMemoryQualityIssueEventRepository,
    InMemoryQualityIssuePhotoRepository,
    InMemoryQualityIssueRepository,
    qc_issue_payload,
    qc_published_issue_payload,
)
from tests.test_field_visit_reports import (
    FakeVisitReportLineRepository,
    FakeVisitReportRepository,
)


def _build_access_token(role: str = "SUPERVISOR") -> str:
    return JWTService().issue_access_token(
        user_id=f"{role.lower()}-1",
        org_id="org-1",
        role=role,
        token_id="token-qc-stage4-gate",
    )


def _auth_headers(role: str = "SUPERVISOR") -> dict[str, str]:
    return {
        "Authorization": f"Bearer {_build_access_token(role=role)}",
        "X-Organization-ID": "org-1",
    }


@pytest.fixture
def stage4_gate_setup(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> tuple[
    TestClient,
    QualityIssueService,
    InMemoryQualityIssueRepository,
    FakeVisitReportRepository,
    FakeVisitReportLineRepository,
]:
    issues = InMemoryQualityIssueRepository()
    events = InMemoryQualityIssueEventRepository()
    photo_repo = InMemoryQualityIssuePhotoRepository()
    reports = FakeVisitReportRepository()
    lines = FakeVisitReportLineRepository()
    projects = FakeProjectRepository(
        projects={
            "proj-1": {
                "id": "proj-1",
                "organization_id": "org-1",
                "project_name": "האורנים 7",
            },
            "proj-2": {
                "id": "proj-2",
                "organization_id": "org-1",
                "project_name": "פרויקט ב",
            },
        }
    )
    service = QualityIssueService(
        issue_repository=issues,
        event_repository=events,
        project_repository=projects,
        photo_repository=photo_repo,
        photo_service=QualityIssuePhotoService(photos_root=tmp_path),
        report_repository=reports,
    )
    monkeypatch.setattr("app.dependencies.quality_issue_service", service)
    return TestClient(app), service, issues, reports, lines


def test_stage4_gate_developer_sees_critical_projects_in_portfolio(
    stage4_gate_setup: tuple[
        TestClient,
        QualityIssueService,
        InMemoryQualityIssueRepository,
        FakeVisitReportRepository,
        FakeVisitReportLineRepository,
    ],
) -> None:
    client, _service, _issues, _reports, _lines = stage4_gate_setup
    supervisor_headers = _auth_headers("SUPERVISOR")
    developer_headers = _auth_headers("DEVELOPER")

    client.post(
        "/projects/proj-1/issues",
        headers=supervisor_headers,
        json=qc_published_issue_payload(
            title="נזילה קריטית",
            severity="CRITICAL",
            materialization_key="gate4-proj1-critical",
        ),
    )
    client.post(
        "/projects/proj-2/issues",
        headers=supervisor_headers,
        json=qc_published_issue_payload(
            title="ליקוי בינוני",
            severity="MEDIUM",
            materialization_key="gate4-proj2-medium",
        ),
    )

    summary = client.get(
        "/portfolio/quality-summary",
        headers=developer_headers,
    )
    assert summary.status_code == 200
    body = summary.json()
    assert body["total_open"] == 2
    assert body["total_open_critical"] == 1

    ranked = body["projects"]
    assert len(ranked) >= 2
    proj_one = next(
        project for project in ranked if project["project_id"] == "proj-1"
    )
    proj_two = next(
        project for project in ranked if project["project_id"] == "proj-2"
    )
    assert proj_one["open_critical"] == 1
    assert proj_two["open_critical"] == 0

    assert ranked[0]["project_id"] == "proj-1"
    assert ranked[0]["open_critical"] >= ranked[1]["open_critical"]

    contractor_summary = client.get(
        "/portfolio/quality-summary",
        headers=_auth_headers("CONTRACTOR"),
    )
    assert contractor_summary.status_code == 403


def test_stage4_gate_contractor_photo_supervisor_approves_on_visit_two(
    stage4_gate_setup: tuple[
        TestClient,
        QualityIssueService,
        InMemoryQualityIssueRepository,
        FakeVisitReportRepository,
        FakeVisitReportLineRepository,
    ],
) -> None:
    client, _service, issues, reports, lines = stage4_gate_setup
    supervisor_headers = _auth_headers("SUPERVISOR")
    contractor_headers = _auth_headers("CONTRACTOR")
    developer_headers = _auth_headers("DEVELOPER")

    created = client.post(
        "/projects/proj-1/issues",
        headers=supervisor_headers,
        json=qc_issue_payload(
            title="סדק בקיר",
            materialization_key="gate4-remediation-1",
        ),
    ).json()
    issue_id = created["id"]

    client.patch(
        f"/issues/{issue_id}",
        headers=supervisor_headers,
        json={"status": "IN_REMEDIATION"},
    )

    upload = client.post(
        f"/issues/{issue_id}/photos",
        headers=contractor_headers,
        files={
            "file": ("remediation.jpg", b"fake-jpeg-bytes", "image/jpeg"),
        },
    )
    assert upload.status_code == 200
    photo_id = upload.json()["photo_id"]

    pending = client.patch(
        f"/issues/{issue_id}",
        headers=contractor_headers,
        json={
            "status": "PENDING_VERIFICATION",
            "notes": "בוצע תיקון",
            "photo_ids": [photo_id],
        },
    )
    assert pending.status_code == 200
    assert pending.json()["status"] == "PENDING_VERIFICATION"

    contractor_open = client.get(
        "/projects/proj-1/issues/open",
        headers=contractor_headers,
    ).json()
    assert contractor_open["total"] == 0

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

    closed = client.patch(
        f"/issues/{issue_id}",
        headers=supervisor_headers,
        json={
            "status": "CLOSED",
            "last_seen_report_id": "report-visit-2",
            "last_seen_line_id": visit_two_line["id"],
        },
    )
    assert closed.status_code == 200
    closed_body = closed.json()
    assert closed_body["status"] == "CLOSED"
    assert closed_body["last_seen_report_id"] == "report-visit-2"
    assert closed_body["last_seen_line_id"] == visit_two_line["id"]

    diff = client.get(
        "/projects/proj-1/visits/report-visit-2/issue-diff",
        headers=supervisor_headers,
    )
    assert diff.status_code == 200
    diff_body = diff.json()
    assert diff_body["total_closed"] == 1
    assert diff_body["closed"][0]["issue"]["id"] == issue_id

    summary = client.get(
        "/portfolio/quality-summary",
        headers=developer_headers,
    ).json()
    assert summary["total_open"] == 0
    proj_one = next(
        project
        for project in summary["projects"]
        if project["project_id"] == "proj-1"
    )
    assert proj_one["open_total"] == 0
    assert proj_one["open_critical"] == 0

    detail = client.get(
        f"/issues/{issue_id}",
        headers=supervisor_headers,
    ).json()
    event_types = [event["event_type"] for event in detail["events"]]
    assert "REMEDIATION_SUBMITTED" in event_types
    assert event_types.count(QualityIssueEventType.VERIFIED_CLOSED.value) == 1

    verified = next(
        event
        for event in detail["events"]
        if event["event_type"] == QualityIssueEventType.VERIFIED_CLOSED.value
    )
    assert verified["report_id"] == "report-visit-2"
    assert verified["line_id"] == visit_two_line["id"]
    assert verified["payload"]["from_status"] == "PENDING_VERIFICATION"

    stored = issues.get_by_id(issue_id)
    assert stored is not None
    assert stored["status"] == "CLOSED"
    assert photo_id in stored.get("photo_ids", [])
