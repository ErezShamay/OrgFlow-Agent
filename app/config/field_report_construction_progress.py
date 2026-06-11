"""Default construction-progress table rows per visit type (appendix 0.2, task 3C.6)."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from app.config.field_report_visit_types import (
    VISIT_TYPE_FINISHING_APARTMENTS,
    VISIT_TYPE_MIXED,
    VISIT_TYPE_STRUCTURE_SITE,
)

ConstructionProgressRow = dict[str, str]

STRUCTURE_SITE_PROGRESS_TITLE_HE = "סטטוס בניה-שלד"
FINISHING_APARTMENTS_PROGRESS_TITLE_HE = "התקדמות הבנייה"
FINISHING_LOBBY_FINDINGS_TITLE_HE = "התקדמות עבודות הגמר לובי קומה"
FINISHING_APARTMENT_FINDINGS_TITLE_HE = "ממצאים בדירות"

DEFAULT_STRUCTURE_SITE_PROGRESS_ROWS: list[ConstructionProgressRow] = [
    {"description": "הריסת המבנה", "status": "", "completion_date": ""},
    {"description": "עבודות דיפון", "status": "", "completion_date": ""},
    {"description": "חפירה חניון תת קרקעי", "status": "", "completion_date": ""},
    {"description": "ביסוס המבנה", "status": "", "completion_date": ""},
    {
        "description": "יציקת רצפה קומת מינוס 2",
        "status": "",
        "completion_date": "",
    },
    {
        "description": "יציקת קירות קומת מינוס 2",
        "status": "",
        "completion_date": "",
    },
    {
        "description": "יציקת רצפה קומת מינוס 1",
        "status": "",
        "completion_date": "",
    },
    {
        "description": "יציקת קירות קומת מינוס 1",
        "status": "",
        "completion_date": "",
    },
    {
        "description": "יציקת רצפת קומת קרקע",
        "status": "",
        "completion_date": "",
    },
]

DEFAULT_FINISHING_APARTMENTS_PROGRESS_ROWS: list[ConstructionProgressRow] = [
    {
        "description": "עבודות גמר בדירות הבעלים",
        "status": "",
        "completion_date": "",
    },
    {"description": "חדר מדרגות", "status": "", "completion_date": ""},
    {"description": "לובי / מעברים", "status": "", "completion_date": ""},
    {
        "description": "מערכות חשמל בדירות",
        "status": "",
        "completion_date": "",
    },
    {
        "description": "מערכות אינסטלציה בדירות",
        "status": "",
        "completion_date": "",
    },
    {
        "description": "איטום חדרים רטובים ומרפסות",
        "status": "",
        "completion_date": "",
    },
]

VISIT_TYPE_PROGRESS_CONFIG: dict[str, dict[str, Any]] = {
    VISIT_TYPE_STRUCTURE_SITE: {
        "title_he": STRUCTURE_SITE_PROGRESS_TITLE_HE,
        "default_rows": DEFAULT_STRUCTURE_SITE_PROGRESS_ROWS,
    },
    VISIT_TYPE_FINISHING_APARTMENTS: {
        "title_he": FINISHING_APARTMENTS_PROGRESS_TITLE_HE,
        "default_rows": DEFAULT_FINISHING_APARTMENTS_PROGRESS_ROWS,
    },
    VISIT_TYPE_MIXED: {
        "title_he": FINISHING_APARTMENTS_PROGRESS_TITLE_HE,
        "default_rows": DEFAULT_FINISHING_APARTMENTS_PROGRESS_ROWS,
    },
}


def default_construction_progress_rows(
    visit_type: str,
) -> list[ConstructionProgressRow]:
    config = VISIT_TYPE_PROGRESS_CONFIG.get(visit_type)
    if not config:
        return []
    return deepcopy(config["default_rows"])


def construction_progress_title_he(visit_type: str) -> str:
    config = VISIT_TYPE_PROGRESS_CONFIG.get(visit_type)
    if not config:
        return "התקדמות הבנייה"
    return str(config["title_he"])
