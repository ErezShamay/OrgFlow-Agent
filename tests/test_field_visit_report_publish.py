from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.auth.jwt_service import JWTService
from app.schemas.quality_issue import IssueVisibility, QualityIssueEventType
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
from app.services.quality_issue_materialization_service import (
    QualityIssueMaterializationService,
)
from app.services.resident_portal_service import ResidentPortalService
from tests.quality_issues_test_support import (
    InMemoryQualityIssueEventRepository,
    InMemoryQualityIssueRepository,
)
from tests.test_field_visit_reports import (
    FakeModuleRepository,
    FakeOrganizationRepository,
    FakeProjectRepository,
    FakeReportProcessingService,
    FakeVisitReportLinePhotoRepository,
    FakeVisitReportLineRepository,
    FakeVisitReportRepository,
    _headers,
)

FAKE_PDF = b"%PDF-1.4\npublished-report\n%%EOF\n"


def _token(
    *,
    user_id: str = "admin-1",
    org_id: str = "org-1",
    role: str = "ADMIN",
) -> str:
    return JWTService().issue_access_token(
        user_id=user_id,
        org_id=org_id,
        role=role,
        token_id="t-publish-1",
    )


def _publish_service(
    *,
    reports: FakeVisitReportRepository | None = None,
    lines: FakeVisitReportLineRepository | None = None,
    issues: InMemoryQualityIssueRepository | None = None,
    events: InMemoryQualityIssueEventRepository | None = None,
    pdf_root: Path | None = None,
) -> FieldVisitReportService:
    report_repository = reports or FakeVisitReportRepository()
    line_repository = lines or FakeVisitReportLineRepository()
    issue_repository = issues or InMemoryQualityIssueRepository()
    event_repository = events or InMemoryQualityIssueEventRepository()
    materialization = QualityIssueMaterializationService(
        report_repository=report_repository,
        line_repository=line_repository,
        line_photo_repository=FakeVisitReportLinePhotoRepository(),
        issue_repository=issue_repository,
        event_repository=event_repository,
    )
    pdf_service = (
        FieldVisitReportPdfService(pdfs_root=pdf_root)
        if pdf_root is not None
        else FieldVisitReportPdfService()
    )
    return FieldVisitReportService(
        report_repository=report_repository,
        line_repository=line_repository,
        line_photo_repository=FakeVisitReportLinePhotoRepository(),
        project_repository=FakeProjectRepository(),
        materialization_service=materialization,
        pdf_service=pdf_service,
    )


def _setup_client(
    monkeypatch,
    *,
    visit_service: FieldVisitReportService,
    module_enabled: bool = True,
) -> TestClient:
    from app.main import app

    module_repository = FakeModuleRepository()
    module_repository.records["org-1"]["is_enabled"] = module_enabled

    module_service = FieldReportModuleService(
        module_repository=module_repository,
        organization_repository=FakeOrganizationRepository(),
    )
    organization_profile_service = FieldReportOrganizationProfileService(
        organization_repository=FakeOrganizationRepository(),
        module_service=module_service,
    )

    monkeypatch.setattr(
        "app.dependencies.field_report_module_service",
        module_service,
    )
    monkeypatch.setattr(
        "app.dependencies.field_visit_report_service",
        visit_service,
    )
    monkeypatch.setattr(
        "app.dependencies.project_repository",
        FakeProjectRepository(),
    )

    app.state.field_report_module_service = module_service

    return TestClient(app)


def _closed_report_with_line(
    *,
    report_id: str = "report-1",
    line_description: str = "סדק בקיר",
) -> tuple[FakeVisitReportRepository, FakeVisitReportLineRepository]:
    reports = FakeVisitReportRepository()
    lines = FakeVisitReportLineRepository()

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
    }
    line = lines.create(
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
    _ = line
    return reports, lines


def test_publish_report_materializes_issues_and_publishes_lines(
    tmp_path: Path,
) -> None:
    reports, lines = _closed_report_with_line()
    issues = InMemoryQualityIssueRepository()
    events = InMemoryQualityIssueEventRepository()
    service = _publish_service(
        reports=reports,
        lines=lines,
        issues=issues,
        events=events,
        pdf_root=tmp_path / "pdfs",
    )

    result = service.publish_report(
        organization_id="org-1",
        report_id="report-1",
        actor_id="admin-1",
        source_filename="visit.pdf",
        source_content=FAKE_PDF,
    )

    assert result["is_published"] is True
    assert result["can_publish"] is False
    assert result["publish_result"]["published_line_count"] == 1
    assert result["publish_result"]["issue_materialization"]["created_count"] == 1
    assert result["publish_result"]["pdf_archived"] is True
    assert len(issues.records) == 1

    published_line = lines.list_by_report("report-1")[0]
    assert published_line["visibility"] == IssueVisibility.PUBLISHED.value

    detected = [
        event
        for event in events.records.values()
        if event["event_type"] == QualityIssueEventType.DETECTED.value
    ]
    assert len(detected) == 1


def test_publish_report_archives_pdf_and_appears_in_deliverables(
    tmp_path: Path,
) -> None:
    from datetime import date

    from app.services.deliverable_reports_service import DeliverableReportsService

    reports, lines = _closed_report_with_line()
    reports.records["report-1"]["closed_at"] = "2026-06-11T09:00:00+00:00"
    service = _publish_service(
        reports=reports,
        lines=lines,
        pdf_root=tmp_path / "pdfs",
    )

    service.publish_report(
        organization_id="org-1",
        report_id="report-1",
        actor_id="admin-1",
        source_filename="published-visit.pdf",
        source_content=FAKE_PDF,
    )

    archived = reports.records["report-1"]
    assert archived.get("pdf_storage_path")
    assert archived.get("pdf_filename")

    class PublishedOnlyRepository(FakeVisitReportRepository):
        def list_pdf_deliverables_by_organization(self, organization_id: str):
            return [archived]

    deliverables = DeliverableReportsService(
        project_repository=FakeProjectRepository(),
        field_visit_report_repository=PublishedOnlyRepository(),
        weekly_report_repository=MagicMock(
            list_by_project_ids=MagicMock(return_value=[])
        ),
    )
    dashboard = deliverables.get_dashboard(
        organization_id="org-1",
        actor_role="ADMIN",
        period_start=date(2026, 6, 1),
        period_end=date(2026, 6, 15),
    )

    assert dashboard.total_deliverables == 1
    assert dashboard.reports[0].id == "report-1"
    assert dashboard.reports[0].origin == "field_visit"


def test_publish_report_without_pdf_returns_warning() -> None:
    reports, lines = _closed_report_with_line()
    service = _publish_service(reports=reports, lines=lines)

    result = service.publish_report(
        organization_id="org-1",
        report_id="report-1",
        actor_id="admin-1",
    )

    assert result["publish_result"]["pdf_archived"] is False
    assert result["publish_result"]["warnings"]
    assert "PDF" in result["publish_result"]["warnings"][0]


def test_publish_report_rejects_open_report() -> None:
    reports = FakeVisitReportRepository()
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
    service = _publish_service(reports=reports)

    with pytest.raises(Exception) as error:
        service.publish_report(
            organization_id="org-1",
            report_id="report-1",
            actor_id="admin-1",
        )

    assert "סגור" in str(error.value)


def test_preview_publish_report_counts_materializable_lines() -> None:
    reports, lines = _closed_report_with_line()
    service = _publish_service(reports=reports, lines=lines)

    preview = service.preview_publish_report(
        organization_id="org-1",
        report_id="report-1",
    )

    assert preview["line_count"] == 1
    assert preview["draft_line_count"] == 1
    assert preview["materializable_line_count"] == 1
    assert preview["already_published"] is False


def test_publish_endpoint_requires_publish_permission(monkeypatch) -> None:
    reports, lines = _closed_report_with_line()
    service = _publish_service(reports=reports, lines=lines)
    client = _setup_client(monkeypatch, visit_service=service)

    supervisor_token = _token(role="SUPERVISOR", user_id="supervisor-1")
    denied = client.post(
        "/field-reports/visits/report-1/publish",
        headers=_headers(supervisor_token),
    )
    assert denied.status_code == 403

    admin_token = _token(role="ADMIN")
    allowed = client.post(
        "/field-reports/visits/report-1/publish",
        headers=_headers(admin_token),
    )
    assert allowed.status_code == 200
    payload = allowed.json()
    assert payload["is_published"] is True
    assert payload["publish_result"]["issue_materialization"]["created_count"] == 1


def test_publish_preview_endpoint_requires_publish_permission(
    monkeypatch,
) -> None:
    reports, lines = _closed_report_with_line()
    service = _publish_service(reports=reports, lines=lines)
    client = _setup_client(monkeypatch, visit_service=service)

    supervisor_token = _token(role="SUPERVISOR", user_id="supervisor-1")
    denied = client.get(
        "/field-reports/visits/report-1/publish-preview",
        headers=_headers(supervisor_token),
    )
    assert denied.status_code == 403

    manager_token = _token(role="MANAGER", user_id="manager-1")
    allowed = client.get(
        "/field-reports/visits/report-1/publish-preview",
        headers=_headers(manager_token),
    )
    assert allowed.status_code == 200
    assert allowed.json()["materializable_line_count"] == 1


def test_resident_portal_sees_issues_only_after_publish() -> None:
    reports, lines = _closed_report_with_line()
    issues = InMemoryQualityIssueRepository()
    service = _publish_service(
        reports=reports,
        lines=lines,
        issues=issues,
    )

    def list_visible_issues(
        organization_id: str,
        project_id: str,
        group_key: str,
    ) -> list:
        portal = ResidentPortalService(
            issue_repository=MagicMock(
                is_storage_available=MagicMock(return_value=True),
                list_by_project=MagicMock(
                    return_value=list(issues.records.values())
                ),
            )
        )
        issues_visible, _records = portal._collect_issues(
            organization_id=organization_id,
            project_id=project_id,
            group_key=group_key,
        )
        return issues_visible

    before = list_visible_issues(
        organization_id="org-1",
        project_id="project-1",
        group_key="apartment:3",
    )
    assert before == []

    service.publish_report(
        organization_id="org-1",
        report_id="report-1",
        actor_id="admin-1",
    )

    after = list_visible_issues(
        organization_id="org-1",
        project_id="project-1",
        group_key="apartment:3",
    )
    assert len(after) == 1
    assert after[0].title


@patch(
    "app.repositories.field_visit_report_repository.FieldVisitReportRepository",
)
def test_resident_portal_field_lines_visible_after_publish(
    mock_report_repo_cls,
) -> None:
    reports, lines = _closed_report_with_line()
    service = _publish_service(reports=reports, lines=lines)

    report_repository = mock_report_repo_cls.return_value
    report_repository.is_storage_available.return_value = True
    report_repository.list_by_organization.return_value = [
        {
            "id": "report-1",
            "visit_date": "2026-06-01",
            "status": "CLOSED",
            "title": "דוח שלד",
        }
    ]

    portal = ResidentPortalService(line_repository=lines)

    _, before_lines, _ = portal._collect_field_reports(
        organization_id="org-1",
        project_id="project-1",
        group_key="apartment:3",
        actor_role="RESIDENT",
    )
    assert before_lines == []

    service.publish_report(
        organization_id="org-1",
        report_id="report-1",
        actor_id="admin-1",
    )

    _, after_lines, _ = portal._collect_field_reports(
        organization_id="org-1",
        project_id="project-1",
        group_key="apartment:3",
        actor_role="RESIDENT",
    )
    assert len(after_lines) == 1
    assert after_lines[0].description == "סדק בקיר"
