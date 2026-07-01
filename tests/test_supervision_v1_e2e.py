"""Gate H — supervision v1.0 E2E loop (§10.1–10.4).

Single in-memory flow: supervisor draft → manager publish → visit diff → resident portal → portfolio KPIs.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.auth.jwt_service import JWTService
from app.schemas.quality_issue import IssueVisibility, QualityIssueEventType
from app.services.deliverable_reports_service import DeliverableReportsService
from app.services.field_report_catalog_service import FieldReportCatalogService
from app.services.field_report_module_service import FieldReportModuleService
from app.services.field_report_organization_profile_service import (
    FieldReportOrganizationProfileService,
)
from app.services.field_visit_report_pdf_service import FieldVisitReportPdfService
from app.services.field_visit_report_service import FieldVisitReportService
from app.services.quality_issue_materialization_service import (
    QualityIssueMaterializationService,
)
from app.services.quality_issue_service import QualityIssueService
from app.services.resident_portal_service import ResidentPortalService
from tests.quality_issues_test_support import (
    InMemoryQualityIssueEventRepository,
    InMemoryQualityIssueRepository,
    qc_create_request,
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
    _setup_client,
    _token,
)


def _structure_catalog_issue_id() -> str:
    service = FieldReportCatalogService()
    for candidate in ("STR-02-001", "QC-STR-001"):
        issue = service.find_issue(candidate)
        if issue is not None:
            return str(issue["issue_id"])
    catalog = service.get_catalog_for_visit_type("STRUCTURE_SITE")
    issues = catalog.get("issues") or []
    assert issues, "STRUCTURE_SITE catalog must include at least one issue"
    return str(issues[0]["issue_id"])


FAKE_PDF = b"%PDF-1.4\npublished-report\n%%EOF\n"


class PortalCompatibleIssueRepository:
    """Adapter: resident portal calls list_by_project(project_id) positionally."""

    def __init__(self, inner: InMemoryQualityIssueRepository) -> None:
        self._inner = inner

    def is_storage_available(self) -> bool:
        return self._inner.is_storage_available()

    def list_by_project(self, project_id: str) -> list[dict]:
        return self._inner.list_by_project(
            organization_id="org-1",
            project_id=project_id,
        )


class DeliverableAwareReportRepository(FakeVisitReportRepository):
    def list_pdf_deliverables_by_organization(self, organization_id: str) -> list[dict]:
        return [
            record
            for record in self.records.values()
            if record.get("organization_id") == organization_id
            and record.get("pdf_storage_path")
        ]


def _publish_service(
    *,
    reports: DeliverableAwareReportRepository | None = None,
    lines: FakeVisitReportLineRepository | None = None,
    issues: InMemoryQualityIssueRepository | None = None,
    events: InMemoryQualityIssueEventRepository | None = None,
    pdf_root: Path | None = None,
    organization_profile_service: FieldReportOrganizationProfileService | None = None,
) -> FieldVisitReportService:
    report_repository = reports or DeliverableAwareReportRepository()
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
        organization_profile_service=organization_profile_service,
        report_processing_service=FakeReportProcessingService(),
        materialization_service=materialization,
        pdf_service=pdf_service,
    )


def _admin_token() -> str:
    return JWTService().issue_access_token(
        user_id="admin-1",
        org_id="org-1",
        role="ADMIN",
        token_id="t-v1-admin",
    )


@pytest.fixture
def supervision_v1_setup(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> tuple[
    TestClient,
    FakeVisitReportRepository,
    FakeVisitReportLineRepository,
    InMemoryQualityIssueRepository,
    InMemoryQualityIssueEventRepository,
    QualityIssueService,
    FieldVisitReportService,
]:
    reports = DeliverableAwareReportRepository()
    lines = FakeVisitReportLineRepository()
    issues = InMemoryQualityIssueRepository()
    events = InMemoryQualityIssueEventRepository()

    module_repository = FakeModuleRepository()
    module_service = FieldReportModuleService(
        module_repository=module_repository,
        organization_repository=FakeOrganizationRepository(),
    )
    organization_profile_service = FieldReportOrganizationProfileService(
        organization_repository=FakeOrganizationRepository(),
        module_service=module_service,
    )

    visit_service = _publish_service(
        reports=reports,
        lines=lines,
        issues=issues,
        events=events,
        pdf_root=tmp_path / "pdfs",
        organization_profile_service=organization_profile_service,
    )

    qc_service = QualityIssueService(
        issue_repository=issues,
        event_repository=events,
        project_repository=FakeProjectRepository(),
        report_repository=reports,
    )

    portal_service = ResidentPortalService(
        line_repository=lines,
        issue_repository=PortalCompatibleIssueRepository(issues),
        project_repository=FakeProjectRepository(),
    )

    monkeypatch.setattr("app.dependencies.field_visit_report_service", visit_service)
    monkeypatch.setattr("app.dependencies.quality_issue_service", qc_service)
    monkeypatch.setattr("app.dependencies.resident_portal_service", portal_service)
    monkeypatch.setattr("app.dependencies.project_repository", FakeProjectRepository())

    client = _setup_client(
        monkeypatch,
        field_visit_report_service=visit_service,
    )
    return (
        client,
        reports,
        lines,
        issues,
        events,
        qc_service,
        visit_service,
    )


def test_supervision_v1_full_loop(
    supervision_v1_setup: tuple[
        TestClient,
        FakeVisitReportRepository,
        FakeVisitReportLineRepository,
        InMemoryQualityIssueRepository,
        InMemoryQualityIssueEventRepository,
        QualityIssueService,
        FieldVisitReportService,
    ],
) -> None:
    (
        client,
        reports,
        lines,
        issues,
        events,
        qc_service,
        visit_service,
    ) = supervision_v1_setup

    supervisor_headers = _headers(_token())
    admin_headers = _headers(_admin_token())

    # §10.1 — supervisor: create report → catalog line → close (DRAFT)
    create_response = client.post(
        "/field-reports/visits",
        headers=supervisor_headers,
        json={
            "project_id": "project-1",
            "visit_type": "STRUCTURE_SITE",
            "visit_date": "2026-06-01",
        },
    )
    assert create_response.status_code == 200
    report_id = create_response.json()["id"]

    catalog_issue_id = _structure_catalog_issue_id()

    line_response = client.post(
        f"/field-reports/visits/{report_id}/lines",
        headers=supervisor_headers,
        json={
            "description": "סדק בקיר חיצוני",
            "location": "דירה 3",
            "group_key": "apartment:3",
            "standard_ref": 'ת"י 466',
            "catalog_reference_id": "IL-STD-466-CRACK",
            "issue_id": catalog_issue_id,
        },
    )
    assert line_response.status_code == 200
    line_id = line_response.json()["id"]
    assert line_response.json()["visibility"] == IssueVisibility.DRAFT.value

    close_response = client.post(
        f"/field-reports/visits/{report_id}/close",
        headers=supervisor_headers,
    )
    assert close_response.status_code == 200
    closed = close_response.json()
    assert closed["status"] == "CLOSED"
    assert closed["issue_materialization"]["created_count"] == 0
    assert len(issues.records) == 0

    closed_line = lines.get_by_id(line_id)
    assert closed_line is not None
    assert closed_line["visibility"] == IssueVisibility.DRAFT.value

    portal_before = ResidentPortalService(
        line_repository=lines,
        issue_repository=PortalCompatibleIssueRepository(issues),
    )
    issues_before, _ = portal_before._collect_issues(
        organization_id="org-1",
        project_id="project-1",
        group_key="apartment:3",
    )
    assert issues_before == []

    # §10.2 — manager: publish preview → POST publish → materialize + PDF + archive
    preview = client.get(
        f"/field-reports/visits/{report_id}/publish-preview",
        headers=admin_headers,
    )
    assert preview.status_code == 200
    preview_body = preview.json()
    assert preview_body["materializable_line_count"] == 1
    assert preview_body["draft_line_count"] == 1

    publish = client.post(
        f"/field-reports/visits/{report_id}/publish",
        headers=admin_headers,
        files={"file": ("supervision-v1.pdf", FAKE_PDF, "application/pdf")},
    )
    assert publish.status_code == 200
    publish_body = publish.json()
    assert publish_body["is_published"] is True
    assert publish_body["publish_result"]["issue_materialization"]["created_count"] == 1
    assert publish_body["publish_result"]["pdf_archived"] is True

    archived = reports.records[report_id]
    assert archived.get("pdf_storage_path")
    assert archived.get("pdf_filename")

    published_line = lines.list_by_report(report_id)[0]
    assert published_line["visibility"] == IssueVisibility.PUBLISHED.value

    assert len(issues.records) == 1
    published_issue = next(iter(issues.records.values()))
    assert published_issue["visibility"] == IssueVisibility.PUBLISHED.value
    assert published_issue["status"] == "OPEN"

    portfolio_open = qc_service.get_portfolio_quality_summary(
        organization_id="org-1",
        actor_role="ADMIN",
    )
    assert portfolio_open.total_open == 1

    issues.create(
        organization_id="org-1",
        project_id="project-1",
        request=qc_create_request(materialization_key="draft-kpi-leak"),
    )
    portfolio_ignores_draft = qc_service.get_portfolio_quality_summary(
        organization_id="org-1",
        actor_role="ADMIN",
    )
    assert portfolio_ignores_draft.total_open == 1

    deliverables = DeliverableReportsService(
        project_repository=FakeProjectRepository(),
        field_visit_report_repository=reports,
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
    assert dashboard.reports[0].id == report_id

    # §10.3 — visit diff + lifecycle transitions
    diff = client.get(
        f"/projects/project-1/visits/{report_id}/issue-diff",
        headers=supervisor_headers,
    )
    assert diff.status_code == 200
    diff_body = diff.json()
    assert diff_body["total_new"] == 1
    assert len(diff_body["new"]) == 1

    issue_id = published_issue["id"]

    closed_issue = client.patch(
        f"/issues/{issue_id}",
        headers=supervisor_headers,
        json={
            "status": "CLOSED",
            "last_seen_report_id": report_id,
            "last_seen_line_id": line_id,
        },
    )
    assert closed_issue.status_code == 200
    assert closed_issue.json()["status"] == "CLOSED"

    # §10.4 — resident portal: published-only, zero DRAFT
    portal_after = ResidentPortalService(
        line_repository=lines,
        issue_repository=PortalCompatibleIssueRepository(issues),
    )
    visible_issues, issue_records = portal_after._collect_issues(
        organization_id="org-1",
        project_id="project-1",
        group_key="apartment:3",
    )
    assert len(visible_issues) == 1
    assert all(
        record.get("visibility") == IssueVisibility.PUBLISHED.value
        for record in issue_records
    )
    assert not any(
        record.get("visibility") == IssueVisibility.DRAFT.value
        for record in issue_records
    )

    draft_line = lines.create(
        {
            "report_id": report_id,
            "organization_id": "org-1",
            "sort_order": 99,
            "description": "טיוטה נסתרת",
            "location": "דירה 3",
            "group_key": "apartment:3",
            "visibility": IssueVisibility.DRAFT.value,
        }
    )
    _ = draft_line
    leaked_issues, _ = portal_after._collect_issues(
        organization_id="org-1",
        project_id="project-1",
        group_key="apartment:3",
    )
    assert len(leaked_issues) == 1
    assert leaked_issues[0].title == published_issue["title"]

    portfolio_closed = qc_service.get_portfolio_quality_summary(
        organization_id="org-1",
        actor_role="ADMIN",
    )
    assert portfolio_closed.total_open == 0

    open_published = client.patch(
        f"/issues/{issue_id}",
        headers=supervisor_headers,
        json={"status": "REOPENED"},
    )
    assert open_published.status_code == 200

    portfolio_reopened = qc_service.get_portfolio_quality_summary(
        organization_id="org-1",
        actor_role="ADMIN",
    )
    assert portfolio_reopened.total_open == 1

    detected = [
        event
        for event in events.records.values()
        if event["event_type"] == QualityIssueEventType.DETECTED.value
    ]
    assert len(detected) == 1
