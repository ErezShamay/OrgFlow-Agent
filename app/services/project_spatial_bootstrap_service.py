"""Z3 — auto-create apartments and register public areas on project create."""

from __future__ import annotations

from app.config.project_template_seed import DEFAULT_PUBLIC_AREA_IDS
from app.exceptions.exceptions import NotFoundError
from app.repositories.project_apartment_repository import (
    ProjectApartmentRepository,
)
from app.repositories.project_repository import ProjectRepository
from app.schemas.project_spatial_bootstrap import ProjectSpatialBootstrapResponse
from app.schemas.project_template import ProjectTemplate
from app.services.project_template_service import ProjectTemplateService

BOOTSTRAP_OWNER_PLACEHOLDER_HE = "דייר"


def build_stable_apartment_number(
    floor: int,
    unit_index: int,
    *,
    units_per_floor: int,
) -> str:
    """Stable numbering: floor 1 units 1..U → 1..U, floor 2 → U+1..2U, etc."""
    if floor < 1 or unit_index < 1:
        raise ValueError("floor and unit_index must be positive")
    return str((floor - 1) * units_per_floor + unit_index)


def build_apartment_bootstrap_rows(
    *,
    floors: int,
    units_per_floor: int,
    owner_name: str = BOOTSTRAP_OWNER_PLACEHOLDER_HE,
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for floor in range(1, floors + 1):
        for unit_index in range(1, units_per_floor + 1):
            rows.append(
                {
                    "apartment_number": build_stable_apartment_number(
                        floor,
                        unit_index,
                        units_per_floor=units_per_floor,
                    ),
                    "owner_name": owner_name,
                }
            )
    return rows


class ProjectSpatialBootstrapService:
    def __init__(
        self,
        *,
        template_service: ProjectTemplateService | None = None,
        apartment_repository: ProjectApartmentRepository | None = None,
        project_repository: ProjectRepository | None = None,
    ) -> None:
        self.template_service = template_service or ProjectTemplateService()
        self.apartment_repository = (
            apartment_repository or ProjectApartmentRepository()
        )
        self.project_repository = project_repository or ProjectRepository()

    def bootstrap(
        self,
        *,
        project_id: str,
        scheme: str,
        organization_id: str,
        floors: int | None = None,
        units_per_floor: int | None = None,
        housing_units_count: int | None = None,
        template_id: str | None = None,
    ) -> ProjectSpatialBootstrapResponse:
        existing = self.apartment_repository.list_by_project(project_id)
        if existing:
            public_areas = self._read_public_areas(project_id)
            return ProjectSpatialBootstrapResponse(
                apartments_created=0,
                public_areas=public_areas,
                skipped=True,
            )

        resolved_floors, resolved_units, public_areas = self._resolve_layout(
            scheme=scheme,
            organization_id=organization_id,
            template_id=template_id,
            floors=floors,
            units_per_floor=units_per_floor,
            housing_units_count=housing_units_count,
        )

        apartment_rows = build_apartment_bootstrap_rows(
            floors=resolved_floors,
            units_per_floor=resolved_units,
        )
        created = self.apartment_repository.bulk_create_apartments(
            organization_id=organization_id,
            project_id=project_id,
            apartments=apartment_rows,
        )
        self._persist_public_areas(project_id, public_areas)

        return ProjectSpatialBootstrapResponse(
            apartments_created=len(created),
            public_areas=public_areas,
            skipped=False,
            floors=resolved_floors,
            units_per_floor=resolved_units,
        )

    def _resolve_layout(
        self,
        *,
        scheme: str,
        organization_id: str,
        template_id: str | None,
        floors: int | None,
        units_per_floor: int | None,
        housing_units_count: int | None,
    ) -> tuple[int, int, list[str]]:
        template = self._load_template(
            scheme=scheme,
            organization_id=organization_id,
            template_id=template_id,
        )

        resolved_floors = floors
        if resolved_floors is None and template is not None:
            resolved_floors = template.default_floors
        if resolved_floors is None:
            resolved_floors = 1

        resolved_units = units_per_floor
        if resolved_units is None and template is not None:
            resolved_units = template.default_units_per_floor
        if (
            resolved_units is None
            and housing_units_count is not None
            and resolved_floors > 0
        ):
            resolved_units = max(1, housing_units_count // resolved_floors)
        if resolved_units is None:
            resolved_units = 1

        if template is not None and template.public_area_ids:
            public_areas = list(template.public_area_ids)
        else:
            public_areas = list(DEFAULT_PUBLIC_AREA_IDS)

        return resolved_floors, resolved_units, public_areas

    def _load_template(
        self,
        *,
        scheme: str,
        organization_id: str,
        template_id: str | None,
    ) -> ProjectTemplate | None:
        if template_id:
            try:
                return self.template_service.get_by_id(template_id)
            except NotFoundError:
                return None

        try:
            return self.template_service.resolve_for_scheme(
                scheme,
                organization_id=organization_id,
            ).template
        except NotFoundError:
            return None

    def _read_public_areas(self, project_id: str) -> list[str]:
        project = self.project_repository.get_project_by_id(project_id)
        if not project:
            return []

        stored = project.get("spatial_public_area_ids")
        if isinstance(stored, list):
            return [str(value) for value in stored if value]

        return []

    def _persist_public_areas(
        self,
        project_id: str,
        public_area_ids: list[str],
    ) -> None:
        if not public_area_ids:
            return

        self.project_repository.update_project(
            project_id,
            {"spatial_public_area_ids": public_area_ids},
        )
