"""Default report blocks, column presets, and fixed text boilerplate (FR-0.4).

Mirrors orgflow-ui/lib/field-reports/schema/column-presets.ts and block-defaults.ts.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import date, datetime
from typing import Any, Final, Literal, TypedDict

from app.config.field_report_construction_progress import (
    FINISHING_APARTMENT_FINDINGS_TITLE_HE,
    FINISHING_APARTMENTS_PROGRESS_TITLE_HE,
    FINISHING_LOBBY_FINDINGS_TITLE_HE,
    STRUCTURE_SITE_PROGRESS_TITLE_HE,
    default_construction_progress_rows,
)
from app.config.field_report_pdf_defaults import DEFAULT_WINTER_RECOMMENDATIONS_HE

ColumnPresetKey = Literal["rich", "simple", "finishing", "progress", "structure"]

VISIT_TYPE_MIXED: Final = "MIXED"

DEFAULT_NON_CONFORMANCE_DISCLAIMER_HE: Final = (
    'מלאכות שנמצאה לגביהן אי התאמה/הסתייגות מדווחות בגוף הדו"ח'
)

DEFAULT_SAFETY_DISCLAIMER_HE: Final = (
    "זו. היזם/הקבלן/ממונה הבטיחות אחראים למילוי כל הוראות הדין "
    "ביחס לבטיחות והוראות פיקוד העורף"
)

COLUMN_PRESETS: dict[ColumnPresetKey, list[dict[str, str]]] = {
    "rich": [
        {"id": "location", "header_he": "מיקום"},
        {"id": "trade", "header_he": "מלאכה"},
        {"id": "status", "header_he": "סטטוס / הערות"},
        {"id": "description", "header_he": "תיאור"},
        {"id": "photos", "header_he": "תמונות"},
    ],
    "simple": [
        {"id": "description", "header_he": "תיאור"},
        {"id": "notes", "header_he": "הערות / לטיפול"},
        {"id": "photos", "header_he": "תמונות"},
    ],
    "finishing": [
        {"id": "location", "header_he": "מיקום"},
        {"id": "trade", "header_he": "מלאכה"},
        {"id": "notes", "header_he": "הערות"},
        {"id": "status", "header_he": "סטטוס / תיאור"},
        {"id": "photos", "header_he": "תמונות"},
    ],
    "progress": [
        {"id": "description", "header_he": "תיאור עבודה"},
        {"id": "status", "header_he": "סטטוס"},
        {"id": "completion_date", "header_he": "תאריך ביצוע / סיום"},
    ],
    "structure": [
        {"id": "description", "header_he": "תיאור"},
        {"id": "status", "header_he": "סטטוס / תאריך סיום"},
    ],
}


class BlockTemplate(TypedDict, total=False):
    kind: str
    id: str
    title_he: str
    column_preset: ColumnPresetKey
    include_default_progress_rows: bool


DEFAULT_FINISHING_CHECKLIST_BLOCK_ID: Final = "default-finishing-checklist"

DEFAULT_FINISHING_CHECKLIST_TITLE_HE: Final = FINISHING_APARTMENTS_PROGRESS_TITLE_HE

FINISHING_CHECKLIST_ITEM_DEFS: Final = [
    {"id": "owners", "label_he": "בעלים"},
    {"id": "spaces", "label_he": "בדיקת חללים"},
    {"id": "electrical", "label_he": "חשמל"},
    {"id": "plumbing", "label_he": "אינסטלציה"},
    {"id": "wet_rooms_sealing", "label_he": "איטום חדרים רטובים"},
    {"id": "balcony_sealing", "label_he": "איטום מרפסות"},
]


def default_finishing_checklist_items() -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for index, definition in enumerate(FINISHING_CHECKLIST_ITEM_DEFS):
        items.append(
            {
                "id": f"checklist-{definition['id']}",
                "label_he": definition["label_he"],
                "checked": False,
                "notes": None,
                "sort_order": index,
            }
        )
    return items


DEFAULT_BLOCKS_BY_VISIT_TYPE: dict[str, list[BlockTemplate]] = {
    "STRUCTURE_SITE": [
        {
            "kind": "progress_table",
            "id": "default-progress-table",
            "title_he": STRUCTURE_SITE_PROGRESS_TITLE_HE,
            "column_preset": "structure",
            "include_default_progress_rows": True,
        },
        {
            "kind": "findings_table",
            "id": "default-findings-table",
            "title_he": "ממצאים נוספים",
            "column_preset": "simple",
        },
    ],
    "FINISHING_APARTMENTS": [
        {
            "kind": "checklist",
            "id": DEFAULT_FINISHING_CHECKLIST_BLOCK_ID,
            "title_he": DEFAULT_FINISHING_CHECKLIST_TITLE_HE,
        },
        {
            "kind": "findings_table",
            "id": "default-lobby-findings",
            "title_he": FINISHING_LOBBY_FINDINGS_TITLE_HE,
            "column_preset": "finishing",
        },
        {
            "kind": "findings_table",
            "id": "default-apartment-findings",
            "title_he": FINISHING_APARTMENT_FINDINGS_TITLE_HE,
            "column_preset": "finishing",
        },
    ],
    VISIT_TYPE_MIXED: [
        {
            "kind": "progress_table",
            "id": "default-progress-table",
            "title_he": "התקדמות הבנייה",
            "column_preset": "progress",
            "include_default_progress_rows": True,
        },
        {
            "kind": "findings_table",
            "id": "default-findings-table",
            "title_he": "ממצאים / עבודות",
            "column_preset": "rich",
        },
    ],
}


def column_preset_headers(key: ColumnPresetKey) -> list[str]:
    return [column["header_he"] for column in COLUMN_PRESETS[key]]


def _progress_rows_from_defaults(visit_type: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(default_construction_progress_rows(visit_type)):
        rows.append(
            {
                "id": f"default-progress-row-{index}",
                "description": row["description"],
                "status": row["status"],
                "completion_date": row["completion_date"],
                "sort_order": index,
            }
        )
    return rows


def default_report_blocks_for_visit_type(visit_type: str) -> list[dict[str, Any]]:
    templates = DEFAULT_BLOCKS_BY_VISIT_TYPE.get(visit_type)
    if not templates:
        return []

    blocks: list[dict[str, Any]] = []
    for sort_order, template in enumerate(templates):
        base: dict[str, Any] = {
            "id": template["id"],
            "title_he": template["title_he"],
            "sort_order": sort_order,
            "kind": template["kind"],
        }

        if template["kind"] == "progress_table":
            rows: list[dict[str, Any]] = []
            if template.get("include_default_progress_rows"):
                rows = _progress_rows_from_defaults(visit_type)
            blocks.append(
                {
                    **base,
                    "column_preset": template.get("column_preset", "progress"),
                    "rows": rows,
                }
            )
            continue

        if template["kind"] == "findings_table":
            blocks.append(
                {
                    **base,
                    "column_preset": template.get("column_preset", "rich"),
                    "rows": [],
                }
            )
            continue

        if template["kind"] == "checklist":
            blocks.append(
                {
                    **base,
                    "items": default_finishing_checklist_items(),
                }
            )

    return blocks


WINTER_SEASON_MONTHS: Final = frozenset({10, 11, 12, 1, 2, 3})


def is_winter_season_date(value: str | date | datetime | None) -> bool:
    """אוקטובר–מרץ - להפעלת המלצות חורף בדוח חדש (FR-4.2)."""
    if value is None:
        return False
    if isinstance(value, datetime):
        parsed = value.date()
    elif isinstance(value, date):
        parsed = value
    else:
        text = str(value).strip()
        if not text:
            return False
        try:
            parsed = date.fromisoformat(text[:10])
        except ValueError:
            return False
    return parsed.month in WINTER_SEASON_MONTHS


def default_fixed_text_blocks(
    *,
    visit_date: str | date | datetime | None = None,
) -> list[dict[str, Any]]:
    enable_winter = is_winter_season_date(visit_date)
    return [
        {
            "id": "default-non-conformance-disclaimer",
            "kind": "non_conformance_disclaimer",
            "body_he": DEFAULT_NON_CONFORMANCE_DISCLAIMER_HE,
            "enabled": True,
            "sort_order": 0,
        },
        {
            "id": "default-safety-disclaimer",
            "kind": "safety_disclaimer",
            "body_he": DEFAULT_SAFETY_DISCLAIMER_HE,
            "enabled": True,
            "sort_order": 1,
        },
        {
            "id": "default-winter-recommendations",
            "kind": "winter_recommendations",
            "title_he": "המלצות חורף / עונת גשמים",
            "body_he": DEFAULT_WINTER_RECOMMENDATIONS_HE,
            "enabled": enable_winter,
            "sort_order": 2,
        },
    ]


def default_fixed_text_blocks_for_new_report(
    visit_date: str | date | datetime | None = None,
) -> list[dict[str, Any]]:
    """Boilerplate לדוח חדש - mirrors buildFixedTextBlocksForNewReport (FR-4.2)."""
    return default_fixed_text_blocks(visit_date=visit_date)


def get_column_preset(key: ColumnPresetKey) -> list[dict[str, str]]:
    return deepcopy(COLUMN_PRESETS[key])
