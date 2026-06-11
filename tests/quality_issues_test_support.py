from __future__ import annotations

from datetime import UTC, datetime

from app.repositories.quality_issue_repository import (
    NULLABLE_ISSUE_UPDATE_FIELDS,
    OPEN_ISSUE_STATUSES,
    matches_issue_list_filters,
)
from app.schemas.quality_issue import (
    QualityIssueCreateRequest,
    QualityIssueListQuery,
    QualityIssueStatus,
)


def qc_now() -> datetime:
    return datetime(2026, 6, 9, 12, 0, tzinfo=UTC)


def qc_now_iso() -> str:
    return qc_now().isoformat()


def qc_create_request(**overrides: object) -> QualityIssueCreateRequest:
    base = {
        "title": "נזילה",
        "first_seen_report_id": "report-1",
        "first_seen_at": qc_now(),
        "materialization_key": "report-1:line-1",
    }
    base.update(overrides)
    return QualityIssueCreateRequest(**base)


def qc_issue_payload(**overrides: object) -> dict:
    base = {
        "title": "נזילה",
        "first_seen_report_id": "report-1",
        "first_seen_at": qc_now_iso(),
        "materialization_key": "report-1:line-1",
    }
    base.update(overrides)
    return base


class InMemoryQualityIssueRepository:
    """Test double mirroring repository list/filter semantics."""

    def __init__(self) -> None:
        self.records: dict[str, dict] = {}
        self._counter = 0

    def is_storage_available(self) -> bool:
        return True

    def create(
        self,
        *,
        organization_id: str,
        project_id: str,
        request: QualityIssueCreateRequest,
        status: str | None = None,
    ) -> dict:
        self._counter += 1
        issue_id = f"issue-{self._counter}"
        payload = request.model_dump(mode="json", exclude_none=True)
        record = {
            "id": issue_id,
            "organization_id": organization_id,
            "project_id": project_id,
            "status": status or QualityIssueStatus.OPEN.value,
            "recurrence_count": 0,
            **payload,
        }
        self.records[issue_id] = record
        return record

    def get_by_id(self, issue_id: str) -> dict | None:
        return self.records.get(issue_id)

    def get_for_organization(
        self,
        *,
        issue_id: str,
        organization_id: str,
    ) -> dict | None:
        record = self.get_by_id(issue_id)
        if record is None or record.get("organization_id") != organization_id:
            return None
        return record

    def get_by_materialization_key(
        self,
        *,
        organization_id: str,
        materialization_key: str,
    ) -> dict | None:
        for record in self.records.values():
            if (
                record.get("organization_id") == organization_id
                and record.get("materialization_key") == materialization_key
            ):
                return record
        return None

    def update(self, issue_id: str, payload: dict) -> dict | None:
        record = self.records.get(issue_id)
        if record is None:
            return None
        record.update(
            {
                key: value
                for key, value in payload.items()
                if value is not None
                or key in NULLABLE_ISSUE_UPDATE_FIELDS
            }
        )
        self.records[issue_id] = record
        return record

    def list_by_project(
        self,
        *,
        organization_id: str,
        project_id: str,
        query: QualityIssueListQuery | None = None,
    ) -> list[dict]:
        filters = query or QualityIssueListQuery()
        statuses = [status.value for status in filters.status] if filters.status else None
        severities = (
            [severity.value for severity in filters.severity]
            if filters.severity
            else None
        )

        records = [
            record
            for record in self.records.values()
            if record.get("organization_id") == organization_id
            and record.get("project_id") == project_id
            and matches_issue_list_filters(
                record,
                statuses=statuses,
                severities=severities,
                trade=filters.trade,
                search=filters.search,
            )
        ]
        records.sort(key=lambda item: item.get("updated_at", ""), reverse=True)
        start = filters.offset
        end = start + filters.limit
        return records[start:end]

    def count_by_project(
        self,
        *,
        organization_id: str,
        project_id: str,
        query: QualityIssueListQuery | None = None,
    ) -> int:
        filters = query or QualityIssueListQuery()
        statuses = [status.value for status in filters.status] if filters.status else None
        severities = (
            [severity.value for severity in filters.severity]
            if filters.severity
            else None
        )
        return sum(
            1
            for record in self.records.values()
            if record.get("organization_id") == organization_id
            and record.get("project_id") == project_id
            and matches_issue_list_filters(
                record,
                statuses=statuses,
                severities=severities,
                trade=filters.trade,
                search=filters.search,
            )
        )

    def list_by_organization(
        self,
        *,
        organization_id: str,
        query: QualityIssueListQuery | None = None,
    ) -> list[dict]:
        filters = query or QualityIssueListQuery()
        statuses = [status.value for status in filters.status] if filters.status else None
        severities = (
            [severity.value for severity in filters.severity]
            if filters.severity
            else None
        )

        records = [
            record
            for record in self.records.values()
            if record.get("organization_id") == organization_id
            and matches_issue_list_filters(
                record,
                statuses=statuses,
                severities=severities,
                trade=filters.trade,
                search=filters.search,
            )
        ]
        records.sort(key=lambda item: item.get("updated_at", ""), reverse=True)
        start = filters.offset
        end = start + filters.limit
        return records[start:end]

    def count_by_organization(
        self,
        *,
        organization_id: str,
        query: QualityIssueListQuery | None = None,
    ) -> int:
        filters = query or QualityIssueListQuery()
        statuses = [status.value for status in filters.status] if filters.status else None
        severities = (
            [severity.value for severity in filters.severity]
            if filters.severity
            else None
        )
        return sum(
            1
            for record in self.records.values()
            if record.get("organization_id") == organization_id
            and matches_issue_list_filters(
                record,
                statuses=statuses,
                severities=severities,
                trade=filters.trade,
                search=filters.search,
            )
        )

    def list_open_by_project(
        self,
        *,
        organization_id: str,
        project_id: str,
    ) -> list[dict]:
        return [
            record
            for record in self.records.values()
            if record.get("organization_id") == organization_id
            and record.get("project_id") == project_id
            and record.get("status") in OPEN_ISSUE_STATUSES
        ]


class InMemoryQualityIssueEventRepository:
    def __init__(self) -> None:
        self.records: dict[str, dict] = {}
        self._counter = 0

    def is_storage_available(self) -> bool:
        return True

    def create(
        self,
        *,
        issue_id: str,
        event_type: str,
        payload: dict | None = None,
        report_id: str | None = None,
        line_id: str | None = None,
        actor_id: str | None = None,
    ) -> dict:
        self._counter += 1
        event_id = f"event-{self._counter}"
        record = {
            "id": event_id,
            "issue_id": issue_id,
            "event_type": event_type,
            "payload": payload or {},
            "report_id": report_id,
            "line_id": line_id,
            "actor_id": actor_id,
        }
        self.records[event_id] = record
        return record

    def list_by_issue_id(self, issue_id: str) -> list[dict]:
        return [
            record
            for record in self.records.values()
            if record.get("issue_id") == issue_id
        ]

    def list_by_report_id(self, report_id: str) -> list[dict]:
        return [
            record
            for record in self.records.values()
            if record.get("report_id") == report_id
        ]


class FakeFieldVisitReportRepository:
    def __init__(self, reports: dict[str, dict] | None = None) -> None:
        self.reports = reports or {
            "report-1": {
                "id": "report-1",
                "organization_id": "org-1",
                "project_id": "proj-1",
                "status": "CLOSED",
            },
            "report-2": {
                "id": "report-2",
                "organization_id": "org-1",
                "project_id": "proj-1",
                "status": "CLOSED",
            },
            "report-other": {
                "id": "report-other",
                "organization_id": "org-1",
                "project_id": "proj-2",
                "status": "CLOSED",
            },
        }

    def is_storage_available(self) -> bool:
        return True

    def get_by_id(self, report_id: str) -> dict | None:
        return self.reports.get(report_id)


class FakeProjectRepository:
    def __init__(self, projects: dict[str, dict] | None = None) -> None:
        self.projects = projects or {
            "proj-1": {
                "id": "proj-1",
                "organization_id": "org-1",
                "project_name": "האורנים 7",
            },
            "proj-2": {
                "id": "proj-2",
                "organization_id": "org-1",
                "project_name": "פרויקט ב",
            },
        }

    def get_project_by_id(self, project_id: str) -> dict | None:
        return self.projects.get(project_id)

    def get_projects_by_organization(
        self,
        organization_id: str,
    ) -> list[dict]:
        return [
            project
            for project in self.projects.values()
            if project.get("organization_id") == organization_id
        ]


class InMemoryQualityIssuePhotoRepository:
    def __init__(self) -> None:
        self.records: dict[str, dict] = {}

    def is_storage_available(self) -> bool:
        return True

    def list_by_issue(self, issue_id: str) -> list[dict]:
        return [
            record
            for record in self.records.values()
            if record.get("issue_id") == issue_id
        ]

    def get_by_id(self, photo_id: str) -> dict | None:
        return self.records.get(photo_id)

    def get_for_issue(
        self,
        *,
        issue_id: str,
        photo_id: str,
        organization_id: str,
    ) -> dict | None:
        photo = self.records.get(photo_id)
        if photo is None:
            return None
        if photo.get("issue_id") != issue_id:
            return None
        if photo.get("organization_id") != organization_id:
            return None
        return photo

    def next_sort_order(self, issue_id: str) -> int:
        photos = self.list_by_issue(issue_id)
        if not photos:
            return 0
        return max(int(photo.get("sort_order") or 0) for photo in photos) + 1

    def create(self, payload: dict) -> dict:
        photo_id = str(payload["id"])
        self.records[photo_id] = dict(payload)
        return self.records[photo_id]
