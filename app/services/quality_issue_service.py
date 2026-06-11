from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from app.exceptions.exceptions import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    ValidationError,
)
from app.repositories.field_visit_report_repository import (
    FieldVisitReportRepository,
)
from app.repositories.project_repository import ProjectRepository
from app.repositories.quality_issue_photo_repository import (
    QualityIssuePhotoRepository,
)
from app.repositories.quality_issue_repository import (
    OPEN_ISSUE_STATUSES,
    QualityIssueEventRepository,
    QualityIssueRepository,
)
from app.schemas.qc_permissions import (
    can_perform_issue_transition,
    has_qc_permission,
    visible_issue_statuses_for_role,
)
from app.schemas.quality_issue import (
    QualityIssueCreateRequest,
    QualityIssueDetailResponse,
    QualityIssueEventType,
    QualityIssueListQuery,
    QualityIssueListResponse,
    QualityIssueOrgListResponse,
    QualityIssueOpenListResponse,
    QualityIssueSeverity,
    QualityIssueStatus,
    QualityIssueSuggestMatchesRequest,
    QualityIssueSuggestMatchesResponse,
    QualityIssueUpdateRequest,
    QualityIssueVisitDiffResponse,
    QualityPeriodicReportResponse,
    QualityPortfolioSummaryResponse,
    QualityRecurringRankingsResponse,
    QualityTradeHeatmapResponse,
    parse_quality_issue_event_row,
    parse_quality_issue_row,
    preferred_event_type_for_transition,
    validate_event_fields,
    validate_status_update,
)
from app.services.catalog_standard_ref_resolver import (
    enrich_issue_standard_ref,
    resolve_catalog_link_for_issue,
)
from app.services.field_report_catalog_service import (
    FieldReportCatalogService,
)
from app.services.quality_issue_matching_service import (
    QualityIssueMatchingService,
    match_key_for_finding,
)
from app.services.quality_issue_portfolio_kpi import (
    aggregate_average_open_days_by_project,
    aggregate_critical_stale_by_project,
    aggregate_open_issue_counts_by_project,
    build_open_issues_per_project_summaries,
    compute_average_open_days,
    compute_closed_within_days_percent,
    count_critical_open_over_days,
)
from app.services.quality_issue_recurring_rankings import (
    build_contractor_recurring_rankings,
    build_recurring_issue_rankings,
    is_recurring_issue,
)
from app.services.quality_issue_trade_heatmap import (
    build_trade_heatmap_cells,
)
from app.services.quality_issue_periodic_report_service import (
    build_periodic_report_response,
    render_periodic_report_csv,
)
from app.services.quality_issue_photo_service import (
    QualityIssuePhotoService,
)
from app.services.quality_issue_visit_diff_service import (
    QualityIssueVisitDiffService,
)


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _utc_now_iso() -> str:
    return _utc_now().isoformat()


def _parse_timestamp(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value
    text = str(value).strip()
    if not text:
        return None
    normalized = text.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed


def _days_between(start: datetime, end: datetime) -> int:
    return max(0, int((end - start).total_seconds() // 86400))


class QualityIssueService:
    def __init__(
        self,
        issue_repository: QualityIssueRepository | None = None,
        event_repository: QualityIssueEventRepository | None = None,
        project_repository: ProjectRepository | None = None,
        report_repository: FieldVisitReportRepository | None = None,
        photo_repository: QualityIssuePhotoRepository | None = None,
        photo_service: QualityIssuePhotoService | None = None,
        catalog_service: FieldReportCatalogService | None = None,
    ) -> None:
        self.issue_repository = (
            issue_repository or QualityIssueRepository()
        )
        self.event_repository = (
            event_repository or QualityIssueEventRepository()
        )
        self.project_repository = (
            project_repository or ProjectRepository()
        )
        self.report_repository = (
            report_repository or FieldVisitReportRepository()
        )
        self.photo_repository = (
            photo_repository or QualityIssuePhotoRepository()
        )
        self.photo_service = photo_service or QualityIssuePhotoService()
        self.catalog_service = catalog_service or FieldReportCatalogService()
        self.visit_diff_service = QualityIssueVisitDiffService(
            issue_repository=self.issue_repository,
            event_repository=self.event_repository,
            report_repository=self.report_repository,
            project_repository=self.project_repository,
        )

    def is_storage_available(self) -> bool:
        return self.issue_repository.is_storage_available()

    def create_issue(
        self,
        *,
        organization_id: str,
        project_id: str,
        request: QualityIssueCreateRequest,
        actor_role: str | None,
        actor_id: str | None = None,
    ) -> dict:
        self._require_write_permission(actor_role)
        self._ensure_project(organization_id, project_id)

        existing = self.issue_repository.get_by_materialization_key(
            organization_id=organization_id,
            materialization_key=request.materialization_key,
        )
        if existing is not None:
            raise ConflictError(
                message="Issue already exists for this materialization key",
                details={
                    "materialization_key": request.materialization_key,
                    "issue_id": existing.get("id"),
                },
            )

        record = self.issue_repository.create(
            organization_id=organization_id,
            project_id=project_id,
            request=request,
        )

        self._append_detected_event(
            issue=record,
            actor_id=actor_id,
        )
        return record

    def list_issues(
        self,
        *,
        organization_id: str,
        project_id: str,
        query: QualityIssueListQuery | None = None,
        actor_role: str | None,
    ) -> QualityIssueListResponse:
        self._require_read_permission(actor_role)
        self._ensure_project(organization_id, project_id)

        filters = self._apply_visible_status_filter(
            query or QualityIssueListQuery(),
            actor_role,
        )
        rows = self.issue_repository.list_by_project(
            organization_id=organization_id,
            project_id=project_id,
            query=filters,
        )
        total = self.issue_repository.count_by_project(
            organization_id=organization_id,
            project_id=project_id,
            query=filters,
        )

        return QualityIssueListResponse(
            project_id=project_id,
            total=total,
            limit=filters.limit,
            offset=filters.offset,
            items=[parse_quality_issue_row(row) for row in rows],
        )

    def list_organization_issues(
        self,
        *,
        organization_id: str,
        query: QualityIssueListQuery | None = None,
        actor_role: str | None,
    ) -> QualityIssueOrgListResponse:
        self._require_read_permission(actor_role)

        filters = self._apply_visible_status_filter(
            query or QualityIssueListQuery(),
            actor_role,
        )
        rows = self.issue_repository.list_by_organization(
            organization_id=organization_id,
            query=filters,
        )
        total = self.issue_repository.count_by_organization(
            organization_id=organization_id,
            query=filters,
        )

        return QualityIssueOrgListResponse(
            organization_id=organization_id,
            total=total,
            limit=filters.limit,
            offset=filters.offset,
            items=[parse_quality_issue_row(row) for row in rows],
        )

    def list_open_issues(
        self,
        *,
        organization_id: str,
        project_id: str,
        actor_role: str | None,
    ) -> QualityIssueOpenListResponse:
        self._require_read_permission(actor_role)
        self._ensure_project(organization_id, project_id)

        rows = self.issue_repository.list_open_by_project(
            organization_id=organization_id,
            project_id=project_id,
        )
        visible = visible_issue_statuses_for_role(actor_role)
        if visible is not None:
            allowed = {status.value for status in visible}
            rows = [
                row
                for row in rows
                if row.get("status") in allowed
            ]

        items = [parse_quality_issue_row(row) for row in rows]
        return QualityIssueOpenListResponse(
            project_id=project_id,
            total=len(items),
            items=items,
        )

    def get_visit_issue_diff(
        self,
        *,
        organization_id: str,
        project_id: str,
        report_id: str,
        actor_role: str | None,
    ) -> QualityIssueVisitDiffResponse:
        return self.visit_diff_service.get_visit_issue_diff(
            organization_id=organization_id,
            project_id=project_id,
            report_id=report_id,
            actor_role=actor_role,
        )

    def suggest_matches(
        self,
        *,
        organization_id: str,
        project_id: str,
        request: QualityIssueSuggestMatchesRequest,
        actor_role: str | None,
    ) -> QualityIssueSuggestMatchesResponse:
        self._require_read_permission(actor_role)
        self._ensure_project(organization_id, project_id)

        finding = request.to_finding_input()
        open_issues = self.list_open_issues(
            organization_id=organization_id,
            project_id=project_id,
            actor_role=actor_role,
        )
        matcher = QualityIssueMatchingService(self.issue_repository)
        candidates = matcher.find_matches(
            finding=finding,
            open_issues=open_issues.items,
            limit=request.limit,
        )
        return QualityIssueSuggestMatchesResponse(
            project_id=project_id,
            match_key=match_key_for_finding(finding),
            total=len(candidates),
            candidates=candidates,
        )

    def get_portfolio_quality_summary(
        self,
        *,
        organization_id: str,
        actor_role: str | None,
    ) -> QualityPortfolioSummaryResponse:
        self._require_portfolio_read_permission(actor_role)

        issues = self.issue_repository.list_by_organization(
            organization_id=organization_id,
        )
        projects = self.project_repository.get_projects_by_organization(
            organization_id
        )

        now = _utc_now()
        open_issues = [
            issue
            for issue in issues
            if issue.get("status") in OPEN_ISSUE_STATUSES
        ]
        closed_issues = [
            issue
            for issue in issues
            if issue.get("status") == QualityIssueStatus.CLOSED.value
        ]

        open_counts_by_project = aggregate_open_issue_counts_by_project(
            open_issues
        )
        critical_stale_by_project = aggregate_critical_stale_by_project(
            open_issues,
            now=now,
        )
        average_open_days_by_project = aggregate_average_open_days_by_project(
            open_issues,
            now=now,
        )
        critical_open_over_14_days = count_critical_open_over_days(
            open_issues,
            now=now,
        )
        average_open_days = compute_average_open_days(
            open_issues,
            now=now,
        )
        closed_within_30_days_percent = compute_closed_within_days_percent(
            closed_issues
        )

        project_summaries = build_open_issues_per_project_summaries(
            projects=projects,
            open_counts_by_project=open_counts_by_project,
            critical_stale_by_project=critical_stale_by_project,
            average_open_days_by_project=average_open_days_by_project,
        )

        return QualityPortfolioSummaryResponse(
            organization_id=organization_id,
            total_open=len(open_issues),
            total_open_critical=sum(
                1
                for issue in open_issues
                if issue.get("severity") == QualityIssueSeverity.CRITICAL.value
            ),
            critical_open_over_14_days=critical_open_over_14_days,
            average_open_days=average_open_days,
            closed_within_30_days_percent=closed_within_30_days_percent,
            projects=project_summaries,
        )

    def get_portfolio_trade_heatmap(
        self,
        *,
        organization_id: str,
        actor_role: str | None,
        project_id: str | None = None,
    ) -> QualityTradeHeatmapResponse:
        self._require_portfolio_read_permission(actor_role)

        issues = self.issue_repository.list_by_organization(
            organization_id=organization_id,
        )

        normalized_project_id = (project_id or "").strip() or None
        if normalized_project_id:
            issues = [
                issue
                for issue in issues
                if str(issue.get("project_id") or "") == normalized_project_id
            ]

        open_issues = [
            issue
            for issue in issues
            if issue.get("status") in OPEN_ISSUE_STATUSES
        ]

        return QualityTradeHeatmapResponse(
            organization_id=organization_id,
            project_id=normalized_project_id,
            total_open=len(open_issues),
            cells=build_trade_heatmap_cells(open_issues),
        )

    def get_portfolio_recurring_rankings(
        self,
        *,
        organization_id: str,
        actor_role: str | None,
        project_id: str | None = None,
    ) -> QualityRecurringRankingsResponse:
        self._require_portfolio_read_permission(actor_role)

        issues = self.issue_repository.list_by_organization(
            organization_id=organization_id,
        )
        projects = self.project_repository.get_projects_by_organization(
            organization_id
        )

        normalized_project_id = (project_id or "").strip() or None
        if normalized_project_id:
            issues = [
                issue
                for issue in issues
                if str(issue.get("project_id") or "") == normalized_project_id
            ]
            projects = [
                project
                for project in projects
                if str(project.get("id") or "") == normalized_project_id
            ]

        recurring_issues = [
            issue for issue in issues if is_recurring_issue(issue)
        ]

        return QualityRecurringRankingsResponse(
            organization_id=organization_id,
            project_id=normalized_project_id,
            total_recurring=len(recurring_issues),
            issues=build_recurring_issue_rankings(
                issues,
                projects=projects,
            ),
            contractors=build_contractor_recurring_rankings(
                issues,
                projects=projects,
            ),
        )

    def get_portfolio_periodic_report(
        self,
        *,
        organization_id: str,
        actor_role: str | None,
        period_days: int = 30,
        project_id: str | None = None,
    ) -> QualityPeriodicReportResponse:
        self._require_portfolio_read_permission(actor_role)

        issues = self.issue_repository.list_by_organization(
            organization_id=organization_id,
        )
        projects = self.project_repository.get_projects_by_organization(
            organization_id
        )

        normalized_project_id = (project_id or "").strip() or None
        if normalized_project_id:
            issues = [
                issue
                for issue in issues
                if str(issue.get("project_id") or "") == normalized_project_id
            ]
            projects = [
                project
                for project in projects
                if str(project.get("id") or "") == normalized_project_id
            ]

        enriched_issues = [
            enrich_issue_standard_ref(
                issue,
                catalog_service=self.catalog_service,
            )
            for issue in issues
        ]

        return build_periodic_report_response(
            organization_id=organization_id,
            issues=enriched_issues,
            projects=projects,
            period_days=period_days,
            project_id=normalized_project_id,
        )

    def export_portfolio_periodic_report_csv(
        self,
        *,
        organization_id: str,
        actor_role: str | None,
        period_days: int = 30,
        project_id: str | None = None,
    ) -> str:
        report = self.get_portfolio_periodic_report(
            organization_id=organization_id,
            actor_role=actor_role,
            period_days=period_days,
            project_id=project_id,
        )
        return render_periodic_report_csv(report)

    def get_issue_detail(
        self,
        *,
        organization_id: str,
        issue_id: str,
        actor_role: str | None,
    ) -> QualityIssueDetailResponse:
        self._require_read_permission(actor_role)
        record = self._get_issue_for_org(
            organization_id=organization_id,
            issue_id=issue_id,
        )
        self._ensure_issue_visible(record, actor_role)

        enriched = enrich_issue_standard_ref(
            record,
            catalog_service=self.catalog_service,
        )
        catalog_link = resolve_catalog_link_for_issue(
            catalog_issue_id=enriched.get("catalog_issue_id"),
            catalog_service=self.catalog_service,
        )
        events = self.event_repository.list_by_issue_id(issue_id)
        return QualityIssueDetailResponse(
            issue=parse_quality_issue_row(enriched),
            events=[
                parse_quality_issue_event_row(event)
                for event in events
            ],
            catalog_link=catalog_link,
        )

    def update_issue(
        self,
        *,
        organization_id: str,
        issue_id: str,
        request: QualityIssueUpdateRequest,
        actor_role: str | None,
        actor_id: str | None = None,
    ) -> dict:
        record = self._get_issue_for_org(
            organization_id=organization_id,
            issue_id=issue_id,
        )
        self._ensure_issue_visible(record, actor_role)

        updates = request.model_dump(exclude_unset=True, mode="json")
        transition_notes = updates.pop("notes", None)
        status_change = self._extract_status_change(record, updates)
        remediation_photo_ids: list[str] | None = None

        if status_change is not None:
            self._authorize_status_transition(
                actor_role=actor_role,
                from_status=status_change["from_status"],
                to_status=status_change["to_status"],
            )
            remediation_photo_ids = self._prepare_remediation_photos(
                record=record,
                updates=updates,
                from_status=status_change["from_status"],
                to_status=status_change["to_status"],
                organization_id=organization_id,
            )
            self._apply_status_side_effects(
                record=record,
                updates=updates,
                from_status=status_change["from_status"],
                to_status=status_change["to_status"],
                actor_id=actor_id,
            )
        elif self._has_non_status_updates(updates):
            self._require_write_permission(actor_role)

        updated = self.issue_repository.update(issue_id, updates)
        if updated is None:
            raise NotFoundError(
                message="Quality issue not found",
                resource_type="quality_issue",
                resource_id=issue_id,
            )

        if status_change is not None:
            self._append_transition_event(
                issue=updated,
                from_status=status_change["from_status"],
                to_status=status_change["to_status"],
                actor_id=actor_id,
                report_id=updates.get("last_seen_report_id"),
                line_id=updates.get("last_seen_line_id"),
                photo_ids=remediation_photo_ids,
                notes=transition_notes,
            )

        return updated

    def upload_remediation_photo(
        self,
        *,
        organization_id: str,
        issue_id: str,
        content: bytes,
        content_type: str | None,
        filename: str | None = None,
        actor_role: str | None,
    ) -> dict:
        record = self._get_issue_for_org(
            organization_id=organization_id,
            issue_id=issue_id,
        )
        self._ensure_issue_visible(record, actor_role)
        self._require_remediate_permission(actor_role)

        if record.get("status") != QualityIssueStatus.IN_REMEDIATION.value:
            raise ValidationError(
                message="ניתן להעלות תמונת תיקון רק לליקוי בסטטוס בטיפול",
            )

        photo_id = str(uuid4())
        storage_path = self.photo_service.save_photo(
            organization_id=organization_id,
            issue_id=issue_id,
            photo_id=photo_id,
            content=content,
            content_type=content_type,
            filename=filename,
        )

        if self.photo_repository.is_storage_available():
            self.photo_repository.create(
                {
                    "id": photo_id,
                    "organization_id": organization_id,
                    "project_id": str(record["project_id"]),
                    "issue_id": issue_id,
                    "storage_path": storage_path,
                    "kind": "remediation",
                    "sort_order": self.photo_repository.next_sort_order(
                        issue_id
                    ),
                }
            )

        return {
            "issue_id": issue_id,
            "photo_id": photo_id,
            "url": self._issue_photo_url(
                issue_id=issue_id,
                photo_id=photo_id,
            ),
        }

    def get_issue_photo(
        self,
        *,
        organization_id: str,
        issue_id: str,
        photo_id: str,
        actor_role: str | None,
    ) -> tuple[bytes, str]:
        record = self._get_issue_for_org(
            organization_id=organization_id,
            issue_id=issue_id,
        )
        self._ensure_issue_visible(record, actor_role)
        self._require_read_permission(actor_role)

        photo = self.photo_repository.get_for_issue(
            issue_id=issue_id,
            photo_id=photo_id,
            organization_id=organization_id,
        )
        if photo is None:
            raise NotFoundError(
                message="Issue photo not found",
                resource_type="quality_issue_photo",
                resource_id=photo_id,
            )

        return self.photo_service.read_photo(str(photo["storage_path"]))

    def _require_read_permission(self, actor_role: str | None) -> None:
        if not has_qc_permission(actor_role, "quality_issues:read"):
            raise ForbiddenError("Missing quality_issues:read permission")

    def _require_portfolio_read_permission(
        self,
        actor_role: str | None,
    ) -> None:
        if not has_qc_permission(actor_role, "quality_portfolio:read"):
            raise ForbiddenError(
                "Missing quality_portfolio:read permission"
            )

    def _require_write_permission(self, actor_role: str | None) -> None:
        if not has_qc_permission(actor_role, "quality_issues:write"):
            raise ForbiddenError("Missing quality_issues:write permission")

    def _require_verify_permission(self, actor_role: str | None) -> None:
        if not has_qc_permission(actor_role, "quality_issues:verify"):
            raise ForbiddenError("Missing quality_issues:verify permission")

    def _require_remediate_permission(self, actor_role: str | None) -> None:
        if not has_qc_permission(actor_role, "quality_issues:remediate"):
            raise ForbiddenError("Missing quality_issues:remediate permission")

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

    def _get_issue_for_org(
        self,
        *,
        organization_id: str,
        issue_id: str,
    ) -> dict:
        record = self.issue_repository.get_for_organization(
            issue_id=issue_id,
            organization_id=organization_id,
        )
        if record is None:
            raise NotFoundError(
                message="Quality issue not found",
                resource_type="quality_issue",
                resource_id=issue_id,
            )
        return record

    def _ensure_issue_visible(
        self,
        record: dict,
        actor_role: str | None,
    ) -> None:
        visible = visible_issue_statuses_for_role(actor_role)
        if visible is None:
            return

        status = record.get("status")
        if status not in {item.value for item in visible}:
            raise NotFoundError(
                message="Quality issue not found",
                resource_type="quality_issue",
                resource_id=str(record.get("id")),
            )

    def _apply_visible_status_filter(
        self,
        query: QualityIssueListQuery,
        actor_role: str | None,
    ) -> QualityIssueListQuery:
        visible = visible_issue_statuses_for_role(actor_role)
        if visible is None:
            return query

        visible_list = list(visible)
        if query.status:
            allowed = [
                status
                for status in query.status
                if status in visible
            ]
            if not allowed:
                return query.model_copy(
                    update={"status": visible_list, "limit": query.limit}
                )
            return query.model_copy(update={"status": allowed})

        return query.model_copy(update={"status": visible_list})

    def _extract_status_change(
        self,
        record: dict,
        updates: dict[str, Any],
    ) -> dict[str, QualityIssueStatus] | None:
        if "status" not in updates:
            return None

        from_status = QualityIssueStatus(record["status"])
        to_status = QualityIssueStatus(updates["status"])
        if from_status == to_status:
            updates.pop("status", None)
            return None

        try:
            validate_status_update(
                current_status=from_status,
                target_status=to_status,
            )
        except ValueError as error:
            raise ValidationError(str(error)) from error

        return {
            "from_status": from_status,
            "to_status": to_status,
        }

    def _authorize_status_transition(
        self,
        *,
        actor_role: str | None,
        from_status: QualityIssueStatus,
        to_status: QualityIssueStatus,
    ) -> None:
        if not can_perform_issue_transition(
            actor_role,
            from_status,
            to_status,
        ):
            raise ForbiddenError(
                f"Role cannot transition {from_status.value} → {to_status.value}"
            )

        if to_status == QualityIssueStatus.CLOSED:
            self._require_verify_permission(actor_role)
            return

        if (
            from_status == QualityIssueStatus.IN_REMEDIATION
            and to_status == QualityIssueStatus.PENDING_VERIFICATION
        ):
            self._require_remediate_permission(actor_role)
            return

        self._require_write_permission(actor_role)

    @staticmethod
    def _has_non_status_updates(updates: dict[str, Any]) -> bool:
        return any(key not in {"status", "notes"} for key in updates)

    def _prepare_remediation_photos(
        self,
        *,
        record: dict,
        updates: dict[str, Any],
        from_status: QualityIssueStatus,
        to_status: QualityIssueStatus,
        organization_id: str,
    ) -> list[str] | None:
        if (
            from_status != QualityIssueStatus.IN_REMEDIATION
            or to_status != QualityIssueStatus.PENDING_VERIFICATION
        ):
            return None

        submitted_ids = [
            str(photo_id).strip()
            for photo_id in (updates.get("photo_ids") or [])
            if str(photo_id).strip()
        ]
        if not submitted_ids:
            raise ValidationError(
                message="נדרשת לפחות תמונת תיקון אחת",
            )

        self._validate_remediation_photo_ids(
            organization_id=organization_id,
            issue_id=str(record["id"]),
            photo_ids=submitted_ids,
        )

        existing_ids = [
            str(photo_id).strip()
            for photo_id in (record.get("photo_ids") or [])
            if str(photo_id).strip()
        ]
        updates["photo_ids"] = list(
            dict.fromkeys([*existing_ids, *submitted_ids])
        )
        return submitted_ids

    def _validate_remediation_photo_ids(
        self,
        *,
        organization_id: str,
        issue_id: str,
        photo_ids: list[str],
    ) -> None:
        if not self.photo_repository.is_storage_available():
            return

        for photo_id in photo_ids:
            photo = self.photo_repository.get_for_issue(
                issue_id=issue_id,
                photo_id=photo_id,
                organization_id=organization_id,
            )
            if photo is None:
                raise ValidationError(
                    message="תמונת התיקון לא שייכת לליקוי",
                )

    @staticmethod
    def _issue_photo_url(*, issue_id: str, photo_id: str) -> str:
        return (
            f"/issues/{issue_id}/photos/{photo_id}"
        )

    def _apply_status_side_effects(
        self,
        *,
        record: dict,
        updates: dict[str, Any],
        from_status: QualityIssueStatus,
        to_status: QualityIssueStatus,
        actor_id: str | None,
    ) -> None:
        if to_status == QualityIssueStatus.CLOSED:
            updates.setdefault("closed_at", _utc_now_iso())
            if actor_id:
                updates.setdefault("closed_by", actor_id)
            return

        if to_status == QualityIssueStatus.REOPENED:
            current_count = int(record.get("recurrence_count") or 0)
            updates["recurrence_count"] = current_count + 1
            updates["closed_at"] = None
            updates["closed_by"] = None

    def _append_detected_event(
        self,
        *,
        issue: dict,
        actor_id: str | None,
    ) -> None:
        payload = validate_event_fields(
            event_type=QualityIssueEventType.DETECTED,
            report_id=str(issue.get("first_seen_report_id") or ""),
            actor_id=actor_id,
            payload={
                "materialization_key": issue.get("materialization_key"),
                "severity": issue.get("severity"),
                "title": issue.get("title"),
                "catalog_issue_id": issue.get("catalog_issue_id"),
                "location": issue.get("location"),
                "trade": issue.get("trade"),
                "group_key": issue.get("group_key"),
            },
        )
        self.event_repository.create(
            issue_id=str(issue["id"]),
            event_type=QualityIssueEventType.DETECTED.value,
            report_id=str(issue.get("first_seen_report_id") or ""),
            line_id=issue.get("first_seen_line_id"),
            actor_id=actor_id,
            payload=payload,
        )

    def _append_transition_event(
        self,
        *,
        issue: dict,
        from_status: QualityIssueStatus,
        to_status: QualityIssueStatus,
        actor_id: str | None,
        report_id: str | None = None,
        line_id: str | None = None,
        photo_ids: list[str] | None = None,
        notes: str | None = None,
    ) -> None:
        event_type = preferred_event_type_for_transition(
            from_status,
            to_status,
        )
        payload = self._build_transition_payload(
            event_type=event_type,
            issue=issue,
            from_status=from_status,
            to_status=to_status,
            photo_ids=photo_ids,
            notes=notes,
        )

        resolved_report_id = report_id or issue.get("last_seen_report_id")
        if event_type in {
            QualityIssueEventType.VERIFIED_CLOSED,
            QualityIssueEventType.REOPENED,
        }:
            resolved_report_id = resolved_report_id or issue.get(
                "last_seen_report_id"
            )

        validated_payload = validate_event_fields(
            event_type=event_type,
            report_id=(
                str(resolved_report_id)
                if resolved_report_id
                else None
            ),
            actor_id=actor_id,
            payload=payload,
        )

        self.event_repository.create(
            issue_id=str(issue["id"]),
            event_type=event_type.value,
            report_id=(
                str(resolved_report_id)
                if resolved_report_id
                else None
            ),
            line_id=line_id,
            actor_id=actor_id,
            payload=validated_payload,
        )

    def _build_transition_payload(
        self,
        *,
        event_type: QualityIssueEventType,
        issue: dict,
        from_status: QualityIssueStatus,
        to_status: QualityIssueStatus,
        photo_ids: list[str] | None = None,
        notes: str | None = None,
    ) -> dict[str, Any]:
        if event_type == QualityIssueEventType.REOPENED:
            return {
                "from_status": from_status.value,
                "to_status": to_status.value,
                "recurrence_count": int(issue.get("recurrence_count") or 0),
                "previous_closed_at": issue.get("closed_at"),
            }

        if event_type == QualityIssueEventType.REMEDIATION_SUBMITTED:
            payload: dict[str, Any] = {
                "from_status": from_status.value,
                "to_status": to_status.value,
                "photo_ids": photo_ids or issue.get("photo_ids") or [],
            }
            if notes and str(notes).strip():
                payload["notes"] = str(notes).strip()
            return payload

        if event_type == QualityIssueEventType.VERIFIED_CLOSED:
            return {
                "from_status": from_status.value,
                "to_status": to_status.value,
            }

        return {
            "from_status": from_status.value,
            "to_status": to_status.value,
        }
