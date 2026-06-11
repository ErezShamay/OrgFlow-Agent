"""Stage 1 gate validation (roadmap Gate שלב 1).

1. Close report with 5 findings → 5 issues in project
2. Issue list exposes photo_ids from the report
3. Portfolio quality-summary shows open / critical / average days KPIs
"""

from __future__ import annotations

from datetime import timedelta

import pytest
from fastapi.testclient import TestClient

from app.auth.jwt_service import JWTService
from app.main import app
from app.services.field_visit_report_service import FieldVisitReportService
from app.services.quality_issue_materialization_service import (
    QualityIssueMaterializationService,
)
from app.services.quality_issue_service import QualityIssueService
from tests.quality_issues_test_support import (
    FakeProjectRepository,
    InMemoryQualityIssueEventRepository,
    InMemoryQualityIssueRepository,
    qc_create_request,
    qc_now,
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
def stage1_gate_setup(
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[
    TestClient,
    FieldVisitReportService,
    InMemoryQualityIssueRepository,
    FakeVisitReportRepository,
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

    return TestClient(app), visit_service, issues, reports


def test_stage1_gate_close_report_materializes_five_issues_with_photos(
    stage1_gate_setup: tuple[
        TestClient,
        FieldVisitReportService,
        InMemoryQualityIssueRepository,
        FakeVisitReportRepository,
    ],
) -> None:
    client, visit_service, issues, reports = stage1_gate_setup

    reports.records["report-gate"] = {
        "id": "report-gate",
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
                            "id": f"row-{index}",
                            "description": f"ליקוי {index}",
                            "location": f"דירה {index}",
                            "severity": "Critical" if index == 1 else "Medium",
                            "photo_ids": [f"photo-{index}"],
                        }
                        for index in range(1, 6)
                    ],
                }
            ]
        },
    }

    closed = visit_service.close_report(
        organization_id="org-1",
        report_id="report-gate",
        actor_id="profile-1",
    )

    assert closed["status"] == "CLOSED"
    assert closed["issue_materialization"]["created_count"] == 5
    assert len(issues.records) == 5

    list_response = client.get(
        "/projects/proj-1/issues",
        headers=_auth_headers(),
    )
    assert list_response.status_code == 200
    body = list_response.json()
    assert body["total"] == 5
    assert len(body["items"]) == 5

    photo_counts = [len(item["photo_ids"]) for item in body["items"]]
    assert photo_counts == [1, 1, 1, 1, 1]
    assert all(item["photo_ids"][0].startswith("photo-") for item in body["items"])


def test_stage1_gate_portfolio_quality_summary_kpis(
    stage1_gate_setup: tuple[
        TestClient,
        FieldVisitReportService,
        InMemoryQualityIssueRepository,
        FakeVisitReportRepository,
    ],
) -> None:
    client, _visit_service, issues, _reports = stage1_gate_setup
    now = qc_now()

    issues.create(
        organization_id="org-1",
        project_id="proj-1",
        request=qc_create_request(
            title="קריטי",
            severity="CRITICAL",
            materialization_key="gate-critical",
            first_seen_at=now - timedelta(days=10),
        ),
    )
    issues.create(
        organization_id="org-1",
        project_id="proj-1",
        request=qc_create_request(
            title="גבוה",
            severity="HIGH",
            materialization_key="gate-high",
            first_seen_at=now - timedelta(days=4),
        ),
    )
    issues.create(
        organization_id="org-1",
        project_id="proj-1",
        request=qc_create_request(
            title="סגור",
            severity="MEDIUM",
            materialization_key="gate-closed",
            first_seen_at=now - timedelta(days=20),
        ),
        status="CLOSED",
    )
    closed_issue_id = next(
        issue_id
        for issue_id, record in issues.records.items()
        if record["materialization_key"] == "gate-closed"
    )
    issues.update(
        closed_issue_id,
        {"closed_at": (now - timedelta(days=2)).isoformat()},
    )

    summary_response = client.get(
        "/portfolio/quality-summary",
        headers=_auth_headers("DEVELOPER"),
    )
    assert summary_response.status_code == 200
    summary = summary_response.json()

    assert summary["total_open"] == 2
    assert summary["total_open_critical"] == 1
    assert summary["average_open_days"] == 7.0
    assert summary["projects"][0]["project_id"] == "proj-1"
    assert summary["projects"][0]["open_total"] == 2
    assert summary["projects"][0]["open_critical"] == 1
