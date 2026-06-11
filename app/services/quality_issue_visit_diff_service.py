from __future__ import annotations

from typing import Any

from app.exceptions.exceptions import NotFoundError
from app.repositories.field_visit_report_repository import (
    FieldVisitReportRepository,
)
from app.repositories.project_repository import ProjectRepository
from app.repositories.quality_issue_repository import (
    OPEN_ISSUE_STATUSES,
    QualityIssueEventRepository,
    QualityIssueRepository,
)
from app.schemas.qc_permissions import (
    has_qc_permission,
    visible_issue_statuses_for_role,
)
from app.schemas.quality_issue import (
    QualityIssueEventType,
    QualityIssueVisitDiffCategory,
    QualityIssueVisitDiffEntry,
    QualityIssueVisitDiffResponse,
    parse_quality_issue_row,
)

_EVENT_CATEGORY_PRIORITY: dict[QualityIssueEventType, int] = {
    QualityIssueEventType.REOPENED: 0,
    QualityIssueEventType.VERIFIED_CLOSED: 1,
    QualityIssueEventType.DETECTED: 2,
    QualityIssueEventType.LINKED: 3,
}

_EVENT_TO_CATEGORY: dict[QualityIssueEventType, QualityIssueVisitDiffCategory] = {
    QualityIssueEventType.REOPENED: QualityIssueVisitDiffCategory.RECURRING,
    QualityIssueEventType.VERIFIED_CLOSED: QualityIssueVisitDiffCategory.CLOSED,
    QualityIssueEventType.DETECTED: QualityIssueVisitDiffCategory.NEW,
    QualityIssueEventType.LINKED: QualityIssueVisitDiffCategory.STILL_OPEN,
}


class QualityIssueVisitDiffService:
    def __init__(
        self,
        issue_repository: QualityIssueRepository | None = None,
        event_repository: QualityIssueEventRepository | None = None,
        report_repository: FieldVisitReportRepository | None = None,
        project_repository: ProjectRepository | None = None,
    ) -> None:
        self.issue_repository = (
            issue_repository or QualityIssueRepository()
        )
        self.event_repository = (
            event_repository or QualityIssueEventRepository()
        )
        self.report_repository = (
            report_repository or FieldVisitReportRepository()
        )
        self.project_repository = (
            project_repository or ProjectRepository()
        )

    def get_visit_issue_diff(
        self,
        *,
        organization_id: str,
        project_id: str,
        report_id: str,
        actor_role: str | None,
    ) -> QualityIssueVisitDiffResponse:
        self._require_read_permission(actor_role)
        self._ensure_project(organization_id, project_id)
        self._ensure_report(
            organization_id=organization_id,
            project_id=project_id,
            report_id=report_id,
        )

        buckets: dict[QualityIssueVisitDiffCategory, list[QualityIssueVisitDiffEntry]] = {
            QualityIssueVisitDiffCategory.NEW: [],
            QualityIssueVisitDiffCategory.CLOSED: [],
            QualityIssueVisitDiffCategory.STILL_OPEN: [],
            QualityIssueVisitDiffCategory.RECURRING: [],
        }

        for issue_id, line_id, category in self._classify_report_events(
            organization_id=organization_id,
            project_id=project_id,
            report_id=report_id,
        ):
            issue = self.issue_repository.get_for_organization(
                issue_id=issue_id,
                organization_id=organization_id,
            )
            if issue is None:
                continue
            if str(issue.get("project_id")) != project_id:
                continue
            if not self._is_issue_visible(issue, actor_role):
                continue

            buckets[category].append(
                QualityIssueVisitDiffEntry(
                    issue=parse_quality_issue_row(issue),
                    line_id=line_id,
                    category=category,
                )
            )

        return QualityIssueVisitDiffResponse(
            project_id=project_id,
            report_id=report_id,
            new=buckets[QualityIssueVisitDiffCategory.NEW],
            closed=buckets[QualityIssueVisitDiffCategory.CLOSED],
            still_open=buckets[QualityIssueVisitDiffCategory.STILL_OPEN],
            recurring=buckets[QualityIssueVisitDiffCategory.RECURRING],
            total_new=len(buckets[QualityIssueVisitDiffCategory.NEW]),
            total_closed=len(buckets[QualityIssueVisitDiffCategory.CLOSED]),
            total_still_open=len(buckets[QualityIssueVisitDiffCategory.STILL_OPEN]),
            total_recurring=len(buckets[QualityIssueVisitDiffCategory.RECURRING]),
        )

    def _classify_report_events(
        self,
        *,
        organization_id: str,
        project_id: str,
        report_id: str,
    ) -> list[tuple[str, str | None, QualityIssueVisitDiffCategory]]:
        events = self.event_repository.list_by_report_id(report_id)
        grouped: dict[str, list[dict[str, Any]]] = {}

        for event in events:
            event_type = str(event.get("event_type") or "")
            if event_type not in _EVENT_TO_CATEGORY:
                continue

            issue_id = str(event.get("issue_id") or "").strip()
            if not issue_id:
                continue

            grouped.setdefault(issue_id, []).append(event)

        classified: list[tuple[str, str | None, QualityIssueVisitDiffCategory]] = []

        for issue_id, issue_events in grouped.items():
            primary = min(
                issue_events,
                key=lambda event: (
                    _EVENT_CATEGORY_PRIORITY.get(
                        QualityIssueEventType(str(event.get("event_type"))),
                        99,
                    ),
                    0 if event.get("line_id") else 1,
                ),
            )
            event_type = QualityIssueEventType(str(primary.get("event_type")))
            category = _EVENT_TO_CATEGORY[event_type]
            line_id = primary.get("line_id")

            if category == QualityIssueVisitDiffCategory.STILL_OPEN:
                issue = self.issue_repository.get_for_organization(
                    issue_id=issue_id,
                    organization_id=organization_id,
                )
                if issue is None or str(issue.get("project_id")) != project_id:
                    continue
                if str(issue.get("status") or "") not in OPEN_ISSUE_STATUSES:
                    continue

            classified.append(
                (
                    issue_id,
                    str(line_id).strip() if line_id else None,
                    category,
                )
            )

        return classified

    def _require_read_permission(self, actor_role: str | None) -> None:
        from app.exceptions.exceptions import ForbiddenError

        if not has_qc_permission(actor_role, "quality_issues:read"):
            raise ForbiddenError("Missing quality_issues:read permission")

    def _ensure_project(
        self,
        organization_id: str,
        project_id: str,
    ) -> dict:
        project = self.project_repository.get_project_by_id(project_id)
        if project is None:
            raise NotFoundError(
                message="Project not found",
                resource_type="project",
                resource_id=project_id,
            )
        if str(project.get("organization_id")) != organization_id:
            raise NotFoundError(
                message="Project not found",
                resource_type="project",
                resource_id=project_id,
            )
        return project

    def _ensure_report(
        self,
        *,
        organization_id: str,
        project_id: str,
        report_id: str,
    ) -> dict:
        report = self.report_repository.get_by_id(report_id)
        if report is None:
            raise NotFoundError(
                message="Field visit report not found",
                resource_type="field_visit_report",
                resource_id=report_id,
            )
        if str(report.get("organization_id")) != organization_id:
            raise NotFoundError(
                message="Field visit report not found",
                resource_type="field_visit_report",
                resource_id=report_id,
            )
        if str(report.get("project_id")) != project_id:
            raise NotFoundError(
                message="Field visit report not found",
                resource_type="field_visit_report",
                resource_id=report_id,
            )
        return report

    def _is_issue_visible(
        self,
        record: dict[str, Any],
        actor_role: str | None,
    ) -> bool:
        visible = visible_issue_statuses_for_role(actor_role)
        if visible is None:
            return True

        status = record.get("status")
        return status in {item.value for item in visible}
