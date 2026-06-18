from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from postgrest.exceptions import APIError

from app.db.supabase_client import supabase
from app.repositories.postgrest_errors import is_missing_table_error
from app.schemas.quality_issue import (
    DEFAULT_ISSUE_VISIBILITY,
    DEFAULT_QUALITY_ISSUE_STATUS,
    QualityIssueCreateRequest,
    QualityIssueListQuery,
    QualityIssueStatus,
    resolve_tenant_view_status_he,
)

QUALITY_ISSUES_MIGRATION = (
    "db/migrations/2026060912_quality_issues.sql"
)
QUALITY_ISSUE_EVENTS_MIGRATION = (
    "db/migrations/2026060913_quality_issue_events.sql"
)
QUALITY_ISSUE_TENANT_VIEW_MIGRATION = (
    "db/migrations/2026061803_quality_issues_tenant_view_status_he.sql"
)

OPEN_ISSUE_STATUSES: frozenset[str] = frozenset(
    status.value
    for status in QualityIssueStatus
    if status != QualityIssueStatus.CLOSED
)

NULLABLE_ISSUE_UPDATE_FIELDS: frozenset[str] = frozenset(
    {
        "description",
        "location",
        "trade",
        "group_key",
        "group_label_he",
        "standard_ref",
        "catalog_issue_id",
        "catalog_reference_id",
        "first_seen_line_id",
        "last_seen_report_id",
        "last_seen_line_id",
        "last_seen_at",
        "closed_at",
        "closed_by",
        "tenant_view_status_he",
    }
)


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _enum_values(values: list[Any] | None) -> list[str] | None:
    if not values:
        return None
    return [str(value.value if hasattr(value, "value") else value) for value in values]


def matches_issue_list_filters(
    record: dict[str, Any],
    *,
    statuses: list[str] | None = None,
    severities: list[str] | None = None,
    trade: str | None = None,
    search: str | None = None,
) -> bool:
    if statuses and record.get("status") not in statuses:
        return False

    if severities and record.get("severity") not in severities:
        return False

    normalized_trade = (trade or "").strip()
    if normalized_trade and (record.get("trade") or "").strip() != normalized_trade:
        return False

    normalized_search = (search or "").strip().lower()
    if normalized_search:
        haystacks = (
            str(record.get("title") or ""),
            str(record.get("description") or ""),
            str(record.get("location") or ""),
        )
        if not any(normalized_search in value.lower() for value in haystacks):
            return False

    return True


class QualityIssueRepository:
    TABLE = "quality_issues"

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

    def create(
        self,
        *,
        organization_id: str,
        project_id: str,
        request: QualityIssueCreateRequest,
        status: str | None = None,
    ) -> dict:
        if not self.is_storage_available():
            raise RuntimeError(
                f"Table {self.TABLE} is not available. "
                f"Apply {QUALITY_ISSUES_MIGRATION}"
            )

        now = _utc_now_iso()
        payload = request.model_dump(mode="json", exclude_none=True)
        status_value = status or DEFAULT_QUALITY_ISSUE_STATUS.value
        payload.update(
            {
                "organization_id": organization_id,
                "project_id": project_id,
                "status": status_value,
                "tenant_view_status_he": resolve_tenant_view_status_he(
                    status_value
                ),
                "visibility": payload.get(
                    "visibility",
                    DEFAULT_ISSUE_VISIBILITY.value,
                ),
                "recurrence_count": 0,
                "created_at": now,
                "updated_at": now,
            }
        )

        response = (
            self.client
            .table(self.TABLE)
            .insert(payload)
            .execute()
        )
        return response.data[0]

    def get_by_id(
        self,
        issue_id: str,
    ) -> dict | None:
        if not self.is_storage_available():
            return None

        response = (
            self.client
            .table(self.TABLE)
            .select("*")
            .eq("id", issue_id)
            .limit(1)
            .execute()
        )
        if not response.data:
            return None
        return response.data[0]

    def get_for_organization(
        self,
        *,
        issue_id: str,
        organization_id: str,
    ) -> dict | None:
        record = self.get_by_id(issue_id)
        if record is None:
            return None
        if record.get("organization_id") != organization_id:
            return None
        return record

    def get_by_materialization_key(
        self,
        *,
        organization_id: str,
        materialization_key: str,
    ) -> dict | None:
        if not self.is_storage_available():
            return None

        response = (
            self.client
            .table(self.TABLE)
            .select("*")
            .eq("organization_id", organization_id)
            .eq("materialization_key", materialization_key)
            .limit(1)
            .execute()
        )
        if not response.data:
            return None
        return response.data[0]

    def update(
        self,
        issue_id: str,
        payload: dict[str, Any],
    ) -> dict | None:
        if not self.is_storage_available():
            raise RuntimeError(
                f"Table {self.TABLE} is not available. "
                f"Apply {QUALITY_ISSUES_MIGRATION}"
            )

        update_payload = {
            key: value
            for key, value in payload.items()
            if value is not None
            or key in NULLABLE_ISSUE_UPDATE_FIELDS
        }
        update_payload["updated_at"] = _utc_now_iso()

        response = (
            self.client
            .table(self.TABLE)
            .update(update_payload)
            .eq("id", issue_id)
            .execute()
        )
        if not response.data:
            return None
        return response.data[0]

    def _apply_list_filters(
        self,
        query: Any,
        *,
        statuses: list[str] | None = None,
        severities: list[str] | None = None,
        trade: str | None = None,
        search: str | None = None,
    ) -> Any:
        if statuses:
            query = query.in_("status", statuses)

        if severities:
            query = query.in_("severity", severities)

        normalized_trade = (trade or "").strip()
        if normalized_trade:
            query = query.eq("trade", normalized_trade)

        normalized_search = (search or "").strip()
        if normalized_search:
            pattern = f"%{normalized_search}%"
            query = query.or_(
                f"title.ilike.{pattern},description.ilike.{pattern},location.ilike.{pattern}"
            )

        return query

    def list_by_project(
        self,
        *,
        organization_id: str,
        project_id: str,
        query: QualityIssueListQuery | None = None,
    ) -> list[dict]:
        if not self.is_storage_available():
            return []

        filters = query or QualityIssueListQuery()
        request = (
            self.client
            .table(self.TABLE)
            .select("*")
            .eq("organization_id", organization_id)
            .eq("project_id", project_id)
            .order("updated_at", desc=True)
        )
        request = self._apply_list_filters(
            request,
            statuses=_enum_values(filters.status),
            severities=_enum_values(filters.severity),
            trade=filters.trade,
            search=filters.search,
        )
        request = request.range(
            filters.offset,
            filters.offset + filters.limit - 1,
        )

        response = request.execute()
        return response.data or []

    def count_by_project(
        self,
        *,
        organization_id: str,
        project_id: str,
        query: QualityIssueListQuery | None = None,
    ) -> int:
        if not self.is_storage_available():
            return 0

        filters = query or QualityIssueListQuery()
        request = (
            self.client
            .table(self.TABLE)
            .select("id", count="exact")
            .eq("organization_id", organization_id)
            .eq("project_id", project_id)
        )
        request = self._apply_list_filters(
            request,
            statuses=_enum_values(filters.status),
            severities=_enum_values(filters.severity),
            trade=filters.trade,
            search=filters.search,
        )

        response = request.execute()
        return int(response.count or 0)

    def list_by_organization(
        self,
        *,
        organization_id: str,
        query: QualityIssueListQuery | None = None,
    ) -> list[dict]:
        if not self.is_storage_available():
            return []

        filters = query or QualityIssueListQuery()
        request = (
            self.client
            .table(self.TABLE)
            .select("*")
            .eq("organization_id", organization_id)
            .order("updated_at", desc=True)
        )
        request = self._apply_list_filters(
            request,
            statuses=_enum_values(filters.status),
            severities=_enum_values(filters.severity),
            trade=filters.trade,
            search=filters.search,
        )
        request = request.range(
            filters.offset,
            filters.offset + filters.limit - 1,
        )

        response = request.execute()
        return response.data or []

    def count_by_organization(
        self,
        *,
        organization_id: str,
        query: QualityIssueListQuery | None = None,
    ) -> int:
        if not self.is_storage_available():
            return 0

        filters = query or QualityIssueListQuery()
        request = (
            self.client
            .table(self.TABLE)
            .select("id", count="exact")
            .eq("organization_id", organization_id)
        )
        request = self._apply_list_filters(
            request,
            statuses=_enum_values(filters.status),
            severities=_enum_values(filters.severity),
            trade=filters.trade,
            search=filters.search,
        )

        response = request.execute()
        return int(response.count or 0)

    def list_open_by_project(
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
            .select("*")
            .eq("organization_id", organization_id)
            .eq("project_id", project_id)
            .in_("status", sorted(OPEN_ISSUE_STATUSES))
            .order("severity", desc=True)
            .order("updated_at", desc=True)
            .execute()
        )
        return response.data or []


class QualityIssueEventRepository:
    TABLE = "quality_issue_events"

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

    def create(
        self,
        *,
        issue_id: str,
        event_type: str,
        payload: dict[str, Any] | None = None,
        report_id: str | None = None,
        line_id: str | None = None,
        actor_id: str | None = None,
    ) -> dict:
        if not self.is_storage_available():
            raise RuntimeError(
                f"Table {self.TABLE} is not available. "
                f"Apply {QUALITY_ISSUE_EVENTS_MIGRATION}"
            )

        row = {
            "issue_id": issue_id,
            "event_type": event_type,
            "payload": payload or {},
            "report_id": report_id,
            "line_id": line_id,
            "actor_id": actor_id,
            "created_at": _utc_now_iso(),
        }

        response = (
            self.client
            .table(self.TABLE)
            .insert(row)
            .execute()
        )
        return response.data[0]

    def list_by_issue_id(
        self,
        issue_id: str,
    ) -> list[dict]:
        if not self.is_storage_available():
            return []

        response = (
            self.client
            .table(self.TABLE)
            .select("*")
            .eq("issue_id", issue_id)
            .order("created_at", desc=False)
            .execute()
        )
        return response.data or []

    def list_by_report_id(
        self,
        report_id: str,
    ) -> list[dict]:
        if not self.is_storage_available():
            return []

        response = (
            self.client
            .table(self.TABLE)
            .select("*")
            .eq("report_id", report_id)
            .order("created_at", desc=False)
            .execute()
        )
        return response.data or []
