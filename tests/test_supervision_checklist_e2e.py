"""Gate §18.3 — supervision checklist E2E (field-supervision-checklist-spec).

offline prep → sync create (supervision_checklist) → defect line + photo → close → publish.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.auth.jwt_service import JWTService
from app.schemas.quality_issue import IssueVisibility, QualityIssueEventType
from app.services.field_report_module_service import FieldReportModuleService
from app.services.field_report_organization_profile_service import (
    FieldReportOrganizationProfileService,
)
from app.services.field_visit_report_photo_service import (
    FieldVisitReportPhotoService,
)
from app.services.field_visit_report_pdf_service import FieldVisitReportPdfService
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
    _setup_client,
    _token,
)

CLIENT_REPORT_UUID = "a1111111-1111-4111-8111-111111111111"
CLIENT_LINE_UUID = "b2222222-2222-4222-8222-222222222222"
CHECKLIST_ITEM_ID = "checklist-item-fin-004"
DEFECT_ISSUE_ID = "SUP-FIN-004"
FAKE_PDF = b"%PDF-1.4\nsupervision-checklist-report\n%%EOF\n"
IMAGE_BYTES = b"fake-jpeg-bytes-for-checklist-defect-photo"


class FakeApartmentRepository:
    def is_storage_available(self) -> bool:
        return True

    def list_by_project(self, project_id: str) -> list[dict]:
        if project_id != "project-1":
            return []
        return [
            {
                "id": "apt-12",
                "organization_id": "org-1",
                "project_id": project_id,
                "apartment_number": "12",
                "group_key": "apartment:12",
                "owner_name": "Owner Twelve",
                "invite_status": "none",
            }
        ]


class PortalCompatibleIssueRepository:
    def __init__(self, inner: InMemoryQualityIssueRepository) -> None:
        self._inner = inner

    def is_storage_available(self) -> bool:
        return self._inner.is_storage_available()

    def list_by_project(self, project_id: str) -> list[dict]:
        return self._inner.list_by_project(
            organization_id="org-1",
            project_id=project_id,
        )


def _admin_token() -> str:
    return JWTService().issue_access_token(
        user_id="admin-1",
        org_id="org-1",
        role="ADMIN",
        token_id="t-sc-admin",
    )


def _supervision_header_fields() -> dict:
    return {
        "supervision_meta": {
            "construction_stage": "FINISHING",
            "visit_scope": "APARTMENT",
            "apartment_id": "apt-12",
            "apartment_number": "12",
            "owner_name": "Owner Twelve",
        },
        "blocks": [
            {
                "id": "checklist-main",
                "kind": "supervision_checklist",
                "title_he": "ביקור דירה 12",
                "construction_stage": "FINISHING",
                "visit_scope": "APARTMENT",
                "apartment_number": "12",
                "items": [
                    {
                        "id": CHECKLIST_ITEM_ID,
                        "catalog_issue_id": DEFECT_ISSUE_ID,
                        "issue_name_he": "פוגות לא מלאות/לא אטומות",
                        "category_id": "TILING",
                        "category_name_he": "ריצוף וחיפוי",
                        "top_family": "FINISHING_WORKS",
                        "standard_ref": 'ת"י 1555',
                        "severity": "Medium",
                        "status": "DEFECT",
                        "notes": "פוגה חסרה",
                        "photo_ids": ["primary"],
                        "linked_line_id": CLIENT_LINE_UUID,
                        "sort_order": 0,
                    }
                ],
            }
        ],
    }


def _defect_sync_line() -> dict:
    return {
        "client_line_uuid": CLIENT_LINE_UUID,
        "sort_order": 0,
        "issue_id": DEFECT_ISSUE_ID,
        "description": "פוגות לא מלאות/לא אטומות",
        "standard_ref": 'ת"י 1555',
        "trade": "ריצוף וחיפוי",
        "location": "דירה 12",
        "group_key": "apartment:12",
        "group_label_he": "דירה 12",
        "block_id": "checklist-main",
        "status": "NEEDS_ACTION",
        "notes": "פוגה חסרה",
    }


def _visit_service(
    *,
    reports: FakeVisitReportRepository,
    lines: FakeVisitReportLineRepository,
    issues: InMemoryQualityIssueRepository,
    events: InMemoryQualityIssueEventRepository,
    photos_root: Path,
    pdf_root: Path,
) -> FieldVisitReportService:
    materialization = QualityIssueMaterializationService(
        report_repository=reports,
        line_repository=lines,
        line_photo_repository=FakeVisitReportLinePhotoRepository(),
        issue_repository=issues,
        event_repository=events,
    )
    module_service = FieldReportModuleService(
        module_repository=FakeModuleRepository(),
        organization_repository=FakeOrganizationRepository(),
    )
    return FieldVisitReportService(
        report_repository=reports,
        line_repository=lines,
        line_photo_repository=FakeVisitReportLinePhotoRepository(),
        project_repository=FakeProjectRepository(),
        apartment_repository=FakeApartmentRepository(),
        organization_profile_service=FieldReportOrganizationProfileService(
            organization_repository=FakeOrganizationRepository(),
            module_service=module_service,
        ),
        report_processing_service=FakeReportProcessingService(),
        materialization_service=materialization,
        pdf_service=FieldVisitReportPdfService(pdfs_root=pdf_root),
        photo_service=FieldVisitReportPhotoService(photos_root=photos_root),
    )


@pytest.fixture
def supervision_checklist_setup(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> tuple[
    TestClient,
    FakeVisitReportRepository,
    FakeVisitReportLineRepository,
    InMemoryQualityIssueRepository,
    InMemoryQualityIssueEventRepository,
    FieldVisitReportService,
]:
    reports = FakeVisitReportRepository()
    lines = FakeVisitReportLineRepository()
    issues = InMemoryQualityIssueRepository()
    events = InMemoryQualityIssueEventRepository()
    photos_root = tmp_path / "photos"
    pdf_root = tmp_path / "pdfs"

    visit_service = _visit_service(
        reports=reports,
        lines=lines,
        issues=issues,
        events=events,
        photos_root=photos_root,
        pdf_root=pdf_root,
    )

    portal_service = ResidentPortalService(
        line_repository=lines,
        issue_repository=PortalCompatibleIssueRepository(issues),
        project_repository=FakeProjectRepository(),
    )

    monkeypatch.setattr("app.main.field_visit_report_service", visit_service)
    monkeypatch.setattr("app.main.resident_portal_service", portal_service)
    monkeypatch.setattr("app.main.project_repository", FakeProjectRepository())

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
        visit_service,
    )


def test_supervision_checklist_full_loop(
    supervision_checklist_setup: tuple[
        TestClient,
        FakeVisitReportRepository,
        FakeVisitReportLineRepository,
        InMemoryQualityIssueRepository,
        InMemoryQualityIssueEventRepository,
        FieldVisitReportService,
    ],
) -> None:
    (
        client,
        reports,
        lines,
        issues,
        events,
        _visit_service,
    ) = supervision_checklist_setup

    supervisor_headers = _headers(_token())
    admin_headers = _headers(_admin_token())

    # §17.6 — offline prep includes supervision catalog + apartments + public areas
    prep = client.get("/field-reports/offline-prep", headers=supervisor_headers)
    assert prep.status_code == 200
    prep_body = prep.json()
    assert prep_body["supervision_catalog"]["issue_count"] >= 1
    assert prep_body["public_areas"]
    assert prep_body["apartments_by_project"]["project-1"][0]["apartment_number"] == "12"

    # Create synced supervision report with checklist block + defect line
    sync_response = client.put(
        "/field-reports/visits/sync",
        headers=supervisor_headers,
        json={
            "client_report_uuid": CLIENT_REPORT_UUID,
            "project_id": "project-1",
            "visit_type": "FINISHING_APARTMENTS",
            "visit_date": "2026-06-14",
            "header_fields": _supervision_header_fields(),
            "lines": [_defect_sync_line()],
        },
    )
    assert sync_response.status_code == 200
    sync_body = sync_response.json()
    report_id = sync_body["id"]
    assert sync_body["created"] is True

    stored = reports.records[report_id]
    blocks = stored.get("header_fields", {}).get("blocks", [])
    assert any(block.get("kind") == "supervision_checklist" for block in blocks)

    # Upload defect photo (offline checklist photo → synced line photo)
    photo_response = client.post(
        f"/field-reports/visits/sync/{CLIENT_REPORT_UUID}/lines/"
        f"{CLIENT_LINE_UUID}/photos",
        headers=supervisor_headers,
        files={"file": ("defect.jpg", IMAGE_BYTES, "image/jpeg")},
    )
    assert photo_response.status_code == 200

    # Close — DRAFT visibility, no portal materialization yet (§9, §17.5)
    close_response = client.post(
        f"/field-reports/visits/{report_id}/close",
        headers=supervisor_headers,
    )
    assert close_response.status_code == 200
    closed = close_response.json()
    assert closed["status"] == "CLOSED"
    assert closed["issue_materialization"]["created_count"] == 0
    assert len(issues.records) == 0

    portal_before = ResidentPortalService(
        line_repository=lines,
        issue_repository=PortalCompatibleIssueRepository(issues),
    )
    issues_before, _ = portal_before._collect_issues(
        organization_id="org-1",
        project_id="project-1",
        group_key="apartment:12",
    )
    assert issues_before == []

    # Manager publish → materialize + archive PDF
    publish = client.post(
        f"/field-reports/visits/{report_id}/publish",
        headers=admin_headers,
        files={"file": ("supervision-checklist.pdf", FAKE_PDF, "application/pdf")},
    )
    assert publish.status_code == 200
    publish_body = publish.json()
    assert publish_body["is_published"] is True
    assert publish_body["publish_result"]["issue_materialization"]["created_count"] == 1
    assert publish_body["publish_result"]["pdf_archived"] is True

    published_line = lines.list_by_report(report_id)[0]
    assert published_line["visibility"] == IssueVisibility.PUBLISHED.value
    assert published_line["issue_id"] == DEFECT_ISSUE_ID
    assert published_line["standard_ref"] == 'ת"י 1555'

    assert len(issues.records) == 1
    published_issue = next(iter(issues.records.values()))
    assert published_issue["visibility"] == IssueVisibility.PUBLISHED.value
    assert published_issue["catalog_issue_id"] == DEFECT_ISSUE_ID

    portal_after = ResidentPortalService(
        line_repository=lines,
        issue_repository=PortalCompatibleIssueRepository(issues),
    )
    visible_issues, issue_records = portal_after._collect_issues(
        organization_id="org-1",
        project_id="project-1",
        group_key="apartment:12",
    )
    assert len(visible_issues) == 1
    assert all(
        record.get("visibility") == IssueVisibility.PUBLISHED.value
        for record in issue_records
    )

    detected = [
        event
        for event in events.records.values()
        if event["event_type"] == QualityIssueEventType.DETECTED.value
    ]
    assert len(detected) == 1
