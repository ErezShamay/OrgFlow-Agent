from __future__ import annotations

from typing import Any

from postgrest.exceptions import APIError

from app.config.project_template_seed import iter_seed_templates
from app.db.supabase_client import supabase
from app.repositories.postgrest_errors import is_missing_table_error

PROJECT_TEMPLATES_MIGRATION = (
    "db/migrations/2026061801_project_templates.sql"
)


def _normalize_record(record: dict[str, Any]) -> dict[str, Any]:
    public_area_ids = record.get("public_area_ids") or []
    if not isinstance(public_area_ids, list):
        public_area_ids = []

    return {
        **record,
        "public_area_ids": public_area_ids,
    }


def _seed_records_for_scheme(
    scheme: str,
    *,
    organization_id: str | None = None,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []

    for template in iter_seed_templates():
        if template.get("scheme") != scheme:
            continue
        if not template.get("is_active", True):
            continue

        template_org_id = template.get("organization_id")
        if organization_id:
            if template_org_id not in (None, organization_id):
                continue
        elif template_org_id is not None:
            continue

        records.append(_normalize_record(dict(template)))

    return records


class ProjectTemplateRepository:
    def __init__(self) -> None:
        self.client = supabase

    def list_active_for_scheme(
        self,
        scheme: str,
        *,
        organization_id: str | None = None,
    ) -> list[dict[str, Any]]:
        try:
            query = (
                self.client.table("project_templates")
                .select("*")
                .eq("scheme", scheme)
                .eq("is_active", True)
            )

            if organization_id:
                response = (
                    query.or_(
                        f"organization_id.is.null,"
                        f"organization_id.eq.{organization_id}"
                    ).execute()
                )
            else:
                response = (
                    query.is_("organization_id", "null").execute()
                )

            return [
                _normalize_record(record)
                for record in (response.data or [])
            ]

        except APIError as error:
            if is_missing_table_error(error, "project_templates"):
                return _seed_records_for_scheme(
                    scheme,
                    organization_id=organization_id,
                )
            raise

    def get_by_id(self, template_id: str) -> dict[str, Any] | None:
        try:
            response = (
                self.client.table("project_templates")
                .select("*")
                .eq("id", template_id)
                .limit(1)
                .execute()
            )
        except APIError as error:
            if is_missing_table_error(error, "project_templates"):
                for template in iter_seed_templates():
                    if str(template.get("id")) == template_id:
                        return _normalize_record(dict(template))
                return None
            raise

        if not response.data:
            for template in iter_seed_templates():
                if str(template.get("id")) == template_id:
                    return _normalize_record(dict(template))
            return None

        return _normalize_record(response.data[0])
