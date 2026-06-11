from __future__ import annotations

from app.config.field_report_catalog_supplement import SUPPLEMENT_ISSUES
from app.services.field_report_catalog_parser import (
    load_catalog_from_directory,
)
from app.services.field_report_catalog_service import (
    FieldReportCatalogService,
)


def test_catalog_loads_with_supplement() -> None:
    catalog = load_catalog_from_directory()
    assert catalog["issue_count"] >= len(SUPPLEMENT_ISSUES)
    assert catalog["supplement_issue_count"] == len(SUPPLEMENT_ISSUES)
    assert catalog["errors"]


def test_catalog_filters_by_visit_type() -> None:
    service = FieldReportCatalogService()
    structure = service.get_catalog_for_visit_type("STRUCTURE_SITE")
    finishing = service.get_catalog_for_visit_type(
        "FINISHING_APARTMENTS"
    )
    mixed = service.get_catalog_for_visit_type("MIXED")
    full = service.get_full_catalog()

    structure_families = {
        item["top_family"] for item in structure["issues"]
    }
    finishing_families = {
        item["top_family"] for item in finishing["issues"]
    }

    assert "STRUCTURAL_WORKS" in structure_families
    assert "STRUCTURAL_WORKS" not in finishing_families
    assert "FINISHING_WORKS" in finishing_families
    assert "FINISHING_WORKS" not in structure_families
    assert mixed["issue_count"] == full["issue_count"]


def test_find_issue_str_02_001_if_present() -> None:
    service = FieldReportCatalogService()
    issue = service.find_issue("str-02-001")
    if issue is None:
        supplement = service.find_issue("QC-STR-001")
        assert supplement is not None
        assert supplement["issue_id"] == "QC-STR-001"
        return

    assert issue["issue_id"] == "STR-02-001"
    assert "466" in (issue.get("standard_ref") or "")
