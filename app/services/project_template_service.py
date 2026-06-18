from __future__ import annotations

from app.exceptions.exceptions import NotFoundError
from app.repositories.project_template_repository import (
    ProjectTemplateRepository,
)
from app.schemas.project_template import (
    ProjectTemplate,
    ProjectTemplateResolveResponse,
)


def _template_priority(
    record: dict,
    *,
    organization_id: str | None,
) -> tuple[int, str]:
    record_org = record.get("organization_id")
    if organization_id and record_org == organization_id:
        return (0, "organization")
    if record_org is None:
        return (1, "global")
    return (2, "other")


class ProjectTemplateService:
    def __init__(
        self,
        *,
        repository: ProjectTemplateRepository | None = None,
    ) -> None:
        self.repository = repository or ProjectTemplateRepository()

    def list_active_for_scheme(
        self,
        scheme: str,
        *,
        organization_id: str | None = None,
    ) -> list[ProjectTemplate]:
        records = self.repository.list_active_for_scheme(
            scheme,
            organization_id=organization_id,
        )
        templates = [ProjectTemplate.from_record(record) for record in records]
        templates.sort(
            key=lambda item: _template_priority(
                item.model_dump(),
                organization_id=organization_id,
            )
        )
        return templates

    def resolve_for_scheme(
        self,
        scheme: str,
        *,
        organization_id: str | None = None,
    ) -> ProjectTemplateResolveResponse:
        records = self.repository.list_active_for_scheme(
            scheme,
            organization_id=organization_id,
        )

        if not records:
            raise NotFoundError(
                f"No active project template for scheme {scheme}"
            )

        records.sort(
            key=lambda record: _template_priority(
                record,
                organization_id=organization_id,
            )
        )
        best = records[0]
        _, source = _template_priority(
            best,
            organization_id=organization_id,
        )
        if source == "other":
            source = "seed"

        return ProjectTemplateResolveResponse(
            template=ProjectTemplate.from_record(best),
            source=source,
        )

    def get_by_id(self, template_id: str) -> ProjectTemplate:
        record = self.repository.get_by_id(template_id)
        if not record:
            raise NotFoundError(f"Project template {template_id} not found")
        return ProjectTemplate.from_record(record)
