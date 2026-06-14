from __future__ import annotations

from app.config.field_supervision_public_areas import PUBLIC_AREA_DEFINITIONS
from app.repositories.project_apartment_repository import (
    ProjectApartmentRepository,
)
from app.schemas.project_apartment import ProjectApartmentRecord

SUPERVISION_CATALOG_ISSUE_KEYS = (
    "issue_id",
    "issue_name_he",
    "standard_ref",
    "catalog_reference_id",
    "top_family",
    "category_id",
    "category_name_he",
    "severity",
    "description",
    "scope",
    "public_area_id",
    "allowed_stages",
)


def build_supervision_catalog(full_catalog: dict) -> dict:
    """Extract supervision checklist issues (scope + allowed_stages) from full catalog."""
    issues: list[dict] = []

    for raw_issue in full_catalog.get("issues") or []:
        if not isinstance(raw_issue, dict):
            continue

        scope = raw_issue.get("scope")
        allowed_stages = raw_issue.get("allowed_stages")
        if not scope or not allowed_stages:
            continue

        issue = {
            key: raw_issue.get(key)
            for key in SUPERVISION_CATALOG_ISSUE_KEYS
            if key in raw_issue
        }
        issue["scope"] = str(scope)
        issue["allowed_stages"] = list(allowed_stages)
        issues.append(issue)

    return {
        "catalog_version": full_catalog.get("catalog_version"),
        "issues": issues,
        "issue_count": len(issues),
    }


def build_apartments_by_project(
    *,
    organization_id: str,
    project_ids: list[str],
    apartment_repository: ProjectApartmentRepository,
) -> dict[str, list[dict]]:
    if not apartment_repository.is_storage_available():
        return {}

    apartments_by_project: dict[str, list[dict]] = {}

    for project_id in project_ids:
        rows = apartment_repository.list_by_project(project_id)
        apartments = [
            ProjectApartmentRecord.model_validate(row).model_dump(mode="json")
            for row in rows
            if str(row.get("organization_id")) == organization_id
        ]
        if apartments:
            apartments_by_project[project_id] = apartments

    return apartments_by_project


def public_areas_for_offline_bundle() -> list[dict[str, str]]:
    return [dict(area) for area in PUBLIC_AREA_DEFINITIONS]
