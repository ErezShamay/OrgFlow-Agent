from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.exceptions.exceptions import ConflictError, ValidationError
from app.main import app
from app.auth.jwt_service import JWTService
from app.services.field_report_module_service import (
    FieldReportModuleService,
)
from app.services.field_report_organization_profile_service import (
    FieldReportOrganizationProfileService,
)
from app.services.field_visit_report_service import FieldVisitReportService
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

WRONG_IDEMPOTENCY_KEY = "d4444444-4444-4444-8444-444444444444"
SYNC_REPORT_HTTP = "e5555555-5555-4555-8555-555555555555"
SYNC_LINE_HTTP_ONE = "f6666666-6666-4666-8666-666666666666"
SYNC_REPORT_CONFLICT = "77777777-7777-4777-8777-777777777777"
SYNC_LINE_CONFLICT = "88888888-8888-4888-8888-888888888888"

CLIENT_REPORT_UUID = "a1111111-1111-4111-8111-111111111111"
CLIENT_LINE_ONE = "b2222222-2222-4222-8222-222222222222"
CLIENT_LINE_TWO = "c3333333-3333-4333-8333-333333333333"
ORG_ID = "org-1"

SYNC_BODY = {
    "client_report_uuid": CLIENT_REPORT_UUID,
    "project_id": "project-1",
    "visit_type": "STRUCTURE_SITE",
    "visit_date": "2026-06-03",
    "header_fields": {"contractor_notes": ["שטח"]},
    "lines": [
        {
            "client_line_uuid": CLIENT_LINE_ONE,
            "sort_order": 1,
            "description": "ממצא א",
        },
        {
            "client_line_uuid": CLIENT_LINE_TWO,
            "sort_order": 2,
            "description": "ממצא ב",
        },
    ],
}


def _sync_body_kwargs(*, lines: list[dict] | None = None) -> dict:
    kwargs = {
        key: SYNC_BODY[key]
        for key in SYNC_BODY
        if key != "lines"
    }
    kwargs["lines"] = lines if lines is not None else SYNC_BODY["lines"]
    return kwargs


def _service(
    *,
    reports: FakeVisitReportRepository | None = None,
    lines: FakeVisitReportLineRepository | None = None,
) -> FieldVisitReportService:
    return FieldVisitReportService(
        report_repository=reports or FakeVisitReportRepository(),
        line_repository=lines or FakeVisitReportLineRepository(),
        line_photo_repository=FakeVisitReportLinePhotoRepository(),
        project_repository=FakeProjectRepository(),
    )


def _setup_sync_client(
    monkeypatch,
) -> tuple[TestClient, FakeVisitReportRepository, FakeVisitReportLineRepository]:
    reports = FakeVisitReportRepository()
    lines = FakeVisitReportLineRepository()
    module_repository = FakeModuleRepository()
    module_repository.records["org-1"]["is_enabled"] = True

    module_service = FieldReportModuleService(
        module_repository=module_repository,
        organization_repository=FakeOrganizationRepository(),
    )
    organization_profile_service = FieldReportOrganizationProfileService(
        organization_repository=FakeOrganizationRepository(),
        module_service=module_service,
    )
    visit_service = FieldVisitReportService(
        report_repository=reports,
        line_repository=lines,
        project_repository=FakeProjectRepository(),
        organization_profile_service=organization_profile_service,
        report_processing_service=FakeReportProcessingService(),
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

    return TestClient(app), reports, lines


def test_sync_visit_report_requires_client_report_uuid():
    service = _service()

    with pytest.raises(ValidationError):
        service.sync_visit_report(
            organization_id=ORG_ID,
            actor_profile_id="supervisor-1",
            client_report_uuid="",
            project_id="project-1",
            visit_type="STRUCTURE_SITE",
            visit_date="2026-06-03",
        )


def test_sync_visit_report_creates_report_with_lines():
    reports = FakeVisitReportRepository()
    lines = FakeVisitReportLineRepository()
    service = _service(reports=reports, lines=lines)

    result = service.sync_visit_report(
        organization_id=ORG_ID,
        actor_profile_id="supervisor-1",
        **{
            key: SYNC_BODY[key]
            for key in SYNC_BODY
            if key != "lines"
        },
        lines=SYNC_BODY["lines"],
        idempotency_key=CLIENT_REPORT_UUID,
    )

    assert result["created"] is True
    assert result["client_report_uuid"] == CLIENT_REPORT_UUID
    assert result["report"]["lines"]
    assert len(result["report"]["lines"]) == 2
    assert reports.get_by_client_report_uuid(CLIENT_REPORT_UUID)


def test_sync_visit_report_updates_existing_idempotently():
    reports = FakeVisitReportRepository()
    lines = FakeVisitReportLineRepository()
    service = _service(reports=reports, lines=lines)

    first = service.sync_visit_report(
        organization_id=ORG_ID,
        actor_profile_id="supervisor-1",
        **{
            key: SYNC_BODY[key]
            for key in SYNC_BODY
            if key != "lines"
        },
        lines=SYNC_BODY["lines"],
    )
    server_id = first["id"]

    updated_lines = [
        {
            "client_line_uuid": CLIENT_LINE_ONE,
            "sort_order": 1,
            "description": "ממצא א - עודכן",
        },
    ]
    second = service.sync_visit_report(
        organization_id=ORG_ID,
        actor_profile_id="supervisor-1",
        client_report_uuid=CLIENT_REPORT_UUID,
        project_id="project-1",
        visit_type="STRUCTURE_SITE",
        visit_date="2026-06-04",
        header_fields={"contractor_notes": ["עודכן"]},
        lines=updated_lines,
        idempotency_key=CLIENT_REPORT_UUID,
    )

    assert second["created"] is False
    assert second["id"] == server_id
    assert second["report"]["visit_date"] == "2026-06-04"
    assert len(second["report"]["lines"]) == 1
    assert second["report"]["lines"][0]["description"] == "ממצא א - עודכן"
    assert lines.get_by_client_line_uuid(CLIENT_LINE_TWO) is None


def test_sync_visit_report_rejects_idempotency_key_mismatch():
    service = _service()

    with pytest.raises(ValidationError):
        service.sync_visit_report(
            organization_id=ORG_ID,
            actor_profile_id="supervisor-1",
            **{
                key: SYNC_BODY[key]
                for key in SYNC_BODY
                if key != "lines"
            },
            lines=SYNC_BODY["lines"],
            idempotency_key="different-key",
        )


def test_sync_visit_report_rejects_locked_report():
    reports = FakeVisitReportRepository()
    reports.create(
        organization_id=ORG_ID,
        project_id="project-1",
        created_by_profile_id="supervisor-1",
        visit_type="STRUCTURE_SITE",
        visit_date="2026-06-03",
        status="LOCKED",
        client_report_uuid=CLIENT_REPORT_UUID,
    )
    service = _service(reports=reports)

    with pytest.raises(ConflictError):
        service.sync_visit_report(
            organization_id=ORG_ID,
            actor_profile_id="supervisor-1",
            **{
                key: SYNC_BODY[key]
                for key in SYNC_BODY
                if key != "lines"
            },
            lines=SYNC_BODY["lines"],
        )


def test_put_sync_endpoint(monkeypatch):
    client = _setup_client(monkeypatch)
    token = _token()

    response = client.put(
        "/field-reports/visits/sync",
        headers={
            **_headers(token),
            "X-Idempotency-Key": CLIENT_REPORT_UUID,
        },
        json=SYNC_BODY,
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["created"] is True
    assert payload["client_report_uuid"] == CLIENT_REPORT_UUID
    assert len(payload["report"]["lines"]) == 2

    # עדכון שטח - ללא מפתח idempotency (גוף שונה); ה-upsert לפי client_report_uuid
    retry = client.put(
        "/field-reports/visits/sync",
        headers=_headers(token),
        json={
            **SYNC_BODY,
            "header_fields": {"contractor_notes": ["שני"]},
            "lines": [
                {
                    "client_line_uuid": CLIENT_LINE_ONE,
                    "description": "עודכן",
                },
            ],
        },
    )
    assert retry.status_code == 200
    assert retry.json()["created"] is False
    assert retry.json()["id"] == payload["id"]
    assert retry.json()["report"]["lines"][0]["description"] == "עודכן"

    replay = client.put(
        "/field-reports/visits/sync",
        headers={
            **_headers(token),
            "X-Idempotency-Key": CLIENT_REPORT_UUID,
        },
        json=SYNC_BODY,
    )
    assert replay.status_code == 200
    assert replay.headers.get("X-Idempotency-Replayed") == "true"


def test_sync_visit_report_duplicate_payload_one_db_row():
    """sync כפול עם אותו payload - שורת דוח אחת, אותו server id."""
    reports = FakeVisitReportRepository()
    lines = FakeVisitReportLineRepository()
    service = _service(reports=reports, lines=lines)

    first = service.sync_visit_report(
        organization_id=ORG_ID,
        actor_profile_id="supervisor-1",
        **_sync_body_kwargs(),
    )
    second = service.sync_visit_report(
        organization_id=ORG_ID,
        actor_profile_id="supervisor-1",
        **_sync_body_kwargs(),
    )

    assert first["created"] is True
    assert second["created"] is False
    assert second["id"] == first["id"]
    assert len(reports.records) == 1
    assert len(lines.records) == 2
    assert reports.get_by_client_report_uuid(CLIENT_REPORT_UUID)


def test_sync_visit_report_disconnect_retry_no_duplicate():
    """retry אחרי ניתוק - שני sync זהים עם מפתח idempotency, בלי דוח/שורות כפולים."""
    reports = FakeVisitReportRepository()
    lines = FakeVisitReportLineRepository()
    service = _service(reports=reports, lines=lines)

    first = service.sync_visit_report(
        organization_id=ORG_ID,
        actor_profile_id="supervisor-1",
        **_sync_body_kwargs(),
        idempotency_key=CLIENT_REPORT_UUID,
    )
    second = service.sync_visit_report(
        organization_id=ORG_ID,
        actor_profile_id="supervisor-1",
        **_sync_body_kwargs(),
        idempotency_key=CLIENT_REPORT_UUID,
    )

    assert first["id"] == second["id"]
    assert len(reports.records) == 1
    assert len(lines.records) == 2


def test_put_sync_rejects_idempotency_key_mismatch_http(monkeypatch):
    client = _setup_client(monkeypatch)
    token = _token()

    response = client.put(
        "/field-reports/visits/sync",
        headers={
            **_headers(token),
            "X-Idempotency-Key": WRONG_IDEMPOTENCY_KEY,
        },
        json=SYNC_BODY,
    )

    assert response.status_code == 400
    assert "Idempotency" in response.json()["error"]["message"]


def test_put_sync_idempotency_same_key_different_body_returns_409(
    monkeypatch,
):
    client, reports, _lines = _setup_sync_client(monkeypatch)
    token = _token()
    sync_body = {
        **SYNC_BODY,
        "client_report_uuid": SYNC_REPORT_CONFLICT,
        "lines": [
            {
                "client_line_uuid": SYNC_LINE_CONFLICT,
                "sort_order": 1,
                "description": "שורה לבדיקת 409",
            },
        ],
    }
    headers = {
        **_headers(token),
        "X-Idempotency-Key": SYNC_REPORT_CONFLICT,
    }

    first = client.put(
        "/field-reports/visits/sync",
        headers=headers,
        json=sync_body,
    )
    assert first.status_code == 200
    assert len(reports.records) == 1

    conflict = client.put(
        "/field-reports/visits/sync",
        headers=headers,
        json={
            **sync_body,
            "header_fields": {"contractor_notes": ["גוף שונה"]},
        },
    )

    assert conflict.status_code == 409
    assert (
        conflict.json()["error"]["code"] == "IDEMPOTENCY_KEY_REUSED"
    )
    assert len(reports.records) == 1


def test_put_sync_identical_retry_single_report_row(monkeypatch):
    """שני PUT זהים עם X-Idempotency-Key - replay, שורת דוח אחת ב-fake repo."""
    client, reports, lines = _setup_sync_client(monkeypatch)
    token = _token()
    sync_body = {
        **SYNC_BODY,
        "client_report_uuid": SYNC_REPORT_HTTP,
        "lines": [
            {
                "client_line_uuid": SYNC_LINE_HTTP_ONE,
                "sort_order": 1,
                "description": "שורה ל-retry",
            },
        ],
    }
    headers = {
        **_headers(token),
        "X-Idempotency-Key": SYNC_REPORT_HTTP,
    }

    first = client.put(
        "/field-reports/visits/sync",
        headers=headers,
        json=sync_body,
    )
    second = client.put(
        "/field-reports/visits/sync",
        headers=headers,
        json=sync_body,
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.headers.get("X-Idempotency-Replayed") == "true"
    assert second.json()["id"] == first.json()["id"]
    assert len(reports.records) == 1
    assert len(lines.records) == 1
