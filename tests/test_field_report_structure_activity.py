from __future__ import annotations

from app.lib.field_report_structure_activity import (
    REPORT_STRUCTURE_ACTIVITY_TYPE,
    diff_report_structure_change_kinds,
    record_report_structure_activity_best_effort,
    structure_activity_title_he,
)
from app.services.field_visit_report_service import FieldVisitReportService


def _checklist_block(*, item_ids: list[str]) -> dict:
    return {
        "id": "checklist-main",
        "kind": "checklist",
        "title_he": "צ'קליסט",
        "sort_order": 0,
        "items": [
            {"id": item_id, "label_he": item_id, "sort_order": index}
            for index, item_id in enumerate(item_ids)
        ],
    }


def test_diff_detects_checklist_item_added() -> None:
    before = {"blocks": [_checklist_block(item_ids=["a", "b"])]}
    after = {"blocks": [_checklist_block(item_ids=["a", "b", "c"])]}

    changes = diff_report_structure_change_kinds(before, after)

    assert changes == ["checklist_item_added:c"]


def test_diff_ignores_content_only_header_changes() -> None:
    before = {
        "blocks": [_checklist_block(item_ids=["a"])],
        "inspector_notes": "ישן",
    }
    after = {
        "blocks": [
            {
                **_checklist_block(item_ids=["a"]),
                "items": [
                    {
                        "id": "a",
                        "label_he": "שם חדש",
                        "sort_order": 0,
                        "checked": True,
                        "notes": "הערה",
                    }
                ],
            }
        ],
        "inspector_notes": "חדש",
    }

    assert diff_report_structure_change_kinds(before, after) == []


def test_diff_detects_custom_text_section_added() -> None:
    before = {
        "fixed_text_blocks": [
            {
                "id": "disclaimer",
                "kind": "non_conformance_disclaimer",
                "enabled": True,
                "sort_order": 0,
            }
        ]
    }
    after = {
        "fixed_text_blocks": [
            {
                "id": "disclaimer",
                "kind": "non_conformance_disclaimer",
                "enabled": True,
                "sort_order": 0,
            },
            {
                "id": "custom-1",
                "kind": "custom",
                "enabled": True,
                "sort_order": 1,
                "title_he": "הערת אחריות",
                "body_he": "טקסט",
            },
        ]
    }

    changes = diff_report_structure_change_kinds(before, after)

    assert changes == ["custom_text_section_added:custom-1"]


def test_record_structure_activity_best_effort_swallows_recorder_errors() -> None:
    def failing_recorder(**_kwargs):
        raise RuntimeError("activity down")

    record_report_structure_activity_best_effort(
        activity_recorder=failing_recorder,
        project_id="project-1",
        report_id="report-1",
        before_header_fields={"blocks": [_checklist_block(item_ids=["a"])]},
        after_header_fields={"blocks": [_checklist_block(item_ids=["a", "b"])]},
        actor_id="user-1",
    )


def test_update_report_records_structure_activity() -> None:
    activities: list[dict] = []

    class FakeProjectRepository:
        def get_project_by_id(self, project_id: str) -> dict:
            return {"id": project_id, "project_name": "פרויקט בדיקה"}

    class FakeLineRepository:
        def is_storage_available(self) -> bool:
            return True

        def list_by_report(self, report_id: str) -> list[dict]:
            return []

    class FakeReportRepository:
        def __init__(self) -> None:
            self.record = {
                "id": "report-1",
                "organization_id": "org-1",
                "project_id": "project-1",
                "created_by_profile_id": "supervisor-1",
                "visit_type": "STRUCTURE_SITE",
                "visit_date": "2026-06-01",
                "status": "IN_PROGRESS",
                "header_fields": {
                    "blocks": [_checklist_block(item_ids=["a"])],
                },
            }

        def is_storage_available(self) -> bool:
            return True

        def get_by_id(self, report_id: str) -> dict | None:
            if report_id == "report-1":
                return dict(self.record)
            return None

        def update(self, report_id: str, payload: dict) -> dict | None:
            if report_id != "report-1":
                return None
            self.record = {**self.record, **payload}
            return dict(self.record)

    def record_activity(**kwargs):
        activities.append(kwargs)
        return [{"id": "activity-1"}]

    service = FieldVisitReportService(
        report_repository=FakeReportRepository(),
        line_repository=FakeLineRepository(),
        project_repository=FakeProjectRepository(),
        activity_recorder=record_activity,
    )

    updated = service.update_report(
        organization_id="org-1",
        report_id="report-1",
        header_fields={
            "blocks": [_checklist_block(item_ids=["a", "new-item"])],
        },
        actor_user_id="supervisor-1",
    )

    assert updated["id"] == "report-1"
    assert len(activities) == 1
    activity = activities[0]
    assert activity["project_id"] == "project-1"
    assert activity["activity_type"] == REPORT_STRUCTURE_ACTIVITY_TYPE
    assert activity["metadata"]["report_id"] == "report-1"
    assert "checklist_item_added:new-item" in activity["metadata"]["change_kinds"]
    assert activity["metadata"]["actor_id"] == "supervisor-1"
    assert activity["title"] == structure_activity_title_he(
        activity["metadata"]["change_kinds"]
    )


def test_update_report_skips_activity_when_structure_unchanged() -> None:
    activities: list[dict] = []

    class FakeProjectRepository:
        def get_project_by_id(self, project_id: str) -> dict:
            return {"id": project_id, "project_name": "פרויקט בדיקה"}

    class FakeLineRepository:
        def is_storage_available(self) -> bool:
            return True

        def list_by_report(self, report_id: str) -> list[dict]:
            return []

    class FakeReportRepository:
        def __init__(self) -> None:
            self.record = {
                "id": "report-1",
                "organization_id": "org-1",
                "project_id": "project-1",
                "created_by_profile_id": "supervisor-1",
                "visit_type": "STRUCTURE_SITE",
                "visit_date": "2026-06-01",
                "status": "IN_PROGRESS",
                "header_fields": {
                    "blocks": [_checklist_block(item_ids=["a"])],
                    "inspector_notes": "ישן",
                },
            }

        def is_storage_available(self) -> bool:
            return True

        def get_by_id(self, report_id: str) -> dict | None:
            return dict(self.record)

        def update(self, report_id: str, payload: dict) -> dict | None:
            self.record = {**self.record, **payload}
            return dict(self.record)

    service = FieldVisitReportService(
        report_repository=FakeReportRepository(),
        line_repository=FakeLineRepository(),
        project_repository=FakeProjectRepository(),
        activity_recorder=lambda **kwargs: activities.append(kwargs),
    )

    service.update_report(
        organization_id="org-1",
        report_id="report-1",
        header_fields={"inspector_notes": "חדש"},
        actor_user_id="supervisor-1",
    )

    assert activities == []
