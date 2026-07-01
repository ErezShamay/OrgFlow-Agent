from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.exceptions.exceptions import NotFoundError, ValidationError
from app.main import app
from app.services.field_report_module_service import (
    FieldReportModuleService,
)
from app.services.field_report_organization_profile_service import (
    FieldReportOrganizationProfileService,
)
from app.services.field_visit_report_photo_service import (
    FieldVisitReportPhotoService,
)
from app.services.field_visit_report_service import FieldVisitReportService
from tests.test_field_visit_report_sync import (
    CLIENT_LINE_ONE,
    CLIENT_REPORT_UUID,
    SYNC_BODY,
    _setup_sync_client,
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
    _token,
)

ORG_ID = "org-1"
UNKNOWN_LINE_UUID = "00000000-0000-4000-8000-000000000099"
OTHER_REPORT_LINE_UUID = "99999999-9999-4999-8999-999999999998"
WRONG_IDEMPOTENCY_KEY = "d4444444-4444-4444-8444-444444444444"
IMAGE_BYTES = b"fake-jpeg-bytes-for-sync-photo"


def _photo_service(tmp_path: Path) -> FieldVisitReportPhotoService:
    return FieldVisitReportPhotoService(photos_root=tmp_path)


def _service(
    *,
    reports: FakeVisitReportRepository,
    lines: FakeVisitReportLineRepository,
    photos_root: Path,
) -> FieldVisitReportService:
    module_service = FieldReportModuleService(
        module_repository=FakeModuleRepository(),
        organization_repository=FakeOrganizationRepository(),
    )
    return FieldVisitReportService(
        report_repository=reports,
        line_repository=lines,
        line_photo_repository=FakeVisitReportLinePhotoRepository(),
        project_repository=FakeProjectRepository(),
        organization_profile_service=FieldReportOrganizationProfileService(
            organization_repository=FakeOrganizationRepository(),
            module_service=module_service,
        ),
        photo_service=_photo_service(photos_root),
    )


def _seed_synced_report(
    service: FieldVisitReportService,
) -> tuple[str, str]:
    result = service.sync_visit_report(
        organization_id=ORG_ID,
        actor_profile_id="supervisor-1",
        client_report_uuid=CLIENT_REPORT_UUID,
        project_id=SYNC_BODY["project_id"],
        visit_type=SYNC_BODY["visit_type"],
        visit_date=SYNC_BODY["visit_date"],
        header_fields=SYNC_BODY["header_fields"],
        lines=SYNC_BODY["lines"],
    )
    line = result["report"]["lines"][0]
    return str(result["id"]), str(line["id"])


def test_add_line_photo_by_client_uuids_after_sync(tmp_path):
    reports = FakeVisitReportRepository()
    lines = FakeVisitReportLineRepository()
    service = _service(
        reports=reports,
        lines=lines,
        photos_root=tmp_path,
    )
    _seed_synced_report(service)

    updated = service.add_line_photo_by_client_uuids(
        organization_id=ORG_ID,
        client_report_uuid=CLIENT_REPORT_UUID,
        client_line_uuid=CLIENT_LINE_ONE,
        content=IMAGE_BYTES,
        content_type="image/jpeg",
        filename="finding.jpg",
        idempotency_key=CLIENT_LINE_ONE,
    )

    assert updated["has_photo"] is True
    assert updated["client_line_uuid"] == CLIENT_LINE_ONE
    assert len(updated["photo_ids"]) == 1
    stored = lines.get_by_client_line_uuid(CLIENT_LINE_ONE)
    assert stored is not None
    assert stored.get("photo_storage_path")


def test_add_line_photo_rejects_unknown_client_line(tmp_path):
    service = _service(
        reports=FakeVisitReportRepository(),
        lines=FakeVisitReportLineRepository(),
        photos_root=tmp_path,
    )
    _seed_synced_report(service)

    with pytest.raises(NotFoundError):
        service.add_line_photo_by_client_uuids(
            organization_id=ORG_ID,
            client_report_uuid=CLIENT_REPORT_UUID,
            client_line_uuid=UNKNOWN_LINE_UUID,
            content=IMAGE_BYTES,
            content_type="image/jpeg",
        )


def test_add_line_photo_rejects_line_on_other_report(tmp_path):
    reports = FakeVisitReportRepository()
    lines = FakeVisitReportLineRepository()
    service = _service(
        reports=reports,
        lines=lines,
        photos_root=tmp_path,
    )
    _seed_synced_report(service)

    other_report = reports.create(
        organization_id=ORG_ID,
        project_id="project-2",
        created_by_profile_id="supervisor-1",
        visit_type="STRUCTURE_SITE",
        visit_date="2026-06-04",
        client_report_uuid="f9999999-9999-4999-8999-999999999999",
    )
    lines.create(
        {
            "report_id": str(other_report["id"]),
            "organization_id": ORG_ID,
            "client_line_uuid": OTHER_REPORT_LINE_UUID,
            "sort_order": 0,
            "description": "שורה בדוח אחר",
        }
    )

    with pytest.raises(NotFoundError):
        service.add_line_photo_by_client_uuids(
            organization_id=ORG_ID,
            client_report_uuid=CLIENT_REPORT_UUID,
            client_line_uuid=OTHER_REPORT_LINE_UUID,
            content=IMAGE_BYTES,
            content_type="image/jpeg",
        )


def test_add_line_photo_rejects_idempotency_key_mismatch(tmp_path):
    service = _service(
        reports=FakeVisitReportRepository(),
        lines=FakeVisitReportLineRepository(),
        photos_root=tmp_path,
    )
    _seed_synced_report(service)

    with pytest.raises(ValidationError):
        service.add_line_photo_by_client_uuids(
            organization_id=ORG_ID,
            client_report_uuid=CLIENT_REPORT_UUID,
            client_line_uuid=CLIENT_LINE_ONE,
            content=IMAGE_BYTES,
            content_type="image/jpeg",
            idempotency_key=WRONG_IDEMPOTENCY_KEY,
        )


def test_post_sync_line_photo_endpoint(monkeypatch, tmp_path):
    reports = FakeVisitReportRepository()
    lines = FakeVisitReportLineRepository()
    module_repository = FakeModuleRepository()
    module_repository.records["org-1"]["is_enabled"] = True
    module_service = FieldReportModuleService(
        module_repository=module_repository,
        organization_repository=FakeOrganizationRepository(),
    )
    visit_service = FieldVisitReportService(
        report_repository=reports,
        line_repository=lines,
        line_photo_repository=FakeVisitReportLinePhotoRepository(),
        project_repository=FakeProjectRepository(),
        organization_profile_service=FieldReportOrganizationProfileService(
            organization_repository=FakeOrganizationRepository(),
            module_service=module_service,
        ),
        photo_service=_photo_service(tmp_path),
        report_processing_service=FakeReportProcessingService(),
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
    client = TestClient(app)
    token = _token()

    sync_response = client.put(
        "/field-reports/visits/sync",
        headers=_headers(token),
        json=SYNC_BODY,
    )
    assert sync_response.status_code == 200

    upload_response = client.post(
        f"/field-reports/visits/sync/{CLIENT_REPORT_UUID}/lines/"
        f"{CLIENT_LINE_ONE}/photos",
        headers={
            **_headers(token),
            "X-Idempotency-Key": CLIENT_LINE_ONE,
        },
        files={
            "file": ("finding.jpg", IMAGE_BYTES, "image/jpeg"),
        },
    )
    assert upload_response.status_code == 200
    payload = upload_response.json()
    assert payload["has_photo"] is True
    assert payload["client_line_uuid"] == CLIENT_LINE_ONE
    assert len(payload["photo_ids"]) == 1

    photo_id = payload["photo_ids"][0]
    photo_response = client.get(
        f"/field-reports/visits/{payload['report_id']}/lines/"
        f"{payload['id']}/photos/{photo_id}",
        headers=_headers(token),
    )
    assert photo_response.status_code == 200
    assert photo_response.content == IMAGE_BYTES


def test_post_sync_line_photo_before_sync_returns_404(monkeypatch):
    client, _reports, _lines = _setup_sync_client(monkeypatch)
    token = _token()

    response = client.post(
        f"/field-reports/visits/sync/{CLIENT_REPORT_UUID}/lines/"
        f"{CLIENT_LINE_ONE}/photos",
        headers=_headers(token),
        files={
            "file": ("finding.jpg", IMAGE_BYTES, "image/jpeg"),
        },
    )
    assert response.status_code == 404


def test_post_sync_line_photo_idempotency_key_mismatch_http(monkeypatch, tmp_path):
    reports = FakeVisitReportRepository()
    lines = FakeVisitReportLineRepository()
    module_repository = FakeModuleRepository()
    module_repository.records["org-1"]["is_enabled"] = True
    module_service = FieldReportModuleService(
        module_repository=module_repository,
        organization_repository=FakeOrganizationRepository(),
    )
    visit_service = FieldVisitReportService(
        report_repository=reports,
        line_repository=lines,
        line_photo_repository=FakeVisitReportLinePhotoRepository(),
        project_repository=FakeProjectRepository(),
        organization_profile_service=FieldReportOrganizationProfileService(
            organization_repository=FakeOrganizationRepository(),
            module_service=module_service,
        ),
        photo_service=_photo_service(tmp_path),
        report_processing_service=FakeReportProcessingService(),
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
    client = TestClient(app)
    token = _token()

    client.put(
        "/field-reports/visits/sync",
        headers=_headers(token),
        json=SYNC_BODY,
    )

    response = client.post(
        f"/field-reports/visits/sync/{CLIENT_REPORT_UUID}/lines/"
        f"{CLIENT_LINE_ONE}/photos",
        headers={
            **_headers(token),
            "X-Idempotency-Key": WRONG_IDEMPOTENCY_KEY,
        },
        files={
            "file": ("finding.jpg", IMAGE_BYTES, "image/jpeg"),
        },
    )
    assert response.status_code == 400
    assert "Idempotency" in response.json()["error"]["message"]
