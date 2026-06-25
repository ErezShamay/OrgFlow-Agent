"""
זיהוי שינויי מבנה בדוח ביקור (blocks, צ'קליסט, טקסט קבוע מותאם) ל-workspace activity.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

REPORT_STRUCTURE_ACTIVITY_TYPE = "REPORT_STRUCTURE_UPDATED"


def _sorted_block_list(blocks: Any) -> list[dict]:
    if not isinstance(blocks, list):
        return []

    normalized = [block for block in blocks if isinstance(block, dict)]
    return sorted(
        normalized,
        key=lambda block: (
            block.get("sort_order", 0),
            str(block.get("id") or ""),
        ),
    )


def _checklist_item_ids(block: dict) -> list[str]:
    items = block.get("items")
    if not isinstance(items, list):
        return []
    return sorted(
        str(item.get("id"))
        for item in items
        if isinstance(item, dict) and item.get("id")
    )


def _supervision_item_states(block: dict) -> dict[str, dict[str, bool]]:
    items = block.get("items")
    if not isinstance(items, list):
        return {}

    states: dict[str, dict[str, bool]] = {}
    for item in items:
        if not isinstance(item, dict):
            continue
        item_id = item.get("id")
        if not item_id:
            continue
        states[str(item_id)] = {
            "hidden": bool(item.get("hidden")),
            "is_custom": bool(item.get("is_custom")),
        }
    return states


def _table_row_ids(block: dict) -> list[str]:
    rows = block.get("rows")
    if not isinstance(rows, list):
        return []
    return sorted(
        str(row.get("id"))
        for row in rows
        if isinstance(row, dict) and row.get("id")
    )


def _fixed_text_sections(header_fields: dict) -> list[dict[str, Any]]:
    sections = header_fields.get("fixed_text_blocks")
    if not isinstance(sections, list):
        return []

    normalized: list[dict[str, Any]] = []
    for section in sections:
        if not isinstance(section, dict):
            continue
        normalized.append(
            {
                "id": str(section.get("id") or ""),
                "kind": str(section.get("kind") or ""),
                "enabled": bool(section.get("enabled")),
                "sort_order": section.get("sort_order", 0),
            }
        )

    return sorted(
        normalized,
        key=lambda section: (
            section.get("sort_order", 0),
            section.get("id", ""),
        ),
    )


def build_report_structure_fingerprint(header_fields: dict | None) -> dict[str, Any]:
    """חתימת מבנה בלבד — ללא תוכן שורות / הערות / סימונים."""
    source = header_fields if isinstance(header_fields, dict) else {}
    blocks_fp: list[dict[str, Any]] = []

    for block in _sorted_block_list(source.get("blocks")):
        kind = str(block.get("kind") or "")
        entry: dict[str, Any] = {
            "id": str(block.get("id") or ""),
            "kind": kind,
            "sort_order": block.get("sort_order", 0),
        }

        if kind == "checklist":
            entry["item_ids"] = _checklist_item_ids(block)
        elif kind == "supervision_checklist":
            entry["supervision_items"] = _supervision_item_states(block)
        elif kind in {"findings_table", "progress_table"}:
            entry["row_ids"] = _table_row_ids(block)
            if kind == "findings_table":
                entry["column_preset"] = str(
                    block.get("column_preset") or ""
                )

        blocks_fp.append(entry)

    return {
        "blocks": blocks_fp,
        "fixed_text_blocks": _fixed_text_sections(source),
    }


def diff_report_structure_change_kinds(
    before_header_fields: dict | None,
    after_header_fields: dict | None,
) -> list[str]:
    before = build_report_structure_fingerprint(before_header_fields)
    after = build_report_structure_fingerprint(after_header_fields)

    if before == after:
        return []

    changes: list[str] = []

    before_blocks = {
        block["id"]: block for block in before["blocks"] if block.get("id")
    }
    after_blocks = {
        block["id"]: block for block in after["blocks"] if block.get("id")
    }

    for block_id in sorted(set(before_blocks) - set(after_blocks)):
        kind = before_blocks[block_id].get("kind")
        changes.append(f"block_removed:{kind}:{block_id}")

    for block_id in sorted(set(after_blocks) - set(before_blocks)):
        kind = after_blocks[block_id].get("kind")
        changes.append(f"block_added:{kind}:{block_id}")

    for block_id in sorted(set(before_blocks) & set(after_blocks)):
        before_block = before_blocks[block_id]
        after_block = after_blocks[block_id]
        kind = str(before_block.get("kind") or "")

        if before_block.get("sort_order") != after_block.get("sort_order"):
            changes.append(f"block_reordered:{kind}:{block_id}")

        if kind == "checklist":
            before_ids = set(before_block.get("item_ids") or [])
            after_ids = set(after_block.get("item_ids") or [])
            for item_id in sorted(after_ids - before_ids):
                changes.append(f"checklist_item_added:{item_id}")
            for item_id in sorted(before_ids - after_ids):
                changes.append(f"checklist_item_removed:{item_id}")

        elif kind == "supervision_checklist":
            before_items = before_block.get("supervision_items") or {}
            after_items = after_block.get("supervision_items") or {}

            for item_id in sorted(set(after_items) - set(before_items)):
                if after_items[item_id].get("is_custom"):
                    changes.append(
                        f"supervision_custom_item_added:{item_id}"
                    )

            for item_id in sorted(set(before_items) - set(after_items)):
                if before_items[item_id].get("is_custom"):
                    changes.append(
                        f"supervision_custom_item_removed:{item_id}"
                    )

            for item_id in sorted(set(before_items) & set(after_items)):
                before_state = before_items[item_id]
                after_state = after_items[item_id]

                if (
                    not before_state.get("is_custom")
                    and not after_state.get("is_custom")
                ):
                    if (
                        not before_state.get("hidden")
                        and after_state.get("hidden")
                    ):
                        changes.append(
                            f"supervision_item_hidden:{item_id}"
                        )
                    elif (
                        before_state.get("hidden")
                        and not after_state.get("hidden")
                    ):
                        changes.append(
                            f"supervision_item_restored:{item_id}"
                        )

        elif kind in {"findings_table", "progress_table"}:
            before_rows = set(before_block.get("row_ids") or [])
            after_rows = set(after_block.get("row_ids") or [])
            row_kind = "findings_row" if kind == "findings_table" else "progress_row"
            for row_id in sorted(after_rows - before_rows):
                changes.append(f"{row_kind}_added:{row_id}")
            for row_id in sorted(before_rows - after_rows):
                changes.append(f"{row_kind}_removed:{row_id}")

            if kind == "findings_table" and (
                before_block.get("column_preset")
                != after_block.get("column_preset")
            ):
                changes.append(f"findings_column_preset_changed:{block_id}")

    before_fixed = {
        section["id"]: section
        for section in before["fixed_text_blocks"]
        if section.get("id")
    }
    after_fixed = {
        section["id"]: section
        for section in after["fixed_text_blocks"]
        if section.get("id")
    }

    for section_id in sorted(set(after_fixed) - set(before_fixed)):
        if after_fixed[section_id].get("kind") == "custom":
            changes.append(f"custom_text_section_added:{section_id}")

    for section_id in sorted(set(before_fixed) - set(after_fixed)):
        if before_fixed[section_id].get("kind") == "custom":
            changes.append(f"custom_text_section_removed:{section_id}")

    return changes


def structure_activity_title_he(change_kinds: list[str]) -> str:
    if any(kind.startswith("checklist_item_") for kind in change_kinds):
        return "עודכן מבנה צ'קליסט בדוח"
    if any("supervision_" in kind for kind in change_kinds):
        return "עודכן מבנה צ'קליסט מפקח בדוח"
    if any(kind.startswith("custom_text_section_") for kind in change_kinds):
        return "עודכן מבנה טקסטים קבועים בדוח"
    if any(kind.startswith("block_") for kind in change_kinds):
        return "עודכנו סעיפי גוף הדוח"
    return "עודכן מבנה הדוח"


ActivityRecorder = Callable[..., Any]


def record_report_structure_activity_best_effort(
    *,
    activity_recorder: ActivityRecorder | None,
    project_id: str | None,
    report_id: str,
    before_header_fields: dict | None,
    after_header_fields: dict | None,
    actor_id: str | None = None,
) -> None:
    if not activity_recorder or not project_id:
        return

    change_kinds = diff_report_structure_change_kinds(
        before_header_fields,
        after_header_fields,
    )
    if not change_kinds:
        return

    metadata: dict[str, Any] = {
        "report_id": report_id,
        "change_kinds": change_kinds,
    }
    if actor_id:
        metadata["actor_id"] = actor_id

    try:
        activity_recorder(
            project_id=project_id,
            activity_type=REPORT_STRUCTURE_ACTIVITY_TYPE,
            title=structure_activity_title_he(change_kinds),
            description="Field visit report structure updated",
            metadata=metadata,
        )
    except Exception:
        # Activity logging must not block report saves.
        return
