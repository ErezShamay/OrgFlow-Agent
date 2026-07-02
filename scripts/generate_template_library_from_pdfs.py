#!/usr/bin/env python3
"""Generate per-PDF template definitions from docs/*.pdf examples."""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

from pypdf import PdfReader

REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = REPO_ROOT / "docs"
OUTPUT_JSON = (
    REPO_ROOT / "orgflow-ui/lib/field-reports/template-library-data.json"
)

CATEGORY_RULES: list[tuple[str, str, list[str]]] = [
    ("home_inspection", "בדק בית", ["בדק בית", "בדק+בית", "בדיקת קרינה"]),
    ("leak_detection", "מאתר נזילות", ["נזילות", "איתור נזילות"]),
    ("construction_supervision", "פיקוח בניה", ["פיקוח יזם", "פיקוח עליון", "פיקוח-"]),
    ("tenant_supervision", "פיקוח דיירים", ["פיקוח מטעם", "פיקוח דייר", "בקרה דיירתי"]),
    ("delivery_protocol", "פרוטוקול מסירת דירה", ["פרוטוקול מסירה", "מסירת דירה", "אישור קבלת"]),
    ("construction", "קונסטרוקציה", ["קונסטרוקטור", "קונס"]),
    ("architecture", "אדריכלות/עיצוב פנים", ["אדריכלות", "עיצוב פנים"]),
    ("execution", "ביצוע", ["ביצוע", "מדידות"]),
    ("safety", "בטיחות", ["בטיחות", "ביקורת בטיחות", "מבדק בטיחות"]),
    ("appraiser", "שמאי רכוש", ["שמאי", "חוות דעת"]),
    ("quality", "בקרת איכות", ["בקרת איכות", "בקרה"]),
    ("general", "כללי", []),
]

VISIT_TYPE_RULES: list[tuple[str, list[str]]] = [
    ("STRUCTURE_SITE", ["שלד", "אתר", "בטיחות", "קונסטרוק"]),
    ("FINISHING_APARTMENTS", ["גמר", "דירה", "מסירה", "בדק בית"]),
    ("MIXED", []),
]


def decode_filename(name: str) -> str:
    stem = Path(name).stem
    if stem.startswith("_") and "_D7_" in stem or "_D6_" in stem:
        hex_parts = re.findall(r"_([0-9A-Fa-f]{2})", stem)
        if hex_parts:
            try:
                raw = bytes(int(part, 16) for part in hex_parts)
                return raw.decode("utf-8")
            except UnicodeDecodeError:
                pass
    return stem.replace("+", " ").strip()


def slugify(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    asciiish = re.sub(r"[^\w\s-]", "", normalized, flags=re.UNICODE)
    asciiish = re.sub(r"[\s_]+", "-", asciiish.strip().lower())
    asciiish = re.sub(r"-+", "-", asciiish)
    if asciiish:
        return asciiish[:80]
    digest = abs(hash(text)) % 10_000_000
    return f"template-{digest}"


def extract_pdf_text(path: Path, max_pages: int = 6) -> str:
    try:
        reader = PdfReader(str(path))
    except Exception:
        return ""
    chunks: list[str] = []
    for page in list(reader.pages)[:max_pages]:
        try:
            text = page.extract_text() or ""
        except Exception:
            text = ""
        if text:
            chunks.append(text)
    return "\n".join(chunks)


def resolve_category(label: str) -> tuple[str, str]:
    for cat_id, cat_title, keywords in CATEGORY_RULES:
        if any(keyword in label for keyword in keywords):
            return cat_id, cat_title
    return "general", "כללי"


def resolve_visit_type(label: str, text: str) -> str:
    haystack = f"{label}\n{text}"
    for visit_type, keywords in VISIT_TYPE_RULES:
        if any(keyword in haystack for keyword in keywords):
            return visit_type
    return "MIXED"


def infer_blocks(label: str, text: str) -> list[dict]:
    haystack = f"{label}\n{text}".lower()
    blocks: list[dict] = [
        {"kind": "free_text", "title_he": "כותרת", "required": True},
    ]

    if any(word in haystack for word in ["פרטים כלליים", "פרטי הלקוח", "שם הלקוח", "כתובת"]):
        blocks.append(
            {"kind": "free_text", "title_he": "פרטים כלליים", "required": True}
        )

    if any(word in haystack for word in ["הצהרה", "הצהרת", "disclaimer"]):
        blocks.append({"kind": "free_text", "title_he": "הצהרה", "required": True})

    if any(
        word in haystack
        for word in ["השכלתי", "ניסיוני", "רישיון", "תעודה"]
    ):
        blocks.append(
            {
                "kind": "free_text",
                "title_he": "פרטי השכלתי וניסיוני",
                "required": False,
            }
        )

    if any(
        word in haystack
        for word in ["התקדמות", "מצב הביצוע", "שלבי בנייה", "טבלת התקדמות"]
    ):
        blocks.append(
            {
                "kind": "progress_table",
                "title_he": "טבלת התקדמות",
                "required": True,
            }
        )

    if any(word in haystack for word in ["צ'קליסט", "צקליסט", "רשימת בדיקות", "בדיקות"]):
        blocks.append(
            {"kind": "checklist", "title_he": "צ'קליסט בדיקות", "required": True}
        )

    if any(
        word in haystack
        for word in ["ליקוי", "ליקויים", "ממצא", "ממצאים", "טבלה", "פירוט"]
    ):
        blocks.append(
            {
                "kind": "findings_table",
                "title_he": "טבלת ממצאים / ליקויים",
                "required": True,
            }
        )

    if any(word in haystack for word in ["תמונה", "תמונות", "צילום", "הדמיה"]):
        blocks.append({"kind": "image", "title_he": "תמונות", "required": False})

    if any(word in haystack for word in ["סיכום", "המלצות", "מסקנות", "סיכום דיון"]):
        blocks.append(
            {"kind": "free_text", "title_he": "סיכום והמלצות", "required": False}
        )

    # Filename-based fallbacks when extraction is weak.
    if len(blocks) <= 2:
        if "בדק" in label or "ליקוי" in label:
            blocks.append(
                {
                    "kind": "findings_table",
                    "title_he": "טבלת ליקויים",
                    "required": True,
                }
            )
        if "פיקוח" in label or "בקרה" in label:
            blocks.append(
                {
                    "kind": "progress_table",
                    "title_he": "התקדמות עבודות",
                    "required": True,
                }
            )
            blocks.append(
                {
                    "kind": "findings_table",
                    "title_he": "טבלת ממצאים",
                    "required": True,
                }
            )
        if "פרוטוקול" in label or "מסירה" in label:
            blocks.append(
                {
                    "kind": "checklist",
                    "title_he": "רשימת אביזרים ומערכות",
                    "required": True,
                }
            )
            blocks.append(
                {
                    "kind": "findings_table",
                    "title_he": "ליקויים במסירה",
                    "required": True,
                }
            )
        if "בטיחות" in label:
            blocks.append(
                {"kind": "checklist", "title_he": "צ'קליסט בטיחות", "required": True}
            )

    if not any(block["kind"] == "findings_table" for block in blocks):
        if any(word in label for word in ["דוח", "פרוטוקול", "חוות דעת"]):
            blocks.append(
                {
                    "kind": "findings_table",
                    "title_he": "טבלת ממצאים",
                    "required": False,
                }
            )

    # Deduplicate by kind+title
    seen: set[str] = set()
    unique: list[dict] = []
    for block in blocks:
        key = f"{block['kind']}::{block['title_he']}"
        if key in seen:
            continue
        seen.add(key)
        unique.append(block)
    return unique


def build_library() -> list[dict]:
    pdfs = sorted(DOCS_DIR.glob("*.pdf"), key=lambda p: decode_filename(p.name))
    categories: dict[str, dict] = {}

    used_ids: set[str] = set()
    for pdf_path in pdfs:
        label = decode_filename(pdf_path.name)
        text = extract_pdf_text(pdf_path)
        cat_id, cat_title = resolve_category(label)
        visit_type = resolve_visit_type(label, text)
        template_id = slugify(label)
        suffix = 2
        while template_id in used_ids:
            template_id = f"{slugify(label)}-{suffix}"
            suffix += 1
        used_ids.add(template_id)

        item = {
            "id": template_id,
            "label_he": label,
            "visitType": visit_type,
            "examplePdf": pdf_path.name,
            "blocks": infer_blocks(label, text),
        }

        if cat_id not in categories:
            categories[cat_id] = {
                "id": cat_id,
                "title_he": cat_title,
                "items": [],
            }
        categories[cat_id]["items"].append(item)

    ordered: list[dict] = []
    for cat_id, _, _ in CATEGORY_RULES:
        if cat_id in categories and categories[cat_id]["items"]:
            ordered.append(categories.pop(cat_id))
    for remaining in categories.values():
        if remaining["items"]:
            ordered.append(remaining)
    return ordered


def main() -> None:
    library = build_library()
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(
        json.dumps(library, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    total_items = sum(len(cat["items"]) for cat in library)
    print(f"Wrote {total_items} templates across {len(library)} categories")
    print(f"Output: {OUTPUT_JSON}")


if __name__ == "__main__":
    main()
