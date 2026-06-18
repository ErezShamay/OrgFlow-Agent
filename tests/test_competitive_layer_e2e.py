"""Gate L6 — Competitive Layer v2 full flow (COMPETITIVE-LAYER-TASKS.md)."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import app.main as main_module
from app.auth.jwt_service import JWTService
from app.config.settings import FeatureFlags
from app.config.standards_seed import STANDARD_TI_1752_SILL_ID
from app.schemas.quality_issue import (
    IssueVisibility,
    QualityIssueEventType,
    resolve_tenant_view_status_he,
)
from app.services.field_report_module_service import FieldReportModuleService
from app.services.quality_issue_service import QualityIssueService
from app.services.resident_portal_service import ResidentPortalService
from app.services.standards_resolver_service import StandardsResolverService
from app.services.standards_resolver_service import StandardsResolverService
from tests.quality_issues_test_support import (
    InMemoryQualityIssueEventRepository,
    InMemoryQualityIssueRepository,
)
from tests.test_field_report_finalize_f1_gate import (
    FakeFinalizeRunRepository,
    FAKE_PDF,
)
from tests.test_field_report_finalize_f2_gate import (
    _finalize_service,
    _setup_client as _setup_finalize_client,
)
from tests.test_standards_kb_l4_gate import InMemoryStandardsRepository
from tests.test_supervisor_project_scope import FakeProfileRepository
from tests.test_project_zero_setup_gate import (
    InMemoryProjectApartmentRepository,
    InMemoryProjectRepository,
    ZeroSetupProjectService,
)
from tests.test_supervision_checklist_e2e import _visit_service
from tests.test_field_visit_reports import (
    FakeModuleRepository,
    FakeOrganizationRepository,
    FakeVisitReportLineRepository,
    FakeVisitReportRepository,
    _headers,
)

ORG_ID = "org-cl6"
PROJECT_ID = "proj-cl6"
CLIENT_REPORT_UUID = "c1111111-1111-4111-8111-111111111111"
CLIENT_LINE_UUID = "d2222222-2222-4222-8222-222222222222"
CHECKLIST_ITEM_ID = "checklist-sup-ins-004"
DEFECT_ISSUE_ID = "SUP-INS-004"
APARTMENT_NUMBER = "5"
GROUP_KEY = f"apartment:{APARTMENT_NUMBER}"
IMAGE_BYTES = b"fake-jpeg-competitive-layer-e2e"


def _token(
    *,
    user_id: str = "supervisor-cl6",
    role: str = "SUPERVISOR",
) -> str:
    return JWTService().issue_access_token(
        user_id=user_id,
        org_id=ORG_ID,
        role=role,
        token_id=f"t-cl6-{role.lower()}",
    )


def _supervision_header_fields() -> dict:
    return {
        "supervision_meta": {
            "construction_stage": "FINISHING",
            "visit_scope": "APARTMENT",
            "apartment_number": APARTMENT_NUMBER,
            "inspect_mode": "quick",
        },
        "blocks": [
            {
                "id": "checklist-main",
                "kind": "supervision_checklist",
                "title_he": f"ביקור דירה {APARTMENT_NUMBER}",
                "construction_stage": "FINISHING",
                "visit_scope": "APARTMENT",
                "apartment_number": APARTMENT_NUMBER,
                "items": [
                    {
                        "id": CHECKLIST_ITEM_ID,
                        "catalog_issue_id": DEFECT_ISSUE_ID,
                        "issue_name_he": "חוסר רולקות בחיבור רצפה-קיר במרפסת",
                        "category_id": "ROOFS_AND_BALCONIES",
                        "category_name_he": "גגות ומרפסות",
                        "top_family": "SYSTEM_WATERPROOFING_AND_INSULATION",
                        "standard_ref": 'ת"י 1752 ח"1',
                        "severity": "Critical",
                        "status": "DEFECT",
                        "notes": "אין רולקה",
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
        "description": "חוסר רולקות בחיבור רצפה-קיר במרפסת",
        "standard_ref": 'ת"י 1752 ח"1',
        "trade": "גגות ומרפסות",
        "location": f"דירה {APARTMENT_NUMBER}",
        "group_key": GROUP_KEY,
        "group_label_he": f"דירה {APARTMENT_NUMBER}",
        "block_id": "checklist-main",
        "status": "NEEDS_ACTION",
        "notes": "אין רולקה",
    }


class CompetitivePortalIssueRepository:
    def __init__(
        self,
        inner: InMemoryQualityIssueRepository,
        *,
        organization_id: str,
    ) -> None:
        self._inner = inner
        self._organization_id = organization_id

    def is_storage_available(self) -> bool:
        return self._inner.is_storage_available()

    def list_by_project(self, project_id: str) -> list[dict]:
        return self._inner.list_by_project(
            organization_id=self._organization_id,
            project_id=project_id,
        )


class CompetitiveLayerApartmentRepository(InMemoryProjectApartmentRepository):
    def get_by_id(self, apartment_id: str) -> dict | None:
        for record in self.records:
            if str(record.get("id")) == apartment_id:
                return record
        return None


class CompetitiveLayerProjectRepository(InMemoryProjectRepository):
    def __init__(self) -> None:
        super().__init__()
        self.projects[PROJECT_ID] = {
            "id": PROJECT_ID,
            "organization_id": ORG_ID,
            "project_name": "תמ\"א 38 חיזוק CL6",
            "scheme": "TAMA38_STRENGTHENING",
            "developer_name": "יזם",
            "developer_email": "developer@example.com",
            "contractor_name": "קבלן",
            "contractor_email": "contractor@example.com",
            "lawyer_name": "עו\"ד",
            "supervisor_name": "מפקח",
            "supervisor_email": "supervisor@example.com",
            "status": "ACTIVE",
        }


@pytest.fixture(autouse=True)
def _enable_finalize_feature_flags(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.services.field_report_finalize_email_service.settings.RESEND_API_KEY",
        "test-key",
    )
    monkeypatch.setattr(
        "app.services.field_report_finalize_notifications_service.settings.FEATURE_FLAGS",
        FeatureFlags(
            enable_notifications=True,
            enable_automation=True,
            enable_ai_review=True,
            enable_email_delivery=True,
        ),
    )


@pytest.fixture
def competitive_layer_setup(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    ) -> tuple[
        TestClient,
        str,
        FakeVisitReportRepository,
        FakeVisitReportLineRepository,
        InMemoryQualityIssueRepository,
        InMemoryQualityIssueEventRepository,
        QualityIssueService,
        ResidentPortalService,
    ]:
    project_repository = CompetitiveLayerProjectRepository()
    apartment_repository = CompetitiveLayerApartmentRepository()
    project_service = ZeroSetupProjectService(
        project_repository=project_repository,
        apartment_repository=apartment_repository,
    )
    bootstrap = project_service.spatial_bootstrap_service.bootstrap(
        project_id=PROJECT_ID,
        scheme="TAMA38_STRENGTHENING",
        organization_id=ORG_ID,
        floors=7,
        housing_units_count=28,
    )
    assert bootstrap.apartments_created == 28

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
    visit_service.project_repository = project_repository
    visit_service.apartment_repository = apartment_repository

    finalize_service = _finalize_service(
        reports=reports,
        lines=lines,
        issues=issues,
        events=events,
        runs=FakeFinalizeRunRepository(),
        pdf_root=pdf_root,
    )
    finalize_service.visit_report_service.project_repository = project_repository
    finalize_service.steps.resident_portal_service.project_repository = (
        project_repository
    )
    finalize_service.steps.profile_repository = FakeProfileRepository(
        {
            "supervisor-cl6": {
                "id": "supervisor-cl6",
                "email": "supervisor@example.com",
            }
        }
    )
    finalize_service.steps.visit_diff_service.project_repository = (
        project_repository
    )
    finalize_service.steps.visit_diff_service.profile_repository = (
        finalize_service.steps.profile_repository
    )

    quality_issue_service = QualityIssueService(
        issue_repository=issues,
        event_repository=events,
        project_repository=project_repository,
    )

    standards_repo = InMemoryStandardsRepository()
    monkeypatch.setattr(
        "app.services.catalog_standard_ref_resolver.StandardsResolverService",
        lambda repository=None: StandardsResolverService(
            repository=standards_repo
        ),
    )

    portal_service = ResidentPortalService(
        line_repository=lines,
        issue_repository=CompetitivePortalIssueRepository(
            issues,
            organization_id=ORG_ID,
        ),
        project_repository=project_repository,
        apartment_repository=apartment_repository,
    )

    module_repository = FakeModuleRepository()
    module_repository.records[ORG_ID] = {
        "organization_id": ORG_ID,
        "is_enabled": True,
    }
    module_service = FieldReportModuleService(
        module_repository=module_repository,
        organization_repository=FakeOrganizationRepository(),
    )

    monkeypatch.setattr("app.main.field_visit_report_service", visit_service)
    monkeypatch.setattr("app.main.field_report_finalize_service", finalize_service)
    monkeypatch.setattr("app.main.quality_issue_service", quality_issue_service)
    monkeypatch.setattr("app.main.resident_portal_service", portal_service)
    monkeypatch.setattr("app.main.project_repository", project_repository)

    client = _setup_finalize_client(
        monkeypatch,
        finalize_service=finalize_service,
    )

    monkeypatch.setattr("app.main.field_report_module_service", module_service)
    monkeypatch.setattr("app.main.field_visit_report_service", visit_service)
    monkeypatch.setattr("app.main.quality_issue_service", quality_issue_service)
    monkeypatch.setattr("app.main.resident_portal_service", portal_service)
    monkeypatch.setattr("app.main.project_repository", project_repository)

    class FakeTenantScope:
        def get_organization_scoped_project(self, pid, *_args, **_kwargs):
            return project_repository.projects.get(pid)

    monkeypatch.setattr(main_module, "tenant_scope_service", FakeTenantScope())
    from app.main import app

    app.state.field_report_module_service = module_service
    return (
        client,
        PROJECT_ID,
        reports,
        lines,
        issues,
        events,
        quality_issue_service,
        portal_service,
    )


def test_competitive_layer_full_flow(
    competitive_layer_setup: tuple[
        TestClient,
        str,
        FakeVisitReportRepository,
        FakeVisitReportLineRepository,
        InMemoryQualityIssueRepository,
        InMemoryQualityIssueEventRepository,
        QualityIssueService,
        ResidentPortalService,
    ],
) -> None:
    (
        client,
        project_id,
        reports,
        lines,
        issues,
        events,
        quality_issue_service,
        portal_service,
    ) = competitive_layer_setup

    supervisor_headers = _headers(_token(role="SUPERVISOR"), org_id=ORG_ID)
    contractor_headers = _headers(
        _token(user_id="contractor-cl6", role="CONTRACTOR"),
        org_id=ORG_ID,
    )

    # Z4 — offline prep includes spatial bootstrap + catalog
    prep = client.get(
        f"/projects/{project_id}/offline-prep",
        headers=supervisor_headers,
    )
    assert prep.status_code == 200
    prep_body = prep.json()
    assert prep_body["focused_project_id"] == project_id
    assert len(prep_body["apartments_by_project"][project_id]) == 28
    assert prep_body["supervision_catalog"]["issue_count"] >= 1

    # V1/V2 — supervision sync with quick inspect DEFECT (X) line
    sync_response = client.put(
        "/field-reports/visits/sync",
        headers=supervisor_headers,
        json={
            "client_report_uuid": CLIENT_REPORT_UUID,
            "project_id": project_id,
            "visit_type": "FINISHING_APARTMENTS",
            "visit_date": "2026-06-18",
            "header_fields": _supervision_header_fields(),
            "lines": [_defect_sync_line()],
        },
    )
    assert sync_response.status_code == 200
    report_id = sync_response.json()["id"]

    photo_response = client.post(
        f"/field-reports/visits/sync/{CLIENT_REPORT_UUID}/lines/"
        f"{CLIENT_LINE_UUID}/photos",
        headers=supervisor_headers,
        files={"file": ("defect.jpg", IMAGE_BYTES, "image/jpeg")},
    )
    assert photo_response.status_code == 200

    stored_line = lines.list_by_report(report_id)[0]
    line_id = str(stored_line["id"])

    # L1 — draft materialization on DEFECT
    draft_response = client.post(
        f"/field-reports/visits/{report_id}/lines/{line_id}/draft-issue",
        headers=supervisor_headers,
        json={"checklist_item_id": CHECKLIST_ITEM_ID},
    )
    assert draft_response.status_code == 200
    draft_body = draft_response.json()
    assert draft_body["draft_materialization"]["created"] is True
    assert draft_body["draft_materialization"]["visibility"] == (
        IssueVisibility.DRAFT.value
    )
    issue_id = draft_body["draft_materialization"]["issue_id"]

    draft_issue = issues.get_for_organization(
        issue_id=issue_id,
        organization_id=ORG_ID,
    )
    assert draft_issue is not None
    assert draft_issue["visibility"] == IssueVisibility.DRAFT.value
    assert draft_issue["catalog_issue_id"] == DEFECT_ISSUE_ID
    assert draft_issue["tenant_view_status_he"] == resolve_tenant_view_status_he(
        "OPEN"
    )

    contractor_before = client.get(
        f"/projects/{project_id}/issues",
        headers=contractor_headers,
    )
    assert contractor_before.status_code == 200
    assert contractor_before.json()["total"] == 0

    # Close report (still DRAFT until finalize)
    close_response = client.post(
        f"/field-reports/visits/{report_id}/close",
        headers=supervisor_headers,
    )
    assert close_response.status_code == 200
    assert close_response.json()["status"] == "CLOSED"
    assert close_response.json()["issue_materialization"]["created_count"] == 0
    assert len(issues.records) == 1

    # L2 — finalize promotes draft → PUBLISHED (no duplicate)
    finalize_response = client.post(
        f"/field-reports/visits/{report_id}/finalize",
        headers=supervisor_headers,
        files={"file": ("visit.pdf", FAKE_PDF, "application/pdf")},
    )
    assert finalize_response.status_code == 202

    status = client.get(
        f"/field-reports/visits/{report_id}/finalize-status",
        headers=supervisor_headers,
    )
    assert status.status_code == 200
    payload = status.json()
    assert payload["status"] == "FINALIZED"
    materialization = payload["finalize_run"]["materialization"]
    assert materialization["created_count"] == 0
    assert materialization.get("promoted_count", 0) >= 1 or (
        len(issues.records) == 1
        and next(iter(issues.records.values()))["visibility"]
        == IssueVisibility.PUBLISHED.value
    )

    published_issue = issues.get_for_organization(
        issue_id=issue_id,
        organization_id=ORG_ID,
    )
    assert published_issue is not None
    assert published_issue["visibility"] == IssueVisibility.PUBLISHED.value
    assert len(issues.records) == 1

    issue_events = events.list_by_issue_id(issue_id)
    event_types = {event["event_type"] for event in issue_events}
    assert QualityIssueEventType.CREATED_FROM_FIELD.value in event_types
    assert QualityIssueEventType.PUBLISHED_FROM_FINALIZE.value in event_types
    assert QualityIssueEventType.DETECTED.value not in event_types

    published_line = lines.list_by_report(report_id)[0]
    assert published_line["visibility"] == IssueVisibility.PUBLISHED.value

    # Step 6 — contractor sees PUBLISHED issue only
    contractor_after = client.get(
        f"/projects/{project_id}/issues",
        headers=contractor_headers,
    )
    assert contractor_after.status_code == 200
    contractor_items = contractor_after.json()["items"]
    assert contractor_after.json()["total"] == 1
    assert contractor_items[0]["id"] == issue_id
    assert contractor_items[0]["visibility"] == IssueVisibility.PUBLISHED.value

    # L4 — standard_id resolved from catalog / standards KB
    detail = client.get(
        f"/issues/{issue_id}",
        headers=contractor_headers,
    )
    assert detail.status_code == 200
    assert detail.json()["issue"]["standard_id"] == STANDARD_TI_1752_SILL_ID
    assert detail.json()["catalog_link"]["standard_id"] == STANDARD_TI_1752_SILL_ID

    # L5 — resident portal tenant-friendly status
    portal_issues, _ = portal_service._collect_issues(
        organization_id=ORG_ID,
        project_id=project_id,
        group_key=GROUP_KEY,
    )
    assert len(portal_issues) == 1
    assert portal_issues[0].tenant_view_status_he == resolve_tenant_view_status_he(
        "OPEN"
    )


def test_competitive_layer_gate_files_exist() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    assert (repo_root / "tests" / "test_competitive_layer_e2e.py").is_file()
    assert (
        repo_root
        / "orgflow-ui"
        / "tests"
        / "lib"
        / "competitive-layer-e2e-gate.test.ts"
    ).is_file()
