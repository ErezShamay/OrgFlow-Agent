"""Resolve catalog section metadata for quality issues - roadmap 6.5."""

from __future__ import annotations

from typing import Any

from app.schemas.quality_issue import QualityIssueCatalogLink
from app.services.field_report_catalog_service import FieldReportCatalogService


def resolve_catalog_link_for_issue(
    *,
    catalog_issue_id: str | None,
    catalog_service: FieldReportCatalogService | None = None,
) -> QualityIssueCatalogLink | None:
    normalized = (catalog_issue_id or "").strip().upper()
    if not normalized:
        return None

    service = catalog_service or FieldReportCatalogService()
    catalog_issue = service.find_issue(normalized)
    if catalog_issue is None:
        return None

    standard_ref = (
        catalog_issue.get("standard_ref")
        or catalog_issue.get("category_standard_id")
    )

    return QualityIssueCatalogLink(
        issue_id=normalized,
        issue_name_he=str(catalog_issue.get("issue_name_he") or ""),
        top_family=str(catalog_issue.get("top_family") or ""),
        category_id=str(catalog_issue.get("category_id") or ""),
        category_name_he=str(catalog_issue.get("category_name_he") or ""),
        standard_ref=standard_ref,
        category_standard_id=catalog_issue.get("category_standard_id"),
    )


def enrich_issue_standard_ref(
    issue: dict[str, Any],
    *,
    catalog_service: FieldReportCatalogService | None = None,
) -> dict[str, Any]:
    """Fill missing standard_ref from catalog when catalog_issue_id is set."""
    if (issue.get("standard_ref") or "").strip():
        return issue

    catalog_link = resolve_catalog_link_for_issue(
        catalog_issue_id=issue.get("catalog_issue_id"),
        catalog_service=catalog_service,
    )
    if catalog_link is None or not catalog_link.standard_ref:
        return issue

    enriched = dict(issue)
    enriched["standard_ref"] = catalog_link.standard_ref
    return enriched
