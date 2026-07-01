from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.auth.jwt_service import JWTService
from app.schemas.quality_issue import IssueVisibility, QualityIssueEventType
from app.services.field_report_finalize_registry import (
    INFRASTRUCTURE_PRE_STEP_ORDER,
)
from app.services.field_report_finalize_steps import (
    CORE_FINALIZE_STEP_ORDER,
    EXPECTED_CORE_FINALIZE_STEPS,
    FieldReportFinalizeSteps,
)
from tests.field_report_finalize_test_support import (
    StubFinalizeAiService,
    StubFinalizeEmailService,
    StubFinalizeNotificationsService,
)
from app.services.field_report_finalize_service import (
    FieldReportFinalizeService,
)
from app.services.field_report_module_service import (
    FieldReportModuleService,
)
from app.services.field_report_organization_profile_service import (
    FieldReportOrganizationProfileService,
)
from app.services.field_visit_report_pdf_service import (
    FieldVisitReportPdfService,
)
from app.services.field_visit_report_service import FieldVisitReportService
from app.services.notification_service import NotificationService
from app.services.quality_issue_materialization_service import (
    QualityIssueMaterializationService,
)
from app.services.resident_portal_service import ResidentPortalService
from app.services.workspace_activity_service import WorkspaceActivityService
from tests.quality_issues_test_support import (
    InMemoryQualityIssueEventRepository,
    InMemoryQualityIssueRepository,
)
from tests.test_field_report_finalize_f1_gate import (
    FakeFinalizeRunRepository,
    FAKE_PDF,
)
from tests.test_supervisor_project_scope import FakeProfileRepository
from tests.test_field_visit_reports import (
    FakeModuleRepository,
    FakeOrganizationRepository,
    FakeProjectRepository,
    FakeVisitReportLinePhotoRepository,
    FakeVisitReportLineRepository,
    FakeVisitReportRepository,
    _headers,
)


def _token(
    *,
    user_id: str = "supervisor-1",
    org_id: str = "org-1",
    role: str = "SUPERVISOR",
) -> str:
    return JWTService().issue_access_token(
        user_id=user_id,
        org_id=org_id,
        role=role,
        token_id="t-finalize-f2",
    )


class FinalizeProjectRepository(FakeProjectRepository):
    def get_project_by_id(self, project_id: str) -> dict | None:
        project = super().get_project_by_id(project_id)
        if project is None:
            return None
        return {
            **project,
            "supervisor_email": "supervisor@example.com",
        }


def _closed_report_with_line(
    *,
    report_id: str = "report-1",
    line_description: str = "סדק בקיר",
) -> tuple[
    FakeVisitReportRepository,
    FakeVisitReportLineRepository,
    InMemoryQualityIssueRepository,
    InMemoryQualityIssueEventRepository,
]:
    reports = FakeVisitReportRepository()
    lines = FakeVisitReportLineRepository()
    issues = InMemoryQualityIssueRepository()
    events = InMemoryQualityIssueEventRepository()

    reports.records[report_id] = {
        "id": report_id,
        "organization_id": "org-1",
        "project_id": "project-1",
        "status": "CLOSED",
        "visit_type": "STRUCTURE_SITE",
        "visit_date": "2026-06-01",
        "closed_at": "2026-06-09T10:00:00+00:00",
        "created_by_profile_id": "profile-1",
        "header_fields": {},
        "updated_at": "2026-06-09T10:00:00+00:00",
        "created_at": "2026-06-01T12:00:00+00:00",
    }
    lines.create(
        {
            "report_id": report_id,
            "organization_id": "org-1",
            "sort_order": 0,
            "description": line_description,
            "location": "דירה 3",
            "group_key": "apartment:3",
            "visibility": IssueVisibility.DRAFT.value,
        }
    )
    return reports, lines, issues, events

def _finalize_service(
    *,
    reports: FakeVisitReportRepository,
    lines: FakeVisitReportLineRepository,
    issues: InMemoryQualityIssueRepository,
    events: InMemoryQualityIssueEventRepository,
    runs: FakeFinalizeRunRepository | None = None,
    pdf_root: Path | None = None,
) -> FieldReportFinalizeService:
    materialization = QualityIssueMaterializationService(
        report_repository=reports,
        line_repository=lines,
        line_photo_repository=FakeVisitReportLinePhotoRepository(),
        issue_repository=issues,
        event_repository=events,
    )
    pdf_service = (
        FieldVisitReportPdfService(pdfs_root=pdf_root)
        if pdf_root is not None
        else FieldVisitReportPdfService()
    )
    visit_service = FieldVisitReportService(
        report_repository=reports,
        line_repository=lines,
        line_photo_repository=FakeVisitReportLinePhotoRepository(),
        project_repository=FinalizeProjectRepository(),
        materialization_service=materialization,
        pdf_service=pdf_service,
    )
    steps = FieldReportFinalizeSteps(
        visit_report_service=visit_service,
        profile_repository=FakeProfileRepository(
            {
                "supervisor-1": {
                    "id": "supervisor-1",
                    "email": "supervisor@example.com",
                }
            }
        ),
        notification_service=NotificationService(),
        workspace_activity_service=WorkspaceActivityService(),
        resident_portal_service=ResidentPortalService(
            line_repository=lines,
            issue_repository=issues,
            project_repository=FinalizeProjectRepository(),
        ),
    )
    return FieldReportFinalizeService(
        run_repository=runs or FakeFinalizeRunRepository(),
        report_repository=reports,
        visit_report_service=visit_service,
        steps=steps,
        notification_service=NotificationService(),
        workspace_activity_service=WorkspaceActivityService(),
        resident_portal_service=ResidentPortalService(
            line_repository=lines,
            issue_repository=issues,
            project_repository=FinalizeProjectRepository(),
        ),
        email_service=StubFinalizeEmailService(),
        notifications_service=StubFinalizeNotificationsService(),
        ai_service=StubFinalizeAiService(),
    )


def _setup_client(
    monkeypatch,
    *,
    finalize_service: FieldReportFinalizeService,
) -> TestClient:
    from app.main import app

    module_repository = FakeModuleRepository()
    module_repository.records["org-1"]["is_enabled"] = True

    module_service = FieldReportModuleService(
        module_repository=module_repository,
        organization_repository=FakeOrganizationRepository(),
    )

    monkeypatch.setattr(
        "app.dependencies.field_report_module_service",
        module_service,
    )
    monkeypatch.setattr(
        "app.dependencies.field_report_finalize_service",
        finalize_service,
    )
    monkeypatch.setattr(
        "app.dependencies.project_repository",
        FakeProjectRepository(),
    )

    app.state.field_report_module_service = module_service

    return TestClient(app)


def test_finalize_core_pipeline_marks_report_finalized_and_publishes_lines(
    tmp_path: Path,
) -> None:
    reports, lines, issues, events = _closed_report_with_line()
    runs = FakeFinalizeRunRepository()
    service = _finalize_service(
        reports=reports,
        lines=lines,
        issues=issues,
        events=events,
        runs=runs,
        pdf_root=tmp_path / "pdfs",
    )

    result = service.start_finalize(
        organization_id="org-1",
        report_id="report-1",
        actor_id="supervisor-1",
        source_content=FAKE_PDF,
        source_filename="visit.pdf",
    )

    assert result.finalize_run_id
    assert reports.records["report-1"]["status"] == "FINALIZED"
    assert reports.records["report-1"].get("pdf_storage_path")
    assert reports.records["report-1"].get("locked_at")

    published_line = lines.list_by_report("report-1")[0]
    assert published_line["visibility"] == IssueVisibility.PUBLISHED.value

    run = runs.records[result.finalize_run_id]
    assert run["status"] == "COMPLETED"
    assert EXPECTED_CORE_FINALIZE_STEPS <= set(run["steps_completed"])
    pre_len = len(INFRASTRUCTURE_PRE_STEP_ORDER)
    assert run["steps_completed"][
        pre_len : pre_len + len(CORE_FINALIZE_STEP_ORDER)
    ] == list(CORE_FINALIZE_STEP_ORDER)
    assert run["materialization"]["created_count"] == 1
    assert len(issues.records) == 1

    detected = [
        event
        for event in events.records.values()
        if event["event_type"] == QualityIssueEventType.DETECTED.value
    ]
    assert len(detected) == 1


def test_finalize_endpoint_runs_core_pipeline_e2e(
    monkeypatch,
    tmp_path: Path,
) -> None:
    reports, lines, issues, events = _closed_report_with_line()
    service = _finalize_service(
        reports=reports,
        lines=lines,
        issues=issues,
        events=events,
        pdf_root=tmp_path / "pdfs",
    )
    client = _setup_client(monkeypatch, finalize_service=service)

    response = client.post(
        "/field-reports/visits/report-1/finalize",
        headers=_headers(_token(role="SUPERVISOR")),
        files={"file": ("visit.pdf", FAKE_PDF, "application/pdf")},
    )
    assert response.status_code == 202

    status = client.get(
        "/field-reports/visits/report-1/finalize-status",
        headers=_headers(_token(role="SUPERVISOR")),
    )
    assert status.status_code == 200
    payload = status.json()
    assert payload["status"] == "FINALIZED"
    assert payload["finalize_run"]["status"] == "COMPLETED"
    assert EXPECTED_CORE_FINALIZE_STEPS <= set(
        payload["finalize_run"]["steps_completed"]
    )
    assert payload["finalize_run"]["materialization"]["created_count"] == 1


def test_finalize_idempotent_on_completed_report(
    monkeypatch,
    tmp_path: Path,
) -> None:
    reports, lines, issues, events = _closed_report_with_line()
    service = _finalize_service(
        reports=reports,
        lines=lines,
        issues=issues,
        events=events,
        pdf_root=tmp_path / "pdfs",
    )
    client = _setup_client(monkeypatch, finalize_service=service)
    headers = _headers(_token(role="SUPERVISOR"))
    files = {"file": ("visit.pdf", FAKE_PDF, "application/pdf")}

    first = client.post(
        "/field-reports/visits/report-1/finalize",
        headers=headers,
        files=files,
    )
    second = client.post(
        "/field-reports/visits/report-1/finalize",
        headers=headers,
        files=files,
    )

    assert first.status_code == 202
    assert second.status_code == 202
    assert first.json()["finalize_run_id"] == second.json()["finalize_run_id"]
    assert len(issues.records) == 1
