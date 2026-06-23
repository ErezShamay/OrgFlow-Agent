"""Gate D9 — public_areas aggregation in supervision dashboard."""

from __future__ import annotations

from app.lib.supervision_dashboard_aggregation import aggregate_supervision_dashboard
from tests.test_project_supervision_dashboard_d1_gate import _checklist_item


def _public_area_report(
    *,
    report_id: str,
    area_id: str,
    label_he: str,
    items: list[dict],
    updated_at: str,
) -> dict:
    return {
        "id": report_id,
        "project_id": "proj-d9",
        "organization_id": "org-d9",
        "status": "CLOSED",
        "updated_at": updated_at,
        "header_fields": {
            "supervision_meta": {
                "construction_stage": "FINISHING",
                "visit_scope": "PUBLIC_AREA",
                "public_area_id": area_id,
                "public_area_label_he": label_he,
            },
            "blocks": [
                {
                    "id": "checklist-lobby",
                    "kind": "supervision_checklist",
                    "title_he": label_he,
                    "items": items,
                }
            ],
        },
    }


def test_public_areas_appear_in_dashboard_response() -> None:
    dashboard = aggregate_supervision_dashboard(
        project_id="proj-d9",
        project_name="פיתוח משותף",
        apartments=[],
        reports=[
            _public_area_report(
                report_id="visit-lobby",
                area_id="LOBBY",
                label_he="לובי",
                updated_at="2026-06-12T10:00:00Z",
                items=[
                    _checklist_item(
                        item_id="lobby-ok",
                        status="OK",
                        category_name_he="חללים",
                        category_id="SPACES",
                    )
                ],
            )
        ],
        issues=[],
    )

    assert len(dashboard.public_areas) == 1
    assert dashboard.public_areas[0].area_key == "LOBBY"
    assert dashboard.public_areas[0].label_he == "לובי"
    assert dashboard.public_areas[0].total_items == 1
    assert dashboard.public_areas[0].progress_percent == 100
