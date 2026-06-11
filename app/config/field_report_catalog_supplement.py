"""Embedded catalog supplement - roadmap 6.4.

Adds QC-focused catalog issues when markdown sources are unavailable or as
an extension on top of the parsed md_files catalog.
"""

from __future__ import annotations

SUPPLEMENT_CATALOG_VERSION = "1.2.0-supplement"

SUPPLEMENT_ISSUES: tuple[dict, ...] = (
    {
        "issue_id": "QC-STR-001",
        "top_family": "STRUCTURAL_WORKS",
        "category_id": "REINFORCEMENT_STEEL",
        "category_name_he": "ברזל זיון",
        "category_standard_id": 'ת"י 466 חלק 1',
        "target_elements": "קורות, עמודים, תקרות",
        "issue_name_he": "כיסוי בטון לא מספיק בזיון חשוף",
        "standard_ref": 'ת"י 466 חלק 1',
        "severity": "High",
        "description": "זיון חשוף ללא כיסוי בטון מתוכנן לפני יציקה.",
        "engineering_impact": "קורוזיה וירידת דבק בטון-פלדה.",
        "rectification_action": "להתקין ספייסרים ולאשר לפני יציקה.",
    },
    {
        "issue_id": "QC-STR-002",
        "top_family": "STRUCTURAL_WORKS",
        "category_id": "CONCRETE_PLACING",
        "category_name_he": "יציקת בטון",
        "category_standard_id": 'ת"י 466',
        "target_elements": "יסודות, קורות, תקרות",
        "issue_name_he": "יציקה ללא בדיקת תכולות",
        "standard_ref": 'ת"י 466',
        "severity": "Critical",
        "description": "בוצעה יציקה ללא תיעוד תכולות וסומך.",
        "engineering_impact": "חולשת מבנית נסתרת.",
        "rectification_action": "לעצור ולבצע בדיקה לפי הנחיית מהנדס.",
    },
    {
        "issue_id": "QC-FIN-001",
        "top_family": "FINISHING_WORKS",
        "category_id": "PLASTER_AND_PAINT",
        "category_name_he": "טיח וצבע",
        "category_standard_id": 'ת"י 466 חלק 2',
        "target_elements": "קירות, תקרות",
        "issue_name_he": "סדקים פעילים לפני שכבת גמר",
        "standard_ref": 'ת"י 466 חלק 2',
        "severity": "Medium",
        "description": "סדקים בטיח לפני צביעה/ריצוף.",
        "engineering_impact": "התפשטות סדקים בשכבות גמר.",
        "rectification_action": "לטפל במקור הסדק לפני המשך גמר.",
    },
    {
        "issue_id": "QC-FIN-002",
        "top_family": "FINISHING_WORKS",
        "category_id": "TILING",
        "category_name_he": "ריצוף וחיפוי",
        "category_standard_id": 'ת"י 4458',
        "target_elements": "רצפות, קירות רטובים",
        "issue_name_he": "שיפוע לא מספיק בחדר רטוב",
        "standard_ref": 'ת"י 4458',
        "severity": "High",
        "description": "שיפוע ריצוף בחדר רטוב לא עומד בדרישה.",
        "engineering_impact": "הצטברות מים ורטיבות.",
        "rectification_action": "לתקן שיפוע לפני המשך עבודות.",
    },
    {
        "issue_id": "QC-MEP-001",
        "top_family": "MECHANICAL_ELECTRICAL_SYSTEMS",
        "category_id": "PLUMBING",
        "category_name_he": "אינסטלציה",
        "category_standard_id": 'ת"י 1205',
        "target_elements": "צנרת, נקודות מים",
        "issue_name_he": "בדיקת לחץ לא בוצעה",
        "standard_ref": 'ת"י 1205',
        "severity": "High",
        "description": "לא בוצעה בדיקת לחץ לפני סגירת קירות.",
        "engineering_impact": "נזילות נסתרות.",
        "rectification_action": "לבצע בדיקת לחץ ולתעד.",
    },
    {
        "issue_id": "QC-MEP-002",
        "top_family": "MECHANICAL_ELECTRICAL_SYSTEMS",
        "category_id": "ELECTRICAL",
        "category_name_he": "חשמל",
        "category_standard_id": 'ת"י 60364',
        "target_elements": "לוחות, נקודות",
        "issue_name_he": "חוסר אביזר הגנה בלוח חשמל",
        "standard_ref": 'ת"י 60364',
        "severity": "Critical",
        "description": "לוח חשמל ללא אביזרי הגנה מתאימים.",
        "engineering_impact": "סיכון בטיחותי.",
        "rectification_action": "להשלים הגנה לפני חיבור.",
    },
    {
        "issue_id": "QC-INS-001",
        "top_family": "SYSTEM_WATERPROOFING_AND_INSULATION",
        "category_id": "WATERPROOFING",
        "category_name_he": "איטום",
        "category_standard_id": 'ת"י 2752',
        "target_elements": "גגות, מרפסות",
        "issue_name_he": "יריעת איטום לא מחוברת למעקה",
        "standard_ref": 'ת"י 2752',
        "severity": "High",
        "description": "חיבור יריעה למעקה/סף לא תקין.",
        "engineering_impact": "חדירת מים למבנה.",
        "rectification_action": "להלחים ולאטום לפי יצרן.",
    },
    {
        "issue_id": "QC-INS-002",
        "top_family": "SYSTEM_WATERPROOFING_AND_INSULATION",
        "category_id": "THERMAL_INSULATION",
        "category_name_he": "בידוד תרמי",
        "category_standard_id": 'ת"י 1045',
        "target_elements": "חזיתות, גג",
        "issue_name_he": "רציפות בידוד נשברה",
        "standard_ref": 'ת"י 1045',
        "severity": "Medium",
        "description": "קפיצות/חורים בבידוד תרמי.",
        "engineering_impact": "גשר תרמי ורטיבות.",
        "rectification_action": "להשלים בידוד רציף לפני חיפוי.",
    },
)

SUPPLEMENT_CATEGORIES: tuple[dict, ...] = tuple(
    {
        "top_family": issue["top_family"],
        "category_id": issue["category_id"],
        "category_name_he": issue["category_name_he"],
        "category_standard_id": issue["category_standard_id"],
        "target_elements": issue["target_elements"],
    }
    for issue in SUPPLEMENT_ISSUES
)

# Deduplicate categories while preserving order
_seen_categories: set[tuple[str, str]] = set()
SUPPLEMENT_CATEGORIES_UNIQUE: list[dict] = []
for category in SUPPLEMENT_CATEGORIES:
    key = (category["top_family"], category["category_id"])
    if key in _seen_categories:
        continue
    _seen_categories.add(key)
    SUPPLEMENT_CATEGORIES_UNIQUE.append(category)

SUPPLEMENT_FAMILIES: tuple[dict, ...] = tuple(
    {
        "top_family": family,
        "source_file": "field_report_catalog_supplement.py",
        "issue_count": sum(
            1 for issue in SUPPLEMENT_ISSUES if issue["top_family"] == family
        ),
    }
    for family in sorted({issue["top_family"] for issue in SUPPLEMENT_ISSUES})
)
