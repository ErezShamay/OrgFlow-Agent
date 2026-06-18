"""L4 — global standards_and_regulations seed (Competitive Layer v2)."""

from __future__ import annotations

from typing import Any

STANDARD_TI_1752_SILL_ID = "00000000-0000-4000-8002-000000000001"
STANDARD_MAMAD_REGS_ID = "00000000-0000-4000-8002-000000000002"
STANDARD_HLT_VENT_4M3_ID = "00000000-0000-4000-8002-000000000003"

STANDARDS_SEED: tuple[dict[str, Any], ...] = (
    {
        "id": STANDARD_TI_1752_SILL_ID,
        "standard_code": "TI-1752-SILL",
        "category": "איטום ובידוד",
        "title": 'ת"י 1752 — איטום מפתנים',
        "raw_legal_text": (
            "תקן ישראלי 1752 מגדיר דרישות לאיטום ממשקי רצפה-קיר, מפתנים "
            "ומרפסות למניעת חדירת מים לבניין."
        ),
        "recommended_remedy": (
            "התקנת רולקה בזווית רצפה-קיר, יריעת איטום רציפה ואטימת מפתנים "
            "לפי הוראות היצרן והמהנדס."
        ),
        "version": "2018",
        "effective_from": "2018-01-01",
        "ref_aliases": [
            'ת"י 1752',
            'ת"י 1752 ח"1',
            "TI-1752",
            "1752",
        ],
    },
    {
        "id": STANDARD_MAMAD_REGS_ID,
        "standard_code": "MAMAD-REGS",
        "category": "מיגון וממ\"ד",
        "title": 'תקנות ממ"ד — חלון הדף, משקוף גזים',
        "raw_legal_text": (
            "תקנות הממ\"ד מחייבות התקנת חלון הדף, משקוף גזים ואטימה "
            "התואמת את דרישות המיגון בדירת הממ\"ד."
        ),
        "recommended_remedy": (
            "התקנת חלון הדף ומשקוף גזים מאושרים, אטימה היקפית ואישור "
            "ממונה בטיחות לפני גמר."
        ),
        "version": "2020",
        "effective_from": "2020-01-01",
        "ref_aliases": [
            'תקנות ממ"ד',
            "ממ\"ד",
            "MAMAD",
        ],
    },
    {
        "id": STANDARD_HLT_VENT_4M3_ID,
        "standard_code": "HLT-VENT-4M3",
        "category": "אוורור ומערכות",
        "title": 'הל"ת — וונטה 4 צול',
        "raw_legal_text": (
            "הוראות הל\"ת מחייבות אוורור מספק בחדרים רטובים — לפחות "
            "4 מ\"ק לשעה לצול אוורור."
        ),
        "recommended_remedy": (
            "התקנת וונטה/מפוח מתאים עם נפח אוורור של לפחות 4 מ\"ק/שעה "
            "לצול, כולל בדיקת זרימה ואטימה."
        ),
        "version": "2021",
        "effective_from": "2021-01-01",
        "ref_aliases": [
            'הל"ת',
            "HLT",
            "וונטה 4 צול",
        ],
    },
)


def iter_seed_standards() -> tuple[dict[str, Any], ...]:
    return STANDARDS_SEED


def seed_standard_by_id(standard_id: str) -> dict[str, Any] | None:
    for record in STANDARDS_SEED:
        if str(record.get("id")) == standard_id:
            return dict(record)
    return None


def seed_standard_by_code(standard_code: str) -> dict[str, Any] | None:
    normalized = (standard_code or "").strip().upper()
    for record in STANDARDS_SEED:
        if str(record.get("standard_code") or "").upper() == normalized:
            return dict(record)
    return None
