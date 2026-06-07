from __future__ import annotations

from datetime import UTC, datetime

from postgrest.exceptions import APIError

from app.db.supabase_client import supabase
from app.repositories.postgrest_errors import (
    is_missing_table_error,
)


class FieldVisitReportRepository:
    TABLE = "field_visit_reports"
    STATUS_IN_PROGRESS = "IN_PROGRESS"
    LIST_HIDDEN_STATUSES = frozenset({"LOCKED"})

    def __init__(self) -> None:
        self.client = supabase
        self._table_available: bool | None = None

    def is_storage_available(self) -> bool:
        if self._table_available is not None:
            return self._table_available

        try:
            (
                self.client
                .table(self.TABLE)
                .select("id")
                .limit(1)
                .execute()
            )
            self._table_available = True
        except APIError as error:
            if is_missing_table_error(error, self.TABLE):
                self._table_available = False
            else:
                raise

        return self._table_available

    def list_by_organization(
        self,
        organization_id: str,
        *,
        status: str | None = None,
        include_hidden: bool = False,
    ) -> list[dict]:
        if not self.is_storage_available():
            return []

        query = (
            self.client
            .table(self.TABLE)
            .select("*")
            .eq("organization_id", organization_id)
            .order("updated_at", desc=True)
        )

        if status:
            query = query.eq("status", status)
        elif not include_hidden:
            for hidden_status in self.LIST_HIDDEN_STATUSES:
                query = query.neq("status", hidden_status)

        response = query.execute()
        return response.data or []

    def get_by_id(
        self,
        report_id: str,
    ) -> dict | None:
        if not self.is_storage_available():
            return None

        response = (
            self.client
            .table(self.TABLE)
            .select("*")
            .eq("id", report_id)
            .limit(1)
            .execute()
        )

        if not response.data:
            return None

        return response.data[0]

    def get_by_client_report_uuid(
        self,
        client_report_uuid: str,
    ) -> dict | None:
        if not self.is_storage_available() or not client_report_uuid:
            return None

        response = (
            self.client
            .table(self.TABLE)
            .select("*")
            .eq("client_report_uuid", client_report_uuid)
            .limit(1)
            .execute()
        )

        if not response.data:
            return None

        return response.data[0]

    def list_archived_by_project(
        self,
        *,
        organization_id: str,
        project_id: str,
    ) -> list[dict]:
        if not self.is_storage_available():
            return []

        response = (
            self.client
            .table(self.TABLE)
            .select(
                "id, project_id, visit_date, visit_type, status, "
                "pdf_storage_path, pdf_filename, locked_at, closed_at"
            )
            .eq("organization_id", organization_id)
            .eq("project_id", project_id)
            .eq("status", "LOCKED")
            .not_.is_("pdf_storage_path", "null")
            .order("visit_date", desc=True)
            .execute()
        )

        return response.data or []

    def get_open_for_project(
        self,
        *,
        organization_id: str,
        project_id: str,
    ) -> dict | None:
        if not self.is_storage_available():
            return None

        response = (
            self.client
            .table(self.TABLE)
            .select("*")
            .eq("organization_id", organization_id)
            .eq("project_id", project_id)
            .eq("status", self.STATUS_IN_PROGRESS)
            .limit(1)
            .execute()
        )

        if not response.data:
            return None

        return response.data[0]

    def create(
        self,
        *,
        organization_id: str,
        project_id: str,
        created_by_profile_id: str,
        visit_type: str,
        visit_date: str,
        header_fields: dict | None = None,
        catalog_version: str | None = None,
        organization_profile_snapshot: dict | None = None,
        client_report_uuid: str | None = None,
    ) -> dict:
        if not self.is_storage_available():
            raise RuntimeError(
                f"Table {self.TABLE} is not available. "
                "Apply db/migrations/2026060102_field_visit_reports.sql"
            )

        now = datetime.now(UTC).isoformat()
        payload = {
            "organization_id": organization_id,
            "project_id": project_id,
            "created_by_profile_id": created_by_profile_id,
            "visit_type": visit_type,
            "visit_date": visit_date,
            "status": self.STATUS_IN_PROGRESS,
            "header_fields": header_fields or {},
            "catalog_version": catalog_version,
            "organization_profile_snapshot": (
                organization_profile_snapshot
            ),
            "created_at": now,
            "updated_at": now,
        }

        if client_report_uuid:
            payload["client_report_uuid"] = client_report_uuid

        response = (
            self.client
            .table(self.TABLE)
            .insert(payload)
            .execute()
        )

        return response.data[0]

    def update(
        self,
        report_id: str,
        payload: dict,
    ) -> dict | None:
        if not self.is_storage_available():
            raise RuntimeError(
                f"Table {self.TABLE} is not available. "
                "Apply db/migrations/2026060102_field_visit_reports.sql"
            )

        payload["updated_at"] = datetime.now(UTC).isoformat()

        response = (
            self.client
            .table(self.TABLE)
            .update(payload)
            .eq("id", report_id)
            .execute()
        )

        if not response.data:
            return None

        return response.data[0]
