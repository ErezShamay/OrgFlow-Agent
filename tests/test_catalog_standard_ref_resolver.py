"""Roadmap 6.5 - catalog standard_ref resolver."""

from __future__ import annotations

from app.services.catalog_standard_ref_resolver import (
    enrich_issue_standard_ref,
    resolve_catalog_link_for_issue,
)
from app.services.field_report_catalog_service import FieldReportCatalogService


class FakeCatalogService(FieldReportCatalogService):
    def find_issue(self, issue_id: str) -> dict | None:
        normalized = issue_id.strip().upper()
        if normalized == "QC-MEP-001":
            return {
                "issue_id": "QC-MEP-001",
                "issue_name_he": "בדיקת לחץ לא בוצעה",
                "top_family": "MECHANICAL_ELECTRICAL_SYSTEMS",
                "category_id": "PLUMBING",
                "category_name_he": "אינסטלציה",
                "standard_ref": 'ת"י 1205',
                "category_standard_id": 'ת"י 1205',
            }
        return None


def test_resolve_catalog_link_for_issue() -> None:
    link = resolve_catalog_link_for_issue(
        catalog_issue_id="QC-MEP-001",
        catalog_service=FakeCatalogService(),
    )

    assert link is not None
    assert link.issue_name_he == "בדיקת לחץ לא בוצעה"
    assert link.category_name_he == "אינסטלציה"
    assert '1205' in (link.standard_ref or "")


def test_enrich_issue_standard_ref_fills_missing_value() -> None:
    enriched = enrich_issue_standard_ref(
        {
            "catalog_issue_id": "QC-MEP-001",
            "standard_ref": None,
        },
        catalog_service=FakeCatalogService(),
    )

    assert enriched["standard_ref"] == 'ת"י 1205'


def test_enrich_issue_standard_ref_keeps_existing_value() -> None:
    enriched = enrich_issue_standard_ref(
        {
            "catalog_issue_id": "QC-MEP-001",
            "standard_ref": 'ת"י 9999',
        },
        catalog_service=FakeCatalogService(),
    )

    assert enriched["standard_ref"] == 'ת"י 9999'
