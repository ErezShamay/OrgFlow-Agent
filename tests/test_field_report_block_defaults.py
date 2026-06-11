from __future__ import annotations

from app.config.field_report_block_defaults import (
    COLUMN_PRESETS,
    DEFAULT_BLOCKS_BY_VISIT_TYPE,
    DEFAULT_NON_CONFORMANCE_DISCLAIMER_HE,
    DEFAULT_SAFETY_DISCLAIMER_HE,
    FINISHING_CHECKLIST_ITEM_DEFS,
    VISIT_TYPE_MIXED,
    column_preset_headers,
    default_finishing_checklist_items,
    default_fixed_text_blocks,
    default_fixed_text_blocks_for_new_report,
    default_report_blocks_for_visit_type,
    get_column_preset,
    is_winter_season_date,
)


def test_column_presets_match_typescript_headers() -> None:
    assert column_preset_headers("rich") == [
        "מיקום",
        "מלאכה",
        "סטטוס / הערות",
        "תיאור",
        "תמונות",
    ]
    assert column_preset_headers("simple") == [
        "תיאור",
        "הערות / לטיפול",
        "תמונות",
    ]
    assert column_preset_headers("finishing") == [
        "מיקום",
        "מלאכה",
        "הערות",
        "סטטוס / תיאור",
        "תמונות",
    ]
    assert column_preset_headers("progress") == [
        "תיאור עבודה",
        "סטטוס",
        "תאריך ביצוע / סיום",
    ]
    assert column_preset_headers("structure") == [
        "תיאור",
        "סטטוס / תאריך סיום",
    ]


def test_column_presets_define_all_keys() -> None:
    assert set(COLUMN_PRESETS.keys()) == {
        "rich",
        "simple",
        "finishing",
        "progress",
        "structure",
    }


def test_default_blocks_by_visit_type_keys() -> None:
    assert set(DEFAULT_BLOCKS_BY_VISIT_TYPE.keys()) == {
        "STRUCTURE_SITE",
        "FINISHING_APARTMENTS",
        VISIT_TYPE_MIXED,
    }


def test_default_report_blocks_for_structure_site() -> None:
    blocks = default_report_blocks_for_visit_type("STRUCTURE_SITE")

    assert len(blocks) == 2
    assert blocks[0]["kind"] == "progress_table"
    assert blocks[0]["column_preset"] == "structure"
    assert len(blocks[0]["rows"]) > 0
    assert blocks[1]["kind"] == "findings_table"
    assert blocks[1]["column_preset"] == "simple"
    assert blocks[1]["rows"] == []


def test_default_finishing_checklist_items() -> None:
    items = default_finishing_checklist_items()

    assert len(items) == len(FINISHING_CHECKLIST_ITEM_DEFS)
    assert items[0]["label_he"] == "בעלים"
    assert items[0]["checked"] is False


def test_default_report_blocks_for_finishing_includes_checklist() -> None:
    blocks = default_report_blocks_for_visit_type("FINISHING_APARTMENTS")

    assert [block["kind"] for block in blocks] == [
        "checklist",
        "findings_table",
        "findings_table",
    ]
    checklist = next(block for block in blocks if block["kind"] == "checklist")
    assert checklist["title_he"] == "התקדמות הבנייה"
    assert len(checklist["items"]) == 6
    findings = [block for block in blocks if block["kind"] == "findings_table"]
    assert findings[0]["column_preset"] == "finishing"
    assert findings[1]["column_preset"] == "finishing"


def test_default_report_blocks_for_mixed() -> None:
    blocks = default_report_blocks_for_visit_type(VISIT_TYPE_MIXED)

    assert [block["kind"] for block in blocks] == [
        "progress_table",
        "findings_table",
    ]


def test_default_fixed_text_blocks_include_disclaimers() -> None:
    blocks = default_fixed_text_blocks()

    assert blocks[0]["body_he"] == DEFAULT_NON_CONFORMANCE_DISCLAIMER_HE
    assert blocks[1]["body_he"] == DEFAULT_SAFETY_DISCLAIMER_HE


def test_is_winter_season_date() -> None:
    assert is_winter_season_date("2026-11-01") is True
    assert is_winter_season_date("2026-06-01") is False


def test_default_fixed_text_blocks_enables_winter_by_visit_date() -> None:
    summer = default_fixed_text_blocks_for_new_report("2026-07-01")
    winter = default_fixed_text_blocks_for_new_report("2026-12-01")

    summer_block = next(
        block for block in summer if block["kind"] == "winter_recommendations"
    )
    winter_block = next(
        block for block in winter if block["kind"] == "winter_recommendations"
    )
    assert summer_block["enabled"] is False
    assert winter_block["enabled"] is True


def test_get_column_preset_returns_copy() -> None:
    preset = get_column_preset("rich")
    preset[0]["header_he"] = "changed"

    assert COLUMN_PRESETS["rich"][0]["header_he"] == "מיקום"
