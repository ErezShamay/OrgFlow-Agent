from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime

VISIT_TYPE_LABELS_HE: dict[str, str] = {
    "STRUCTURE_SITE": "שלד ואתר",
    "FINISHING_APARTMENTS": "גמר דירות",
    "MIXED": "משולב",
}

HEBREW_MONTH_LABELS: dict[int, str] = {
    1: "ינואר",
    2: "פברואר",
    3: "מרץ",
    4: "אפריל",
    5: "מאי",
    6: "יוני",
    7: "יולי",
    8: "אוגוסט",
    9: "ספטמבר",
    10: "אוקטובר",
    11: "נובמבר",
    12: "דצמבר",
}


def _visit_type_label(visit_type: str) -> str:
    return VISIT_TYPE_LABELS_HE.get(visit_type, visit_type or "דוח ביקור")


def _parse_visit_date(value: str | None) -> date | None:
    if not value:
        return None

    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def build_project_field_report_archive(
    records: list[dict],
    *,
    project_id: str,
    project_name: str | None = None,
) -> dict:
    by_year: dict[int, dict[int, list[dict]]] = defaultdict(
        lambda: defaultdict(list)
    )

    for record in records:
        storage_path = str(record.get("pdf_storage_path") or "").strip()
        if not storage_path:
            continue

        visit = _parse_visit_date(record.get("visit_date"))
        if not visit:
            continue

        report_id = str(record.get("id") or "")
        visit_type = str(record.get("visit_type") or "")
        by_year[visit.year][visit.month].append(
            {
                "id": report_id,
                "visit_date": visit.isoformat(),
                "visit_type": visit_type,
                "visit_type_label_he": _visit_type_label(visit_type),
                "pdf_filename": (
                    record.get("pdf_filename")
                    or f"field-visit-{visit.isoformat()}-{report_id}.pdf"
                ),
                "locked_at": record.get("locked_at"),
                "closed_at": record.get("closed_at"),
            }
        )

    years: list[dict] = []
    total_reports = 0

    for year in sorted(by_year.keys(), reverse=True):
        months: list[dict] = []

        for month in sorted(by_year[year].keys(), reverse=True):
            reports = sorted(
                by_year[year][month],
                key=lambda item: item["visit_date"],
                reverse=True,
            )
            total_reports += len(reports)
            months.append(
                {
                    "month": month,
                    "month_label_he": HEBREW_MONTH_LABELS.get(
                        month,
                        str(month),
                    ),
                    "reports": reports,
                }
            )

        years.append(
            {
                "year": year,
                "months": months,
            }
        )

    return {
        "project_id": project_id,
        "project_name": project_name,
        "years": years,
        "total_reports": total_reports,
        "generated_at": datetime.now().isoformat(),
    }
