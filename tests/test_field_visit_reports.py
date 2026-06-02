from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app
from app.auth.jwt_service import JWTService
from app.services.field_report_module_service import (
    FieldReportModuleService,
)
from app.services.field_report_organization_profile_service import (
    FieldReportOrganizationProfileService,
)
from app.config.field_report_construction_progress import (
    DEFAULT_STRUCTURE_SITE_PROGRESS_ROWS,
)
from app.config.field_report_pdf_defaults import (
    DEFAULT_WINTER_RECOMMENDATIONS_HE,
)
from app.services.field_visit_report_service import (
    FieldVisitReportService,
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
        token_id="t-visit-1",
    )


def _headers(token: str, org_id: str = "org-1") -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "X-Organization-ID": org_id,
    }


class FakeVisitReportLineRepository:
    def __init__(self) -> None:
        self.records: dict[str, dict] = {}
        self._counter = 0

    def is_storage_available(self) -> bool:
        return True

    def list_by_report(self, report_id: str) -> list[dict]:
        lines = [
            record
            for record in self.records.values()
            if record["report_id"] == report_id
        ]
        return sorted(lines, key=lambda line: line["sort_order"])

    def get_by_id(self, line_id: str) -> dict | None:
        return self.records.get(line_id)

    def next_sort_order(self, report_id: str) -> int:
        lines = self.list_by_report(report_id)
        if not lines:
            return 0
        return max(int(line["sort_order"]) for line in lines) + 1

    def create(self, payload: dict) -> dict:
        self._counter += 1
        line_id = f"line-{self._counter}"
        record = {"id": line_id, **payload}
        self.records[line_id] = record
        return record

    def update(self, line_id: str, payload: dict) -> dict | None:
        record = self.records.get(line_id)
        if not record:
            return None
        record.update(payload)
        return record

    def delete(self, line_id: str) -> bool:
        return self.records.pop(line_id, None) is not None


class FakeVisitReportRepository:
    def __init__(self) -> None:
        self.records: dict[str, dict] = {}
        self._counter = 0

    def is_storage_available(self) -> bool:
        return True

    def list_by_organization(
        self,
        organization_id: str,
        *,
        status: str | None = None,
    ) -> list[dict]:
        items = [
            record
            for record in self.records.values()
            if record["organization_id"] == organization_id
        ]

        if status:
            items = [
                record for record in items if record["status"] == status
            ]

        return sorted(
            items,
            key=lambda record: record["updated_at"],
            reverse=True,
        )

    def get_by_id(self, report_id: str) -> dict | None:
        return self.records.get(report_id)

    def get_open_for_project(
        self,
        *,
        organization_id: str,
        project_id: str,
    ) -> dict | None:
        for record in self.records.values():
            if (
                record["organization_id"] == organization_id
                and record["project_id"] == project_id
                and record["status"] == "IN_PROGRESS"
            ):
                return record
        return None

    def create(self, **kwargs) -> dict:
        self._counter += 1
        report_id = f"report-{self._counter}"
        record = {
            "id": report_id,
            "status": "IN_PROGRESS",
            "updated_at": "2026-06-01T12:00:00+00:00",
            "created_at": "2026-06-01T12:00:00+00:00",
            **kwargs,
        }
        self.records[report_id] = record
        return record

    def update(self, report_id: str, payload: dict) -> dict | None:
        record = self.records.get(report_id)
        if not record:
            return None
        record.update(payload)
        return record


class FakeProjectRepository:
    def get_project_by_id(self, project_id: str) -> dict | None:
        if project_id == "missing":
            return None
        return {
            "id": project_id,
            "organization_id": "org-1",
            "project_name": "פרויקט בדיקה",
        }

    def get_projects_by_organization(
        self,
        organization_id: str,
    ) -> list[dict]:
        return [
            {
                "id": "project-1",
                "organization_id": organization_id,
                "project_name": "פרויקט בדיקה",
            }
        ]


class FakeReportProcessingService:
    def __init__(self, *, should_succeed: bool = True) -> None:
        self.should_succeed = should_succeed
        self.calls: list[dict] = []

    def process_uploaded_report(
        self,
        *,
        project_id: str,
        filename: str,
        file_path: str,
    ) -> dict:
        self.calls.append(
            {
                "project_id": project_id,
                "filename": filename,
                "file_path": file_path,
            }
        )
        if self.should_succeed:
            return {"success": True}
        return {
            "success": False,
            "error_code": "CORE_PIPELINE_FAILED",
            "error_message": "core failed",
        }


class FakeModuleRepository:
    def __init__(self) -> None:
        self.records: dict[str, dict] = {
            "org-1": {
                "organization_id": "org-1",
                "is_enabled": True,
            }
        }

    def is_storage_available(self) -> bool:
        return True

    def get_by_organization_id(self, organization_id: str) -> dict | None:
        return self.records.get(organization_id)

    def list_all(self) -> list[dict]:
        return list(self.records.values())

    def upsert_status(self, **kwargs) -> dict:
        org_id = kwargs["organization_id"]
        self.records[org_id] = kwargs
        return kwargs


class FakeOrganizationRepository:
    def get_by_id(self, organization_id: str) -> dict | None:
        return {
            "id": organization_id,
            "organization_name": "Org",
        }


def _setup_client(
    monkeypatch,
    *,
    report_processing_service: FakeReportProcessingService | None = None,
    module_enabled: bool = True,
) -> TestClient:
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
    visit_service = FieldVisitReportService(
        report_repository=FakeVisitReportRepository(),
        line_repository=FakeVisitReportLineRepository(),
        project_repository=FakeProjectRepository(),
        organization_profile_service=organization_profile_service,
        report_processing_service=(
            report_processing_service
            or FakeReportProcessingService()
        ),
    )

    monkeypatch.setattr(
        "app.main.field_report_module_service",
        module_service,
    )
    monkeypatch.setattr(
        "app.main.field_visit_report_service",
        visit_service,
    )
    monkeypatch.setattr(
        "app.main.project_repository",
        FakeProjectRepository(),
    )

    app.state.field_report_module_service = module_service

    return TestClient(app)


def test_visit_types_and_create_list(monkeypatch):
    client = _setup_client(monkeypatch)
    token = _token()

    types_response = client.get(
        "/field-reports/visit-types",
        headers=_headers(token),
    )
    assert types_response.status_code == 200
    types = types_response.json()["visit_types"]
    assert len(types) == 2
    codes = {item["code"] for item in types}
    assert codes == {"STRUCTURE_SITE", "FINISHING_APARTMENTS"}

    create_response = client.post(
        "/field-reports/visits",
        headers=_headers(token),
        json={
            "project_id": "project-1",
            "visit_type": "STRUCTURE_SITE",
            "visit_date": "2026-06-01",
        },
    )
    assert create_response.status_code == 200
    created = create_response.json()
    assert created["status"] == "IN_PROGRESS"
    assert created["visit_type_label_he"] == "שלד / אתר"
    header_fields = created["header_fields"]
    assert header_fields["project_updates"] == []
    assert header_fields["contractor_notes"] == []
    assert header_fields["winter_recommendations"] == (
        DEFAULT_WINTER_RECOMMENDATIONS_HE
    )
    assert header_fields["construction_progress"] == (
        DEFAULT_STRUCTURE_SITE_PROGRESS_ROWS
    )

    duplicate_response = client.post(
        "/field-reports/visits",
        headers=_headers(token),
        json={
            "project_id": "project-1",
            "visit_type": "FINISHING_APARTMENTS",
            "visit_date": "2026-06-02",
        },
    )
    assert duplicate_response.status_code == 409

    list_response = client.get(
        "/field-reports/visits",
        headers=_headers(token),
    )
    assert list_response.status_code == 200
    assert list_response.json()["total"] == 1


def test_viewer_cannot_create_visit_report(monkeypatch):
    client = _setup_client(monkeypatch)
    token = _token(role="VIEWER")

    response = client.post(
        "/field-reports/visits",
        headers=_headers(token),
        json={
            "project_id": "project-1",
            "visit_type": "STRUCTURE_SITE",
            "visit_date": "2026-06-01",
        },
    )
    assert response.status_code == 403


def test_cannot_create_visit_report_when_module_disabled(monkeypatch):
    client = _setup_client(monkeypatch, module_enabled=False)
    token = _token()

    response = client.post(
        "/field-reports/visits",
        headers=_headers(token),
        json={
            "project_id": "project-1",
            "visit_type": "STRUCTURE_SITE",
            "visit_date": "2026-06-01",
        },
    )
    assert response.status_code == 403


def test_create_line_from_catalog_and_free_text(monkeypatch):
    client = _setup_client(monkeypatch)
    token = _token()

    create_response = client.post(
        "/field-reports/visits",
        headers=_headers(token),
        json={
            "project_id": "project-1",
            "visit_type": "STRUCTURE_SITE",
            "visit_date": "2026-06-01",
        },
    )
    report_id = create_response.json()["id"]

    catalog_line = client.post(
        f"/field-reports/visits/{report_id}/lines",
        headers=_headers(token),
        json={"issue_id": "STR-02-001"},
    )
    assert catalog_line.status_code == 200
    catalog_payload = catalog_line.json()
    assert catalog_payload["issue_id"] == "STR-02-001"
    assert catalog_payload["standard_ref"]
    assert catalog_payload["has_catalog_issue"] is True

    free_line = client.post(
        f"/field-reports/visits/{report_id}/lines",
        headers=_headers(token),
        json={
            "description": "ממצא חופשי לבדיקה",
            "location": "קומה 3",
        },
    )
    assert free_line.status_code == 200
    assert free_line.json()["issue_id"] is None

    detail = client.get(
        f"/field-reports/visits/{report_id}",
        headers=_headers(token),
    )
    assert detail.status_code == 200
    assert detail.json()["line_count"] == 2

    line_id = catalog_payload["id"]
    clear_catalog = client.patch(
        f"/field-reports/visits/{report_id}/lines/{line_id}",
        headers=_headers(token),
        json={"issue_id": None, "description": "תיאור חופשי אחרי המרה"},
    )
    assert clear_catalog.status_code == 200
    cleared = clear_catalog.json()
    assert cleared["issue_id"] is None
    assert cleared["standard_ref"] is None
    assert cleared["has_catalog_issue"] is False


def test_catalog_endpoint_includes_family_labels(monkeypatch):
    client = _setup_client(monkeypatch)
    token = _token()

    response = client.get(
        "/field-reports/catalog?visit_type=STRUCTURE_SITE",
        headers=_headers(token),
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["families"]
    assert payload["families"][0].get("label_he")


def test_line_catalog_warning_helpers():
    from app.services.field_visit_report_service import (
        _catalog_sync_state,
        _line_catalog_warning,
    )

    assert _line_catalog_warning(
        issue_id="STR-99-999",
        line_catalog_version="1.0.0",
        current_catalog_version="1.1.0",
        catalog_issue=None,
    )

    assert _catalog_sync_state(
        report_catalog_version="1.0.0",
        current_catalog_version="1.1.0",
    )["is_current"] is False


def test_upload_and_delete_line_photo(monkeypatch, tmp_path):
    client = _setup_client(monkeypatch)
    token = _token()

    from app.services.field_visit_report_photo_service import (
        FieldVisitReportPhotoService,
    )

    visit_service = FieldVisitReportService(
        report_repository=FakeVisitReportRepository(),
        line_repository=FakeVisitReportLineRepository(),
        project_repository=FakeProjectRepository(),
        organization_profile_service=FieldReportOrganizationProfileService(
            organization_repository=FakeOrganizationRepository(),
            module_service=FieldReportModuleService(
                module_repository=FakeModuleRepository(),
                organization_repository=FakeOrganizationRepository(),
            ),
        ),
        photo_service=FieldVisitReportPhotoService(
            photos_root=tmp_path
        ),
    )
    monkeypatch.setattr(
        "app.main.field_visit_report_service",
        visit_service,
    )

    create_response = client.post(
        "/field-reports/visits",
        headers=_headers(token),
        json={
            "project_id": "project-1",
            "visit_type": "STRUCTURE_SITE",
            "visit_date": "2026-06-01",
        },
    )
    report_id = create_response.json()["id"]

    line_response = client.post(
        f"/field-reports/visits/{report_id}/lines",
        headers=_headers(token),
        json={"description": "שורה עם תמונה"},
    )
    line_id = line_response.json()["id"]

    upload_response = client.post(
        f"/field-reports/visits/{report_id}/lines/{line_id}/photo",
        headers=_headers(token),
        files={
            "file": ("finding.jpg", b"fake-jpeg-bytes", "image/jpeg"),
        },
    )
    assert upload_response.status_code == 200
    uploaded = upload_response.json()
    assert uploaded["has_photo"] is True
    assert uploaded["photo_url"]

    photo_response = client.get(
        f"/field-reports/visits/{report_id}/lines/{line_id}/photo",
        headers=_headers(token),
    )
    assert photo_response.status_code == 200
    assert photo_response.content == b"fake-jpeg-bytes"

    delete_response = client.delete(
        f"/field-reports/visits/{report_id}/lines/{line_id}/photo",
        headers=_headers(token),
    )
    assert delete_response.status_code == 200
    assert delete_response.json()["has_photo"] is False


def test_close_preview_and_close_report(monkeypatch):
    client = _setup_client(monkeypatch)
    token = _token()

    create_response = client.post(
        "/field-reports/visits",
        headers=_headers(token),
        json={
            "project_id": "project-1",
            "visit_type": "STRUCTURE_SITE",
            "visit_date": "2026-06-01",
        },
    )
    report_id = create_response.json()["id"]

    client.post(
        f"/field-reports/visits/{report_id}/lines",
        headers=_headers(token),
        json={"description": "שורה תקינה"},
    )
    client.post(
        f"/field-reports/visits/{report_id}/lines",
        headers=_headers(token),
        json={"description": "   "},
    )

    preview_response = client.get(
        f"/field-reports/visits/{report_id}/close-preview",
        headers=_headers(token),
    )
    assert preview_response.status_code == 200
    preview = preview_response.json()
    assert preview["line_count"] == 2
    assert preview["empty_line_count"] == 1
    assert preview["warnings"]

    close_response = client.post(
        f"/field-reports/visits/{report_id}/close",
        headers=_headers(token),
    )
    assert close_response.status_code == 200
    closed = close_response.json()
    assert closed["status"] == "CLOSED"
    assert closed["is_editable"] is False
    assert closed["closed_at"]
    assert closed["close_preview"]["empty_line_count"] == 1

    second_close = client.post(
        f"/field-reports/visits/{report_id}/close",
        headers=_headers(token),
    )
    assert second_close.status_code == 409

    reopen_response = client.post(
        f"/field-reports/visits/{report_id}/reopen",
        headers=_headers(token),
    )
    assert reopen_response.status_code == 200
    reopened = reopen_response.json()
    assert reopened["status"] == "IN_PROGRESS"
    assert reopened["is_editable"] is True
    assert reopened["can_reopen"] is False
    assert reopened["was_closed"] is True
    assert reopened["closed_at"]

    patch_response = client.patch(
        f"/field-reports/visits/{report_id}",
        headers=_headers(token),
        json={
            "header_fields": {
                **reopened["header_fields"],
                "inspector_notes": "עודכן אחרי סגירה",
            },
        },
    )
    assert patch_response.status_code == 200

    second_close_after_reopen = client.post(
        f"/field-reports/visits/{report_id}/close",
        headers=_headers(token),
    )
    assert second_close_after_reopen.status_code == 200
    assert second_close_after_reopen.json()["status"] == "CLOSED"


def test_reopen_rejects_non_closed_report(monkeypatch):
    client = _setup_client(monkeypatch)
    token = _token()

    create_response = client.post(
        "/field-reports/visits",
        headers=_headers(token),
        json={
            "project_id": "project-1",
            "visit_type": "STRUCTURE_SITE",
            "visit_date": "2026-06-01",
        },
    )
    report_id = create_response.json()["id"]

    reopen_response = client.post(
        f"/field-reports/visits/{report_id}/reopen",
        headers=_headers(token),
    )
    assert reopen_response.status_code == 409


def test_request_send_to_core_from_closed_report(monkeypatch):
    fake_processing = FakeReportProcessingService()
    client = _setup_client(
        monkeypatch,
        report_processing_service=fake_processing,
    )
    token = _token()

    create_response = client.post(
        "/field-reports/visits",
        headers=_headers(token),
        json={
            "project_id": "project-1",
            "visit_type": "STRUCTURE_SITE",
            "visit_date": "2026-06-01",
        },
    )
    report_id = create_response.json()["id"]

    close_response = client.post(
        f"/field-reports/visits/{report_id}/close",
        headers=_headers(token),
    )
    assert close_response.status_code == 200
    closed = close_response.json()
    assert closed["can_send_to_core"] is True

    send_response = client.post(
        f"/field-reports/visits/{report_id}/request-send",
        headers=_headers(token),
        files={
            "file": (
                f"{report_id}.pdf",
                b"%PDF-1.4\nfake-pdf\n%%EOF\n",
                "application/pdf",
            ),
        },
    )
    assert send_response.status_code == 200
    pending = send_response.json()
    assert pending["status"] == "LOCKED"
    assert pending["status_label_he"] == "נעול"
    assert pending["locked_at"] is not None
    assert pending["is_editable"] is False
    assert pending["can_reopen"] is False
    assert pending["can_send_to_core"] is False
    assert len(fake_processing.calls) == 1
    assert fake_processing.calls[0]["project_id"] == "project-1"

    second_send = client.post(
        f"/field-reports/visits/{report_id}/request-send",
        headers=_headers(token),
        files={
            "file": (
                f"{report_id}.pdf",
                b"%PDF-1.4\nfake-pdf\n%%EOF\n",
                "application/pdf",
            ),
        },
    )
    assert second_send.status_code == 200
    second_pending = second_send.json()
    assert second_pending["status"] == "LOCKED"
    assert second_pending["status_label_he"] == "נעול"
    assert len(fake_processing.calls) == 1

    reopen_response = client.post(
        f"/field-reports/visits/{report_id}/reopen",
        headers=_headers(token),
    )
    assert reopen_response.status_code == 409


def test_request_send_to_core_returns_conflict_when_core_pipeline_fails(monkeypatch):
    fake_processing = FakeReportProcessingService(should_succeed=False)
    client = _setup_client(
        monkeypatch,
        report_processing_service=fake_processing,
    )
    token = _token()

    create_response = client.post(
        "/field-reports/visits",
        headers=_headers(token),
        json={
            "project_id": "project-1",
            "visit_type": "STRUCTURE_SITE",
            "visit_date": "2026-06-01",
        },
    )
    report_id = create_response.json()["id"]

    close_response = client.post(
        f"/field-reports/visits/{report_id}/close",
        headers=_headers(token),
    )
    assert close_response.status_code == 200

    send_response = client.post(
        f"/field-reports/visits/{report_id}/request-send",
        headers=_headers(token),
        files={
            "file": (
                f"{report_id}.pdf",
                b"%PDF-1.4\nfake-pdf\n%%EOF\n",
                "application/pdf",
            ),
        },
    )
    assert send_response.status_code == 409
    error_payload = send_response.json()
    assert (
        error_payload["error"]["details"]["error_code"]
        == "CORE_PIPELINE_FAILED"
    )
    assert error_payload["error"]["details"]["retryable"] is True

    report_response = client.get(
        f"/field-reports/visits/{report_id}",
        headers=_headers(token),
    )
    assert report_response.status_code == 200
    assert report_response.json()["status"] == "CLOSED"


def test_request_send_rejects_in_progress_report(monkeypatch):
    client = _setup_client(monkeypatch)
    token = _token()

    create_response = client.post(
        "/field-reports/visits",
        headers=_headers(token),
        json={
            "project_id": "project-1",
            "visit_type": "STRUCTURE_SITE",
            "visit_date": "2026-06-01",
        },
    )
    report_id = create_response.json()["id"]

    send_response = client.post(
        f"/field-reports/visits/{report_id}/request-send",
        headers=_headers(token),
        files={
            "file": (
                f"{report_id}.pdf",
                b"%PDF-1.4\nfake-pdf\n%%EOF\n",
                "application/pdf",
            ),
        },
    )
    assert send_response.status_code == 409
    error_payload = send_response.json()
    assert (
        error_payload["error"]["details"]["error_code"]
        == "FIELD_VISIT_REPORT_SEND_INVALID_STATUS"
    )
    assert error_payload["error"]["details"]["retryable"] is False


def test_report_includes_organization_profile_snapshot(monkeypatch):
    client = _setup_client(monkeypatch)
    token = _token()

    create_response = client.post(
        "/field-reports/visits",
        headers=_headers(token),
        json={
            "project_id": "project-1",
            "visit_type": "STRUCTURE_SITE",
            "visit_date": "2026-06-01",
        },
    )
    assert create_response.status_code == 200
    created = create_response.json()
    assert created["organization_profile_snapshot"]
    assert created["organization_profile_snapshot"]["organization_name"] == "Org"

    report_id = created["id"]
    get_response = client.get(
        f"/field-reports/visits/{report_id}",
        headers=_headers(token),
    )
    assert get_response.status_code == 200
    fetched = get_response.json()
    assert fetched["organization_profile_snapshot"]["organization_id"] == "org-1"


def test_build_close_preview_helpers():
    from app.services.field_visit_report_service import (
        _build_close_preview,
        _line_is_empty,
    )

    assert _line_is_empty({"description": "  "}) is True
    assert _line_is_empty({"description": "תיאור"}) is False

    preview = _build_close_preview(
        [
            {"id": "line-1", "description": "מלא"},
            {"id": "line-2", "description": ""},
        ]
    )
    assert preview["empty_line_count"] == 1
    assert preview["empty_line_ids"] == ["line-2"]


def test_catalog_endpoint_filters_structure_site(monkeypatch):
    client = _setup_client(monkeypatch)
    token = _token()

    response = client.get(
        "/field-reports/catalog?visit_type=STRUCTURE_SITE",
        headers=_headers(token),
    )
    assert response.status_code == 200
    payload = response.json()
    families = {issue["top_family"] for issue in payload["issues"]}
    assert "STRUCTURAL_WORKS" in families
    assert "FINISHING_WORKS" not in families
