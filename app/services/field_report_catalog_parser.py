from __future__ import annotations

import re
from pathlib import Path

from app.config.field_report_catalog_supplement import (
    SUPPLEMENT_CATALOG_VERSION,
    SUPPLEMENT_CATEGORIES_UNIQUE,
    SUPPLEMENT_FAMILIES,
    SUPPLEMENT_ISSUES,
)

VERSION_RE = re.compile(
    r"^#\s*Version:\s*(\S+)",
    re.MULTILINE,
)
TOP_FAMILY_RE = re.compile(
    r"^###\s+TOP_FAMILY:\s*(\S+)",
    re.MULTILINE,
)
CATEGORY_RE = re.compile(
    r"^####\s+CATEGORY_\d+:\s*(\S+)\s*\(([^)]+)\)",
    re.MULTILINE,
)
ISSUE_HEADER_RE = re.compile(
    r"^#####\s+Issue_ID:\s*(\S+)",
    re.MULTILINE,
)
FIELD_RE = re.compile(
    r"^\*\s+\*\*([^*]+):\*\*\s*(.+)$",
    re.MULTILINE,
)
CATEGORY_STANDARD_RE = re.compile(
    r"^\*\s+\*\*Standard_ID:\*\*\s*(.+)$",
    re.MULTILINE,
)
CATEGORY_TARGET_RE = re.compile(
    r"^\*\s+\*\*Target_Elements:\*\*\s*(.+)$",
    re.MULTILINE,
)

ALLOWED_SEVERITIES = frozenset(
    {"Critical", "High", "Medium", "Low"}
)

CATALOG_FILE_SPECS: tuple[tuple[str, str], ...] = (
    (
        "STRUCTURAL_WORKS",
        "קובץ מפרט- שלד, קונסטרוקציה ובטונים.md",
    ),
    (
        "FINISHING_WORKS",
        "קובץ מפרט- עבודות גמר, ארכיטקטורה ופנים.md",
    ),
    (
        "MECHANICAL_ELECTRICAL_SYSTEMS",
        (
            "קובץ מפרט- מערכות אלקטרו-מכניות "
            "(אינסטלציה, חשמל ובטיחות).md"
        ),
    ),
    (
        "SYSTEM_WATERPROOFING_AND_INSULATION",
        "איטום.md",
    ),
)


class CatalogParseError(ValueError):
    pass


def parse_catalog_markdown(
    content: str,
    *,
    expected_top_family: str,
    source_file: str,
) -> dict:
    version_match = VERSION_RE.search(content)
    if not version_match:
        raise CatalogParseError(
            f"{source_file}: missing # Version: line"
        )

    catalog_version = version_match.group(1)
    top_family_match = TOP_FAMILY_RE.search(content)
    if not top_family_match:
        raise CatalogParseError(
            f"{source_file}: missing TOP_FAMILY heading"
        )

    file_top_family = top_family_match.group(1)
    if file_top_family != expected_top_family:
        raise CatalogParseError(
            f"{source_file}: TOP_FAMILY {file_top_family} "
            f"!= expected {expected_top_family}"
        )

    categories: list[dict] = []
    issues: list[dict] = []
    seen_issue_ids: set[str] = set()

    category_matches = list(CATEGORY_RE.finditer(content))
    issue_matches = list(ISSUE_HEADER_RE.finditer(content))

    for index, category_match in enumerate(category_matches):
        category_id = category_match.group(1)
        category_name_he = category_match.group(2).strip()
        category_start = category_match.start()
        category_end = (
            category_matches[index + 1].start()
            if index + 1 < len(category_matches)
            else len(content)
        )
        category_block = content[category_start:category_end]

        category_standard_id = _first_match(
            CATEGORY_STANDARD_RE,
            category_block,
        )
        target_elements = _first_match(
            CATEGORY_TARGET_RE,
            category_block,
        )

        categories.append(
            {
                "top_family": expected_top_family,
                "category_id": category_id,
                "category_name_he": category_name_he,
                "category_standard_id": category_standard_id,
                "target_elements": target_elements,
            }
        )

        category_issues = [
            issue_match
            for issue_match in issue_matches
            if category_start <= issue_match.start() < category_end
        ]

        for issue_match in category_issues:
            issue_id = issue_match.group(1).upper()
            issue_start = issue_match.start()
            issue_end = _next_boundary(
                content,
                issue_start,
                category_end,
                issue_matches,
                category_matches,
            )
            issue_block = content[issue_start:issue_end]
            fields = {
                key.strip(): value.strip()
                for key, value in FIELD_RE.findall(issue_block)
            }

            _require_issue_fields(
                issue_id=issue_id,
                fields=fields,
                source_file=source_file,
            )

            severity = fields["Severity"]
            if severity not in ALLOWED_SEVERITIES:
                raise CatalogParseError(
                    f"{source_file} {issue_id}: "
                    f"invalid Severity {severity!r}"
                )

            if issue_id in seen_issue_ids:
                raise CatalogParseError(
                    f"duplicate issue_id {issue_id} in {source_file}"
                )
            seen_issue_ids.add(issue_id)

            standard_ref = fields.get("Standard_Ref") or None
            issues.append(
                {
                    "issue_id": issue_id,
                    "top_family": expected_top_family,
                    "category_id": category_id,
                    "category_name_he": category_name_he,
                    "category_standard_id": category_standard_id,
                    "target_elements": target_elements,
                    "issue_name_he": fields["Issue_Name_HE"],
                    "standard_ref": standard_ref,
                    "severity": severity,
                    "description": fields["Report_Text_HE"],
                    "engineering_impact": fields[
                        "Engineering_Impact_HE"
                    ],
                    "rectification_action": fields[
                        "Rectification_Action_HE"
                    ],
                }
            )

    return {
        "top_family": expected_top_family,
        "source_file": source_file,
        "catalog_version": catalog_version,
        "categories": categories,
        "issues": issues,
        "issue_count": len(issues),
    }


def load_catalog_from_directory(
    md_root: Path | None = None,
) -> dict:
    root = md_root or Path(__file__).resolve().parents[2] / "md_files"
    families: list[dict] = []
    categories: list[dict] = []
    issues: list[dict] = []
    errors: list[dict] = []
    versions: set[str] = set()
    global_issue_ids: set[str] = set()

    for top_family, filename in CATALOG_FILE_SPECS:
        path = root / filename
        if not path.is_file():
            errors.append(
                {
                    "source_file": filename,
                    "message": "file not found",
                }
            )
            continue

        try:
            parsed = parse_catalog_markdown(
                path.read_text(encoding="utf-8"),
                expected_top_family=top_family,
                source_file=filename,
            )
        except (CatalogParseError, OSError) as error:
            errors.append(
                {
                    "source_file": filename,
                    "message": str(error),
                }
            )
            continue

        versions.add(parsed["catalog_version"])
        families.append(
            {
                "top_family": parsed["top_family"],
                "source_file": parsed["source_file"],
                "issue_count": parsed["issue_count"],
            }
        )
        categories.extend(parsed["categories"])

        for issue in parsed["issues"]:
            issue_id = issue["issue_id"]
            if issue_id in global_issue_ids:
                errors.append(
                    {
                        "source_file": filename,
                        "message": (
                            f"duplicate global issue_id {issue_id}"
                        ),
                    }
                )
                continue
            global_issue_ids.add(issue_id)
            issues.append(issue)

    if len(versions) > 1:
        catalog_version = "mixed"
    elif versions:
        catalog_version = next(iter(versions))
    else:
        catalog_version = None

    catalog = {
        "catalog_version": catalog_version,
        "families": families,
        "categories": categories,
        "issues": issues,
        "issue_count": len(issues),
        "errors": errors,
    }
    return merge_catalog_supplement(catalog)


def merge_catalog_supplement(catalog: dict) -> dict:
    """Roadmap 6.4 - append embedded supplement issues/categories."""
    merged = dict(catalog)
    issues = list(catalog.get("issues") or [])
    categories = list(catalog.get("categories") or [])
    families = list(catalog.get("families") or [])
    global_issue_ids = {
        str(issue.get("issue_id") or "").upper()
        for issue in issues
        if issue.get("issue_id")
    }

    supplement_added = 0
    for issue in SUPPLEMENT_ISSUES:
        issue_id = str(issue["issue_id"]).upper()
        if issue_id in global_issue_ids:
            continue
        issues.append(dict(issue))
        global_issue_ids.add(issue_id)
        supplement_added += 1

    existing_categories = {
        (str(item.get("top_family")), str(item.get("category_id")))
        for item in categories
    }
    for category in SUPPLEMENT_CATEGORIES_UNIQUE:
        key = (category["top_family"], category["category_id"])
        if key in existing_categories:
            continue
        categories.append(dict(category))
        existing_categories.add(key)

    family_counts = {
        str(item.get("top_family")): int(item.get("issue_count") or 0)
        for item in families
    }
    for family in SUPPLEMENT_FAMILIES:
        top_family = family["top_family"]
        family_counts[top_family] = family_counts.get(top_family, 0) + int(
            family["issue_count"]
        )

    if not families:
        families = [
            {
                "top_family": top_family,
                "source_file": "field_report_catalog_supplement.py",
                "issue_count": count,
            }
            for top_family, count in sorted(family_counts.items())
        ]
    else:
        for family in families:
            top_family = str(family.get("top_family") or "")
            if top_family in family_counts:
                family["issue_count"] = family_counts[top_family]

    base_version = catalog.get("catalog_version")
    if supplement_added > 0:
        if base_version:
            merged["catalog_version"] = f"{base_version}+{SUPPLEMENT_CATALOG_VERSION}"
        else:
            merged["catalog_version"] = SUPPLEMENT_CATALOG_VERSION

    merged["issues"] = issues
    merged["categories"] = categories
    merged["families"] = families
    merged["issue_count"] = len(issues)
    merged["supplement_issue_count"] = supplement_added
    return merged


def _first_match(pattern: re.Pattern[str], text: str) -> str | None:
    match = pattern.search(text)
    if not match:
        return None
    return match.group(1).strip()


def _next_boundary(
    content: str,
    issue_start: int,
    category_end: int,
    issue_matches: list[re.Match[str]],
    category_matches: list[re.Match[str]],
) -> int:
    for issue_match in issue_matches:
        if issue_match.start() > issue_start:
            return min(issue_match.start(), category_end)

    for category_match in category_matches:
        if category_match.start() > issue_start:
            return min(category_match.start(), category_end)

    return category_end


def _require_issue_fields(
    *,
    issue_id: str,
    fields: dict[str, str],
    source_file: str,
) -> None:
    required = (
        "Issue_Name_HE",
        "Severity",
        "Report_Text_HE",
        "Engineering_Impact_HE",
        "Rectification_Action_HE",
    )
    missing = [name for name in required if name not in fields]
    if missing:
        raise CatalogParseError(
            f"{source_file} {issue_id}: "
            f"missing fields {', '.join(missing)}"
        )
