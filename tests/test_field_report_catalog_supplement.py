"""Roadmap 6.4 - catalog supplement merge."""

from __future__ import annotations

from app.config.field_report_catalog_supplement import SUPPLEMENT_ISSUES
from app.services.field_report_catalog_parser import (
    load_catalog_from_directory,
    merge_catalog_supplement,
)
from app.services.field_report_catalog_service import FieldReportCatalogService


def test_catalog_includes_supplement_when_md_files_missing() -> None:
    catalog = load_catalog_from_directory()
    assert catalog["issue_count"] >= len(SUPPLEMENT_ISSUES)
    assert catalog["supplement_issue_count"] == len(SUPPLEMENT_ISSUES)
    assert catalog["catalog_version"] is not None


def test_merge_catalog_supplement_is_idempotent_for_issue_ids() -> None:
    base = {
        "catalog_version": "1.1.0",
        "families": [],
        "categories": [],
        "issues": [],
        "issue_count": 0,
        "errors": [],
    }
    merged_once = merge_catalog_supplement(base)
    merged_twice = merge_catalog_supplement(merged_once)

    assert merged_once["issue_count"] == len(SUPPLEMENT_ISSUES)
    assert merged_twice["issue_count"] == len(SUPPLEMENT_ISSUES)


def test_find_supplement_issue_via_service() -> None:
    service = FieldReportCatalogService()
    issue = service.find_issue("QC-FIN-001")
    assert issue is not None
    assert issue["issue_id"] == "QC-FIN-001"
    assert issue["category_name_he"] == "טיח וצבע"
