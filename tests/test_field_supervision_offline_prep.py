from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.services.field_supervision_offline_bundle import (
    build_apartments_by_project,
    build_supervision_catalog,
    public_areas_for_offline_bundle,
)
from app.services.field_visit_report_service import FieldVisitReportService


def test_build_supervision_catalog_filters_scope_issues() -> None:
    catalog = build_supervision_catalog(
        {
            "catalog_version": "1.4.0-supervision-checklist",
            "issues": [
                {
                    "issue_id": "SUP-FIN-004",
                    "issue_name_he": "פוגות",
                    "standard_ref": 'ת"י 1555',
                    "top_family": "FINISHING_WORKS",
                    "category_id": "TILING",
                    "category_name_he": "ריצוף",
                    "scope": "APARTMENT",
                    "allowed_stages": ["FINISHING"],
                },
                {
                    "issue_id": "LEGACY-001",
                    "issue_name_he": "ישן",
                    "standard_ref": "X",
                    "top_family": "FINISHING_WORKS",
                    "category_id": "TILING",
                    "category_name_he": "ריצוף",
                },
            ],
        }
    )

    assert catalog["issue_count"] == 1
    assert catalog["issues"][0]["issue_id"] == "SUP-FIN-004"
    assert catalog["issues"][0]["scope"] == "APARTMENT"


def test_build_apartments_by_project_groups_by_project_id() -> None:
    repository = MagicMock()
    repository.is_storage_available.return_value = True
    repository.list_by_project.side_effect = lambda project_id: {
        "project-a": [
            {
                "id": "apt-1",
                "organization_id": "org-1",
                "project_id": "project-a",
                "apartment_number": "12",
                "group_key": "apartment:12",
                "owner_name": "Owner A",
                "invite_status": "none",
            }
        ],
        "project-b": [],
    }.get(project_id, [])

    apartments = build_apartments_by_project(
        organization_id="org-1",
        project_ids=["project-a", "project-b"],
        apartment_repository=repository,
    )

    assert list(apartments.keys()) == ["project-a"]
    assert apartments["project-a"][0]["apartment_number"] == "12"


def test_public_areas_for_offline_bundle_matches_spec() -> None:
    areas = public_areas_for_offline_bundle()

    assert len(areas) == 6
    assert areas[0]["id"] == "LOBBY"


def test_build_offline_prep_bundle_includes_supervision_fields(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    report_repository = MagicMock()
    report_repository.is_storage_available.return_value = True
    report_repository.list_by_organization.return_value = []

    project_repository = MagicMock()
    project_repository.get_projects_by_organization.return_value = [
        {"id": "project-1", "project_name": "Tower"},
    ]

    apartment_repository = MagicMock()
    apartment_repository.is_storage_available.return_value = True
    apartment_repository.list_by_project.return_value = [
        {
            "id": "apt-1",
            "organization_id": "org-1",
            "project_id": "project-1",
            "apartment_number": "3",
            "group_key": "apartment:3",
            "owner_name": "Owner",
            "invite_status": "none",
        }
    ]

    catalog_service = MagicMock()
    catalog_service.get_full_catalog.return_value = {
        "catalog_version": "1.4.0-supervision-checklist",
        "issues": [
            {
                "issue_id": "SUP-FIN-004",
                "issue_name_he": "פוגות",
                "standard_ref": 'ת"י 1555',
                "top_family": "FINISHING_WORKS",
                "category_id": "TILING",
                "category_name_he": "ריצוף",
                "scope": "APARTMENT",
                "allowed_stages": ["FINISHING"],
            }
        ],
    }

    organization_profile_service = MagicMock()
    organization_profile_service.get_profile.return_value = {}

    service = FieldVisitReportService(
        report_repository=report_repository,
        project_repository=project_repository,
        apartment_repository=apartment_repository,
        organization_profile_service=organization_profile_service,
        catalog_service=catalog_service,
    )
    monkeypatch.setattr(service, "are_lines_available", lambda: True)

    bundle = service.build_offline_prep_bundle("org-1")

    assert bundle["supervision_catalog"]["issue_count"] == 1
    assert bundle["public_areas"]
    assert bundle["apartments_by_project"]["project-1"][0]["apartment_number"] == "3"
