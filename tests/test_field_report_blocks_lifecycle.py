"""E2E lifecycle: blocks, grouping, photos, close (FR-5.2)."""

from __future__ import annotations

from pathlib import Path

from pydantic import TypeAdapter

from app.config.field_report_block_defaults import (
    default_report_blocks_for_visit_type,
)
from app.schemas.field_report_document import (
    FindingsTableBlock,
    ProgressTableBlock,
    ReportBlock,
    VisitReportDocument,
)
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

from tests.test_field_visit_reports import (
    FakeModuleRepository,
    FakeOrganizationRepository,
    FakeProjectRepository,
    FakeVisitReportLinePhotoRepository,
    FakeVisitReportLineRepository,
    FakeVisitReportRepository,
    _headers,
    _setup_client,
    _token,
)

report_blocks_adapter = TypeAdapter(list[ReportBlock])


def _client_with_photos(monkeypatch, tmp_path: Path):
    visit_service = FieldVisitReportService(
        report_repository=FakeVisitReportRepository(),
        line_repository=FakeVisitReportLineRepository(),
        line_photo_repository=FakeVisitReportLinePhotoRepository(),
        project_repository=FakeProjectRepository(),
        organization_profile_service=FieldReportOrganizationProfileService(
            organization_repository=FakeOrganizationRepository(),
            module_service=FieldReportModuleService(
                module_repository=FakeModuleRepository(),
                organization_repository=FakeOrganizationRepository(),
            ),
        ),
        photo_service=FieldVisitReportPhotoService(photos_root=tmp_path),
    )
    monkeypatch.setattr(
        "app.dependencies.field_visit_report_service",
        visit_service,
    )
    return _setup_client(monkeypatch)


def _blocks_payload(visit_type: str) -> list[dict]:
    blocks = default_report_blocks_for_visit_type(visit_type)
    progress = next(
        (block for block in blocks if block["kind"] == "progress_table"),
        None,
    )
    if progress is not None:
        progress["rows"] = [
            {
                "id": "progress-row-1",
                "description": "ביסוס",
                "status": "בוצע",
                "completion_date": "01.06.26",
                "sort_order": 0,
            }
        ]
        return blocks

    lobby_findings = next(
        block for block in blocks if block["kind"] == "findings_table"
    )
    lobby_findings["rows"] = [
        {
            "id": "lobby-row-1",
            "location": "לובי",
            "trade": "חיפוי קירות",
            "status": "בוצע",
            "description": "ביצוע חיפוי בלובי הקומתי",
            "sort_order": 0,
        }
    ]
    return blocks


def _document_from_closed_report(report: dict) -> VisitReportDocument:
    header = report.get("header_fields") or {}
    return VisitReportDocument(
        id=report["id"],
        project_id=report["project_id"],
        visit_type=report["visit_type"],
        visit_date=report["visit_date"],
        visit_type_label_he=report.get("visit_type_label_he"),
        project_name=report.get("project_name"),
        project_metadata=header.get("project_metadata"),
        stakeholders=header.get("stakeholders") or [],
        main_suppliers=header.get("main_suppliers") or [],
        fixed_text_blocks=header.get("fixed_text_blocks") or [],
        blocks=report_blocks_adapter.validate_python(
            header.get("blocks") or []
        ),
        header_fields_raw=header,
        lines=[
            {
                "id": line["id"],
                "sort_order": line.get("sort_order", 0),
                "description": line.get("description"),
                "location": line.get("location"),
                "trade": line.get("trade"),
                "status_notes": line.get("status_notes"),
                "group_key": line.get("group_key"),
                "group_label_he": line.get("group_label_he"),
                "has_photo": line.get("has_photo"),
                "photo_ids": line.get("photo_ids"),
            }
            for line in report.get("lines") or []
        ],
        catalog_version=report.get("catalog_version"),
        status=report.get("status"),
        organization_profile_snapshot=report.get(
            "organization_profile_snapshot"
        ),
    )


def test_new_format_blocks_grouping_photo_close_lifecycle(
    monkeypatch, tmp_path
):
    client = _client_with_photos(monkeypatch, tmp_path)
    token = _token()

    created = client.post(
        "/field-reports/visits",
        headers=_headers(token),
        json={
            "project_id": "project-1",
            "visit_type": "FINISHING_APARTMENTS",
            "visit_date": "2026-01-15",
        },
    ).json()
    report_id = created["id"]

    blocks = _blocks_payload("FINISHING_APARTMENTS")
    patch_response = client.patch(
        f"/field-reports/visits/{report_id}",
        headers=_headers(token),
        json={"header_fields": {"blocks": blocks}},
    )
    assert patch_response.status_code == 200
    patched_blocks = patch_response.json()["header_fields"]["blocks"]
    assert len(patched_blocks) >= 2
    block_kinds = {block["kind"] for block in patched_blocks}
    assert block_kinds >= {"findings_table", "checklist"}

    line = client.post(
        f"/field-reports/visits/{report_id}/lines",
        headers=_headers(token),
        json={
            "description": "איטום מרפסת",
            "group_key": "apartment:3",
            "group_label_he": "דירה 3",
        },
    ).json()
    line_id = line["id"]

    upload = client.post(
        f"/field-reports/visits/{report_id}/lines/{line_id}/photo",
        headers=_headers(token),
        files={"file": ("visit.jpg", b"jpeg-bytes", "image/jpeg")},
    )
    assert upload.status_code == 200
    assert upload.json()["has_photo"] is True
    assert upload.json()["photo_ids"]

    preview = client.get(
        f"/field-reports/visits/{report_id}/close-preview",
        headers=_headers(token),
    )
    assert preview.status_code == 200
    assert preview.json()["empty_line_count"] == 0

    closed = client.post(
        f"/field-reports/visits/{report_id}/close",
        headers=_headers(token),
    ).json()
    assert closed["status"] == "CLOSED"
    assert closed["is_editable"] is False

    detail = client.get(
        f"/field-reports/visits/{report_id}",
        headers=_headers(token),
    ).json()
    document = _document_from_closed_report(detail)

    assert len(document.blocks) >= 2
    findings_blocks = [
        block
        for block in document.blocks
        if isinstance(block, FindingsTableBlock)
    ]
    assert findings_blocks
    assert findings_blocks[0].column_preset == "finishing"
    assert findings_blocks[0].rows[0].location == "לובי"

    assert len(document.lines) == 1
    assert document.lines[0].group_key == "apartment:3"
    assert document.lines[0].group_label_he == "דירה 3"
    assert document.lines[0].has_photo is True
    assert document.lines[0].photo_ids

    assert document.header_fields_raw.get("blocks")
    assert document.header_fields_raw.get("construction_progress") == []


def test_structure_site_create_seeds_default_blocks(monkeypatch):
    client = _setup_client(monkeypatch)
    token = _token()

    created = client.post(
        "/field-reports/visits",
        headers=_headers(token),
        json={
            "project_id": "project-1",
            "visit_type": "STRUCTURE_SITE",
            "visit_date": "2026-06-01",
        },
    ).json()
    report_id = created["id"]
    header = created["header_fields"]
    assert header.get("blocks")
    assert len(header["blocks"]) >= 2
    assert header["construction_progress"]

    client.post(
        f"/field-reports/visits/{report_id}/lines",
        headers=_headers(token),
        json={
            "description": "ממצא שלד",
            "location": "קומה 2",
        },
    )

    closed = client.post(
        f"/field-reports/visits/{report_id}/close",
        headers=_headers(token),
    ).json()
    assert closed["status"] == "CLOSED"

    detail = client.get(
        f"/field-reports/visits/{report_id}",
        headers=_headers(token),
    ).json()
    assert detail["header_fields"].get("blocks")
    assert detail["header_fields"]["construction_progress"]
    assert detail["lines"][0]["group_key"] is None
    assert detail["lines"][0]["description"] == "ממצא שלד"
