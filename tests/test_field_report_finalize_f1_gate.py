from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from fastapi.testclient import TestClient

from app.auth.jwt_service import JWTService
from app.config.field_report_project_scheme import (
    VALID_PROJECT_SCHEMES,
    project_scheme_label_he,
)
from app.services.field_report_finalize_service import (
    FieldReportFinalizeService,
)
from app.services.field_report_finalize_registry import (
    INFRASTRUCTURE_PRE_STEP_ORDER,
)
from app.services.field_report_finalize_steps import (
    CORE_FINALIZE_STEP_ORDER,
)
from app.services.field_report_module_service import (
    FieldReportModuleService,
)
from app.services.field_report_organization_profile_service import (
    FieldReportOrganizationProfileService,
)
from app.services.field_visit_report_service import FieldVisitReportService
from tests.field_report_finalize_test_support import (
    StubFinalizeAiService,
    StubFinalizeEmailService,
    StubFinalizeNotificationsService,
)
from tests.test_field_visit_reports import (
    FakeModuleRepository,
    FakeOrganizationRepository,
    FakeProjectRepository,
    FakeVisitReportLineRepository,
    FakeVisitReportRepository,
    _headers,
)

FAKE_PDF = b"%PDF-1.4\nfinalize-trigger\n%%EOF\n"


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
        token_id="t-finalize-f1",
    )


class FakeFinalizeRunRepository:
    ACTIVE_STATUSES = frozenset(
        {"PENDING", "RUNNING", "COMPLETED", "PARTIAL"}
    )

    def __init__(self) -> None:
        self.records: dict[str, dict] = {}

    def is_storage_available(self) -> bool:
        return True

    def create(self, payload: dict) -> dict:
        run_id = payload.get("id") or str(uuid4())
        now = datetime.now(UTC).isoformat()
        record = {
            "id": run_id,
            "created_at": payload.get("created_at") or now,
            "updated_at": payload.get("updated_at") or now,
            "steps_completed": [],
            "steps_failed": [],
            **payload,
        }
        self.records[str(run_id)] = record
        return record

    def get_by_id(self, run_id: str) -> dict | None:
        return self.records.get(run_id)

    def get_latest_by_report_id(self, report_id: str) -> dict | None:
        matches = [
            record
            for record in self.records.values()
            if record["report_id"] == report_id
        ]
        if not matches:
            return None
        return sorted(
            matches,
            key=lambda record: record["created_at"],
            reverse=True,
        )[0]

    def get_active_by_report_id(self, report_id: str) -> dict | None:
        latest = self.get_latest_by_report_id(report_id)
        if not latest:
            return None
        if str(latest.get("status") or "") in self.ACTIVE_STATUSES:
            return latest
        return None

    def get_by_idempotency_key(
        self,
        *,
        organization_id: str,
        idempotency_key: str,
    ) -> dict | None:
        matches = [
            record
            for record in self.records.values()
            if record["organization_id"] == organization_id
            and record["idempotency_key"] == idempotency_key
        ]
        if not matches:
            return None
        return sorted(
            matches,
            key=lambda record: record["created_at"],
            reverse=True,
        )[0]

    def update(self, run_id: str, payload: dict) -> dict | None:
        record = self.records.get(run_id)
        if not record:
            return None
        record.update(payload)
        record["updated_at"] = datetime.now(UTC).isoformat()
        return record


def _closed_report(
    reports: FakeVisitReportRepository,
    *,
    report_id: str = "report-1",
    status: str = "CLOSED",
) -> None:
    reports.records[report_id] = {
        "id": report_id,
        "organization_id": "org-1",
        "project_id": "project-1",
        "status": status,
        "visit_type": "STRUCTURE_SITE",
        "visit_date": "2026-06-01",
        "closed_at": "2026-06-09T10:00:00+00:00",
        "created_by_profile_id": "profile-1",
        "header_fields": {},
        "updated_at": "2026-06-09T10:00:00+00:00",
        "created_at": "2026-06-01T12:00:00+00:00",
    }


class StubCoreFinalizeSteps:
    def run_core_steps(self, ctx):
        summaries = {
            step_id: {"stub": True} for step_id in CORE_FINALIZE_STEP_ORDER
        }
        return list(CORE_FINALIZE_STEP_ORDER), [], summaries


def _finalize_service(
    *,
    reports: FakeVisitReportRepository | None = None,
    lines: FakeVisitReportLineRepository | None = None,
    runs: FakeFinalizeRunRepository | None = None,
    steps: StubCoreFinalizeSteps | None = None,
) -> FieldReportFinalizeService:
    report_repository = reports or FakeVisitReportRepository()
    line_repository = lines or FakeVisitReportLineRepository()
    visit_report_service = FieldVisitReportService(
        report_repository=report_repository,
        line_repository=line_repository,
        project_repository=FakeProjectRepository(),
    )
    return FieldReportFinalizeService(
        run_repository=runs or FakeFinalizeRunRepository(),
        report_repository=report_repository,
        visit_report_service=visit_report_service,
        steps=steps if steps is not None else StubCoreFinalizeSteps(),
        email_service=StubFinalizeEmailService(),
        notifications_service=StubFinalizeNotificationsService(),
        ai_service=StubFinalizeAiService(),
    )


def _setup_client(
    monkeypatch,
    *,
    finalize_service: FieldReportFinalizeService,
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
        "app.dependencies.field_report_finalize_service",
        finalize_service,
    )
    from app.services.field_visit_report_service import (
        FieldVisitReportService,
    )

    visit_service = FieldVisitReportService(
        report_repository=finalize_service.report_repository,
        organization_profile_service=organization_profile_service,
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


def test_finalize_endpoint_returns_202_with_run_id(monkeypatch) -> None:
    reports = FakeVisitReportRepository()
    runs = FakeFinalizeRunRepository()
    _closed_report(reports)
    service = _finalize_service(reports=reports, runs=runs)
    client = _setup_client(monkeypatch, finalize_service=service)

    supervisor_token = _token(role="SUPERVISOR")
    response = client.post(
        "/field-reports/visits/report-1/finalize",
        headers=_headers(supervisor_token),
        files={"file": ("visit.pdf", FAKE_PDF, "application/pdf")},
    )

    assert response.status_code == 202
    payload = response.json()
    assert payload["report_id"] == "report-1"
    assert payload["status"] == "FINALIZING"
    assert payload["finalize_run_id"]
    assert "הדוח בעיבוד" in payload["message"]
    assert reports.records["report-1"]["status"] == "FINALIZING"
    assert len(runs.records) == 1


def test_finalize_endpoint_supervisor_allowed_manager_admin_denied(
    monkeypatch,
) -> None:
    reports = FakeVisitReportRepository()
    _closed_report(reports)
    service = _finalize_service(reports=reports)
    client = _setup_client(monkeypatch, finalize_service=service)

    files = {"file": ("visit.pdf", FAKE_PDF, "application/pdf")}

    manager_token = _token(role="MANAGER", user_id="manager-1")
    manager_response = client.post(
        "/field-reports/visits/report-1/finalize",
        headers=_headers(manager_token),
        files=files,
    )
    assert manager_response.status_code == 403

    admin_token = _token(role="ADMIN", user_id="admin-1")
    admin_response = client.post(
        "/field-reports/visits/report-1/finalize",
        headers=_headers(admin_token),
        files=files,
    )
    assert admin_response.status_code == 403

    supervisor_token = _token(role="SUPERVISOR")
    allowed = client.post(
        "/field-reports/visits/report-1/finalize",
        headers=_headers(supervisor_token),
        files=files,
    )
    assert allowed.status_code == 202


def test_finalize_is_idempotent_for_same_report(monkeypatch) -> None:
    reports = FakeVisitReportRepository()
    runs = FakeFinalizeRunRepository()
    _closed_report(reports)
    service = _finalize_service(reports=reports, runs=runs)
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
    assert len(runs.records) == 1


def test_finalize_status_endpoint_returns_run_snapshot(monkeypatch) -> None:
    reports = FakeVisitReportRepository()
    runs = FakeFinalizeRunRepository()
    _closed_report(reports)
    service = _finalize_service(reports=reports, runs=runs)
    client = _setup_client(monkeypatch, finalize_service=service)

    supervisor_token = _token(role="SUPERVISOR")
    finalize = client.post(
        "/field-reports/visits/report-1/finalize",
        headers=_headers(supervisor_token),
        files={"file": ("visit.pdf", FAKE_PDF, "application/pdf")},
    )
    run_id = finalize.json()["finalize_run_id"]

    status = client.get(
        "/field-reports/visits/report-1/finalize-status",
        headers=_headers(supervisor_token),
    )
    assert status.status_code == 200
    payload = status.json()
    assert payload["report_id"] == "report-1"
    assert payload["status"] == "FINALIZING"
    assert payload["finalize_run"]["id"] == run_id
    assert payload["finalize_run"]["status"] == "COMPLETED"
    completed = payload["finalize_run"]["steps_completed"]
    pre_len = len(INFRASTRUCTURE_PRE_STEP_ORDER)
    assert completed[pre_len : pre_len + len(CORE_FINALIZE_STEP_ORDER)] == list(
        CORE_FINALIZE_STEP_ORDER
    )


def test_new_construction_scheme_is_valid() -> None:
    assert "NEW_CONSTRUCTION" in VALID_PROJECT_SCHEMES
    assert project_scheme_label_he("NEW_CONSTRUCTION") == "בנייה חדשה"


def test_finalize_rejects_in_progress_report(monkeypatch) -> None:
    reports = FakeVisitReportRepository()
    _closed_report(reports, status="IN_PROGRESS")
    service = _finalize_service(reports=reports)
    client = _setup_client(monkeypatch, finalize_service=service)

    response = client.post(
        "/field-reports/visits/report-1/finalize",
        headers=_headers(_token(role="SUPERVISOR")),
        files={"file": ("visit.pdf", FAKE_PDF, "application/pdf")},
    )
    assert response.status_code == 409


def test_finalize_requires_pdf_file(monkeypatch) -> None:
    reports = FakeVisitReportRepository()
    _closed_report(reports)
    service = _finalize_service(reports=reports)
    client = _setup_client(monkeypatch, finalize_service=service)

    response = client.post(
        "/field-reports/visits/report-1/finalize",
        headers=_headers(_token(role="SUPERVISOR")),
    )
    assert response.status_code == 422
