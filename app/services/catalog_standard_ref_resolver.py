"""Resolve catalog section metadata for quality issues - roadmap 6.5 + L4 standards KB."""

from __future__ import annotations

from typing import Any

from app.schemas.quality_issue import QualityIssueCatalogLink
from app.services.field_report_catalog_service import FieldReportCatalogService
from app.services.standards_resolver_service import StandardsResolverService


def resolve_catalog_link_for_issue(
    *,
    catalog_issue_id: str | None,
    catalog_service: FieldReportCatalogService | None = None,
    standards_resolver: StandardsResolverService | None = None,
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
    resolver = standards_resolver or StandardsResolverService()
    standard = resolver.resolve_for_catalog_issue(catalog_issue)

    return QualityIssueCatalogLink(
        issue_id=normalized,
        issue_name_he=str(catalog_issue.get("issue_name_he") or ""),
        top_family=str(catalog_issue.get("top_family") or ""),
        category_id=str(catalog_issue.get("category_id") or ""),
        category_name_he=str(catalog_issue.get("category_name_he") or ""),
        standard_ref=standard_ref,
        category_standard_id=catalog_issue.get("category_standard_id"),
        standard_id=standard.standard_id if standard else catalog_issue.get("standard_id"),
    )


def enrich_issue_standard_ref(
    issue: dict[str, Any],
    *,
    catalog_service: FieldReportCatalogService | None = None,
    standards_resolver: StandardsResolverService | None = None,
) -> dict[str, Any]:
    """Fill missing standard_ref / standard_id from catalog and standards KB."""
    service = catalog_service or FieldReportCatalogService()
    resolver = standards_resolver or StandardsResolverService()
    enriched = dict(issue)

    catalog_issue = None
    catalog_issue_id = enriched.get("catalog_issue_id")
    if catalog_issue_id:
        catalog_issue = service.find_issue(str(catalog_issue_id))

    if not (enriched.get("standard_ref") or "").strip():
        catalog_link = resolve_catalog_link_for_issue(
            catalog_issue_id=str(catalog_issue_id or ""),
            catalog_service=service,
            standards_resolver=resolver,
        )
        if catalog_link is not None and catalog_link.standard_ref:
            enriched["standard_ref"] = catalog_link.standard_ref

    if not (enriched.get("standard_id") or "").strip():
        standard = resolver.resolve_for_issue(
            enriched,
            catalog_issue=catalog_issue,
        )
        if standard is not None:
            enriched["standard_id"] = standard.standard_id
            if not (enriched.get("standard_ref") or "").strip():
                enriched["standard_ref"] = standard.standard_ref or standard.title

    return enriched
