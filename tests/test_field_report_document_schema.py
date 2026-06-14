from __future__ import annotations

import warnings
from datetime import date

from pydantic import TypeAdapter

from app.schemas.field_report_document import (
    FindingsTableBlock,
    ProgressTableBlock,
    ProjectMetadata,
    Stakeholder,
    VisitReportDocument,
    warn_unknown_header_field_keys,
)
from app.schemas.field_reports import (
    FieldVisitReportCreateRequest,
    FieldVisitReportUpdateRequest,
)

report_block_adapter = TypeAdapter(
    ProgressTableBlock | FindingsTableBlock
)


def test_project_metadata_field_names_match_typescript() -> None:
    metadata = ProjectMetadata(
        scheme="TAMA38_STRENGTHENING",
        scheme_label_he='התחדשות עירונית - פרויקט חיזוק תמ"א',
        project_start_date="2026-01-01",
        housing_units_count=42,
        site_address="רחוב 1",
    )

    assert metadata.scheme == "TAMA38_STRENGTHENING"
    assert metadata.housing_units_count == 42


def test_stakeholder_roles_match_typescript() -> None:
    stakeholder = Stakeholder(
        id="legacy-developer",
        role="developer",
        name="יזם בע\"מ",
    )

    assert stakeholder.role == "developer"


def test_report_block_discriminated_union() -> None:
    progress = report_block_adapter.validate_python(
        {
            "kind": "progress_table",
            "id": "block-1",
            "title_he": "סטטוס בניה-שלד",
            "column_preset": "progress",
            "rows": [
                {
                    "id": "row-1",
                    "description": "ביסוס",
                    "status": "בוצע",
                    "completion_date": "18.11.25",
                }
            ],
        }
    )
    assert isinstance(progress, ProgressTableBlock)
    assert progress.rows[0].description == "ביסוס"

    findings = report_block_adapter.validate_python(
        {
            "kind": "findings_table",
            "id": "block-2",
            "title_he": "ממצאים",
            "column_preset": "rich",
            "rows": [{"id": "line-1", "description": "סדק"}],
        }
    )
    assert isinstance(findings, FindingsTableBlock)


def test_visit_report_document_accepts_legacy_and_new_fields() -> None:
    document = VisitReportDocument(
        id="report-1",
        project_id="project-1",
        visit_type="STRUCTURE_SITE",
        visit_date="2026-06-01",
        project_metadata=ProjectMetadata(site_address="רחוב 1"),
        stakeholders=[
            Stakeholder(id="dev-1", role="developer", name="יזם"),
        ],
        blocks=[
            {
                "kind": "progress_table",
                "id": "legacy-progress-table",
                "title_he": "התקדמות",
                "column_preset": "progress",
                "rows": [],
            }
        ],
        header_fields_raw={
            "developer_name": "יזם",
            "site_address": "רחוב 1",
        },
        lines=[{"id": "line-1", "description": "ממצא"}],
    )

    assert document.stakeholders[0].name == "יזם"
    assert document.header_fields_raw["developer_name"] == "יזם"


def test_create_request_accepts_legacy_header_fields() -> None:
    request = FieldVisitReportCreateRequest(
        project_id="project-1",
        visit_type="STRUCTURE_SITE",
        visit_date=date(2026, 6, 1),
        header_fields={
            "developer_name": "יזם",
            "site_address": "רחוב 1",
            "construction_progress": [
                {
                    "description": "ביסוס",
                    "status": "בוצע",
                    "completion_date": "",
                }
            ],
        },
    )

    assert request.header_fields["developer_name"] == "יזם"


def test_update_request_accepts_partial_header_fields() -> None:
    request = FieldVisitReportUpdateRequest(
        header_fields={"lawyer_name": "עו\"ד לוי"},
    )

    assert request.header_fields is not None
    assert request.header_fields["lawyer_name"] == "עו\"ד לוי"


def test_warn_unknown_header_field_keys_emits_warning_only() -> None:
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        unknown = warn_unknown_header_field_keys(
            {"developer_name": "יזם", "custom_future_key": "value"},
            report_id="report-1",
        )

    assert unknown == ["custom_future_key"]
    assert len(caught) == 1
    assert "custom_future_key" in str(caught[0].message)


def test_create_request_warns_on_unknown_header_keys() -> None:
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        FieldVisitReportCreateRequest(
            project_id="project-1",
            visit_type="STRUCTURE_SITE",
            visit_date=date(2026, 6, 1),
            header_fields={"totally_unknown_key": True},
        )

    assert any("totally_unknown_key" in str(item.message) for item in caught)


def test_known_header_keys_include_supervision_meta() -> None:
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        unknown = warn_unknown_header_field_keys(
            {
                "supervision_meta": {
                    "construction_stage": "FINISHING",
                    "visit_scope": "APARTMENT",
                    "apartment_number": "12",
                },
                "blocks": [],
            },
        )

    assert unknown == []
    assert len(caught) == 0


def test_known_header_keys_include_fixed_text_and_inspector_notes() -> None:
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        unknown = warn_unknown_header_field_keys(
            {
                "include_fixed_text_blocks": True,
                "inspector_notes": "הערה",
                "fixed_text_blocks": [],
            },
        )

    assert unknown == []
    assert len(caught) == 0


def test_create_request_does_not_reject_unknown_header_keys() -> None:
    request = FieldVisitReportCreateRequest(
        project_id="project-1",
        visit_type="STRUCTURE_SITE",
        visit_date=date(2026, 6, 1),
        header_fields={"future_feature_flag": {"enabled": True}},
    )

    assert request.header_fields["future_feature_flag"] == {"enabled": True}
