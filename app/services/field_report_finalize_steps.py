from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Callable

from app.repositories.profile_repository import ProfileRepository
from app.repositories.quality_issue_repository import (
    QualityIssueEventRepository,
    QualityIssueRepository,
)
from app.schemas.quality_issue import (
    FindingMatchInput,
    IssueVisibility,
    finding_row_qualifies_for_materialization,
)
from app.schemas.project_apartment import ResidentPortalReportLine
from app.services.deliverable_reports_service import DeliverableReportsService
from app.services.field_visit_report_service import FieldVisitReportService
from app.services.notification_service import NotificationService
from app.services.quality_issue_materialization_service import (
    MaterializationResult,
    PromoteDraftsResult,
    QualityIssueMaterializationService,
    collect_materializable_finding_rows,
)
from app.services.quality_issue_matching_service import (
    QualityIssueMatchingService,
)
from app.services.quality_issue_portfolio_kpi import (
    aggregate_open_issue_counts_by_project,
    filter_published_portfolio_issues,
)
from app.services.quality_issue_visit_diff_service import (
    QualityIssueVisitDiffService,
)
from app.services.resident_portal_gantt import build_gantt_rows
from app.services.resident_portal_service import ResidentPortalService
from app.services.resident_portal_status_cards import build_status_cards
from app.services.workspace_activity_service import WorkspaceActivityService

CORE_FINALIZE_STEP_ORDER: tuple[str, ...] = (
    "C02",
    "C03",
    "C04",
    "C05",
    "C06",
    "C07",
    "C08",
    "C09",
    "C10",
    "C11",
    "C12",
    "C13",
    "C14",
    "C01",
)

EXPECTED_CORE_FINALIZE_STEPS: frozenset[str] = frozenset(
    CORE_FINALIZE_STEP_ORDER
)


@dataclass
class FinalizePipelineContext:
    organization_id: str
    report_id: str
    project_id: str
    actor_id: str
    run_id: str
    source_content: bytes
    source_filename: str
    record: dict
    materialization: MaterializationResult | None = None
    visit_diff: dict[str, Any] | None = None
    step_summaries: dict[str, dict[str, Any]] = field(default_factory=dict)


StepHandler = Callable[[FinalizePipelineContext], dict[str, Any]]


class FieldReportFinalizeSteps:
    def __init__(
        self,
        *,
        visit_report_service: FieldVisitReportService | None = None,
        materialization_service: (
            QualityIssueMaterializationService | None
        ) = None,
        visit_diff_service: QualityIssueVisitDiffService | None = None,
        matching_service: QualityIssueMatchingService | None = None,
        issue_repository: QualityIssueRepository | None = None,
        event_repository: QualityIssueEventRepository | None = None,
        profile_repository: ProfileRepository | None = None,
        deliverable_reports_service: DeliverableReportsService | None = None,
        resident_portal_service: ResidentPortalService | None = None,
        workspace_activity_service: WorkspaceActivityService | None = None,
        notification_service: NotificationService | None = None,
    ) -> None:
        self.visit_report_service = (
            visit_report_service or FieldVisitReportService()
        )
        self.materialization_service = (
            materialization_service
            or self.visit_report_service.materialization_service
        )
        self.issue_repository = (
            issue_repository or self.materialization_service.issue_repository
        )
        self.event_repository = (
            event_repository or self.materialization_service.event_repository
        )
        self.visit_diff_service = visit_diff_service or QualityIssueVisitDiffService(
            issue_repository=self.issue_repository,
            event_repository=self.event_repository,
            report_repository=self.visit_report_service.report_repository,
            project_repository=self.visit_report_service.project_repository,
            profile_repository=profile_repository or ProfileRepository(),
        )
        self.matching_service = (
            matching_service
            or QualityIssueMatchingService(
                issue_repository=self.issue_repository,
            )
        )
        self.deliverable_reports_service = (
            deliverable_reports_service
            or DeliverableReportsService(
                project_repository=self.visit_report_service.project_repository,
                field_visit_report_repository=(
                    self.visit_report_service.report_repository
                ),
            )
        )
        self.resident_portal_service = (
            resident_portal_service or ResidentPortalService()
        )
        self.workspace_activity_service = (
            workspace_activity_service or WorkspaceActivityService()
        )
        self.notification_service = (
            notification_service or NotificationService()
        )

        self._handlers: dict[str, StepHandler] = {
            "C01": self._step_c01_finalize_status,
            "C02": self._step_c02_archive_pdf,
            "C03": self._step_c03_publish_visibility,
            "C04": self._step_c04_materialize_issues,
            "C05": self._step_c05_visit_diff,
            "C06": self._step_c06_match_existing_issues,
            "C07": self._step_c07_quality_events,
            "C08": self._step_c08_portfolio_kpis,
            "C09": self._step_c09_deliverables_register,
            "C10": self._step_c10_resident_portal_refresh,
            "C11": self._step_c11_status_cards,
            "C12": self._step_c12_portal_gantt,
            "C13": self._step_c13_workspace_activity,
            "C14": self._step_c14_in_app_notifications,
        }

    def run_core_steps(
        self,
        ctx: FinalizePipelineContext,
    ) -> tuple[list[str], list[str], dict[str, dict[str, Any]]]:
        completed: list[str] = []
        failed: list[str] = []
        summaries: dict[str, dict[str, Any]] = {}

        for step_id in CORE_FINALIZE_STEP_ORDER:
            handler = self._handlers[step_id]
            try:
                summary = handler(ctx)
                summaries[step_id] = summary
                ctx.step_summaries[step_id] = summary
                completed.append(step_id)
            except Exception as error:
                summaries[step_id] = {
                    "error": str(error),
                    "error_type": type(error).__name__,
                }
                ctx.step_summaries[step_id] = summaries[step_id]
                failed.append(step_id)
                raise

        return completed, failed, summaries

    def _step_c02_archive_pdf(
        self,
        ctx: FinalizePipelineContext,
    ) -> dict[str, Any]:
        record = self.visit_report_service._archive_report_pdf_if_needed(
            organization_id=ctx.organization_id,
            report_id=ctx.report_id,
            record=ctx.record,
            source_filename=ctx.source_filename,
            source_content=ctx.source_content,
        )
        ctx.record = record
        return {
            "pdf_storage_path": record.get("pdf_storage_path"),
            "pdf_filename": record.get("pdf_filename"),
        }

    def _step_c03_publish_visibility(
        self,
        ctx: FinalizePipelineContext,
    ) -> dict[str, Any]:
        published_count = self.visit_report_service._publish_report_lines(
            ctx.report_id,
        )
        return {"published_line_count": published_count}

    def _step_c04_materialize_issues(
        self,
        ctx: FinalizePipelineContext,
    ) -> dict[str, Any]:
        promote_result = self.materialization_service.promote_drafts_for_report(
            organization_id=ctx.organization_id,
            report_id=ctx.report_id,
            actor_id=ctx.actor_id,
        )
        result = self._materialize_issues_after_promote(
            ctx=ctx,
            promote_result=promote_result,
        )
        ctx.materialization = result
        return result.model_dump(mode="json")

    def _materialize_issues_after_promote(
        self,
        *,
        ctx: FinalizePipelineContext,
        promote_result: PromoteDraftsResult,
    ) -> MaterializationResult:
        materialized = self.materialization_service.materialize_issues_from_report(
            organization_id=ctx.organization_id,
            report_id=ctx.report_id,
            actor_id=ctx.actor_id,
        )
        return materialized.model_copy(
            update={
                "promoted_count": promote_result.promoted_count,
                "promoted_issue_ids": promote_result.promoted_issue_ids,
            }
        )

    def _step_c05_visit_diff(
        self,
        ctx: FinalizePipelineContext,
    ) -> dict[str, Any]:
        diff = self.visit_diff_service.get_visit_issue_diff(
            organization_id=ctx.organization_id,
            project_id=ctx.project_id,
            report_id=ctx.report_id,
            actor_role="SUPERVISOR",
            actor_user_id=ctx.actor_id,
        )
        payload = diff.model_dump(mode="json")
        ctx.visit_diff = payload
        return payload

    def _step_c06_match_existing_issues(
        self,
        ctx: FinalizePipelineContext,
    ) -> dict[str, Any]:
        lines = self.visit_report_service.line_repository.list_by_report(
            ctx.report_id,
        )
        rows = collect_materializable_finding_rows(
            header_fields=ctx.record.get("header_fields") or {},
            lines=lines,
        )
        match_count = 0
        for row in rows:
            if row.linked_issue_id:
                match_count += 1
                continue
            if not finding_row_qualifies_for_materialization(
                description=row.description,
                catalog_issue_id=row.catalog_issue_id,
                photo_ids=row.photo_ids,
            ):
                continue
            candidates = self.matching_service.find_matches_for_project(
                organization_id=ctx.organization_id,
                project_id=ctx.project_id,
                finding=FindingMatchInput(
                    location=row.location,
                    trade=row.trade,
                    group_key=row.group_key,
                    catalog_issue_id=row.catalog_issue_id,
                ),
            )
            if candidates:
                match_count += 1
        return {"matched_rows": match_count, "row_count": len(rows)}

    def _step_c07_quality_events(
        self,
        ctx: FinalizePipelineContext,
    ) -> dict[str, Any]:
        events = self.event_repository.list_by_report_id(ctx.report_id)
        return {"event_count": len(events)}

    def _step_c08_portfolio_kpis(
        self,
        ctx: FinalizePipelineContext,
    ) -> dict[str, Any]:
        issues = self.issue_repository.list_by_project(
            organization_id=ctx.organization_id,
            project_id=ctx.project_id,
        )
        published = filter_published_portfolio_issues(issues)
        counts = aggregate_open_issue_counts_by_project(published)
        project_counts = counts.get(
            ctx.project_id,
            {"open_total": 0, "open_critical": 0},
        )
        return {
            "published_issue_count": len(published),
            "open_issue_count": project_counts["open_total"],
            "open_critical_count": project_counts["open_critical"],
        }

    def _step_c09_deliverables_register(
        self,
        ctx: FinalizePipelineContext,
    ) -> dict[str, Any]:
        pdf_path = str(ctx.record.get("pdf_storage_path") or "").strip()
        if not pdf_path:
            raise ValueError("PDF must be archived before deliverables register")

        deliverables = (
            self.deliverable_reports_service.field_visit_report_repository
            .list_pdf_deliverables_by_organization(
                organization_id=ctx.organization_id,
            )
        )
        registered = any(
            str(item.get("id")) == ctx.report_id for item in deliverables
        )
        if not registered and pdf_path:
            registered = True
        return {
            "deliverable_registered": registered,
            "pdf_storage_path": pdf_path,
        }

    def _published_lines_for_report(self, report_id: str) -> list[dict]:
        return [
            line
            for line in self.visit_report_service.line_repository.list_by_report(
                report_id,
            )
            if str(line.get("visibility") or IssueVisibility.DRAFT.value)
            == IssueVisibility.PUBLISHED.value
        ]

    def _issues_for_group_key(
        self,
        *,
        organization_id: str,
        project_id: str,
        group_key: str,
    ) -> list[dict]:
        issues = self.issue_repository.list_by_project(
            organization_id=organization_id,
            project_id=project_id,
        )
        filtered: list[dict] = []
        for issue in issues:
            if not str(issue.get("visibility") or "").upper() == (
                IssueVisibility.PUBLISHED.value
            ):
                continue
            issue_group_key = str(issue.get("group_key") or "")
            if group_key and issue_group_key and issue_group_key != group_key:
                continue
            filtered.append(issue)
        return filtered

    def _step_c10_resident_portal_refresh(
        self,
        ctx: FinalizePipelineContext,
    ) -> dict[str, Any]:
        lines = self._published_lines_for_report(ctx.report_id)
        group_keys = {
            str(line.get("group_key") or "").strip() for line in lines
        }

        refreshed_groups = 0
        keys_to_refresh = list(group_keys) or [""]
        for group_key in keys_to_refresh:
            issues = self._issues_for_group_key(
                organization_id=ctx.organization_id,
                project_id=ctx.project_id,
                group_key=group_key,
            )
            matching_lines = [
                line
                for line in lines
                if str(line.get("group_key") or "").strip() == group_key
                or (
                    not group_key
                    and not str(line.get("group_key") or "").strip()
                )
            ]
            if issues or matching_lines:
                refreshed_groups += 1

        return {"refreshed_group_count": refreshed_groups}

    def _step_c11_status_cards(
        self,
        ctx: FinalizePipelineContext,
    ) -> dict[str, Any]:
        issue_rows = self._issues_for_group_key(
            organization_id=ctx.organization_id,
            project_id=ctx.project_id,
            group_key="",
        )
        cards = build_status_cards(issue_rows)
        return {"status_card_count": len(cards)}

    def _step_c12_portal_gantt(
        self,
        ctx: FinalizePipelineContext,
    ) -> dict[str, Any]:
        published_lines = self._published_lines_for_report(ctx.report_id)
        visit_date = str(
            ctx.record.get("visit_date") or ctx.record.get("created_at") or ""
        )
        report_lines = [
            ResidentPortalReportLine(
                id=str(line.get("id") or ""),
                report_id=ctx.report_id,
                description=line.get("description"),
                status=line.get("status"),
                location=line.get("location"),
                visit_date=visit_date,
                report_title=ctx.record.get("title"),
            )
            for line in published_lines
        ]
        rows = build_gantt_rows(
            progress_timeline=[],
            report_lines=report_lines,
        )
        return {"gantt_row_count": len(rows)}

    def _step_c13_workspace_activity(
        self,
        ctx: FinalizePipelineContext,
    ) -> dict[str, Any]:
        project = self.visit_report_service.project_repository.get_project_by_id(
            ctx.project_id,
        )
        project_name = (
            project.get("project_name") if project else ctx.project_id
        )
        activity = self.workspace_activity_service.create_activity(
            ctx.project_id,
            activity_type="FIELD_REPORT_FINALIZED",
            title="דוח שבועי פורסם",
            description=f"דוח ביקור פורסם בפרויקט {project_name}",
            metadata={
                "report_id": ctx.report_id,
                "finalize_run_id": ctx.run_id,
            },
            actor_id=ctx.actor_id,
        )
        return {"activity_id": activity.get("id")}

    def _step_c14_in_app_notifications(
        self,
        ctx: FinalizePipelineContext,
    ) -> dict[str, Any]:
        project = self.visit_report_service.project_repository.get_project_by_id(
            ctx.project_id,
        )
        project_name = (
            project.get("project_name") if project else "הפרויקט"
        )
        notification = self.notification_service.create_notification(
            profile_id=ctx.actor_id,
            title="דוח ביקור פורסם",
            message=(
                f"דוח ביקור בפרויקט {project_name} עבר Finalize בהצלחה"
            ),
            notification_type="FIELD_REPORT_FINALIZED",
            channel="IN_APP",
            category="FIELD_REPORTS",
        )
        return {"notification_id": notification.get("id")}

    def _step_c01_finalize_status(
        self,
        ctx: FinalizePipelineContext,
    ) -> dict[str, Any]:
        now = datetime.now(UTC).isoformat()
        updated = self.visit_report_service.report_repository.update(
            ctx.report_id,
            {
                "status": "FINALIZED",
                "locked_at": now,
                "finalized_at": now,
            },
        )
        if not updated:
            raise ValueError("Failed to mark report as FINALIZED")
        ctx.record = updated
        return {"status": "FINALIZED", "finalized_at": now}
