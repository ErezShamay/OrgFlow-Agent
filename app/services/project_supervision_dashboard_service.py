"""Project supervision dashboard aggregation service (gate D1)."""

from __future__ import annotations

from app.exceptions.exceptions import ForbiddenError, NotFoundError
from app.lib.supervision_dashboard_aggregation import (
    aggregate_supervision_dashboard,
    aggregate_supervision_trade_detail,
)
from app.repositories.field_visit_report_repository import (
    FieldVisitReportRepository,
)
from app.repositories.project_apartment_repository import (
    ProjectApartmentRepository,
)
from app.repositories.project_repository import ProjectRepository
from app.repositories.quality_issue_repository import QualityIssueRepository
from app.schemas.project_supervision_dashboard import (
    ProjectSupervisionDashboardResponse,
    SupervisionProjectSummariesResponse,
    SupervisionProjectSummary,
    SupervisionTradeDetailResponse,
)
from app.schemas.qc_permissions import has_qc_permission
from app.schemas.quality_issue import QualityIssueListQuery


class ProjectSupervisionDashboardService:
    def __init__(
        self,
        *,
        project_repository: ProjectRepository | None = None,
        report_repository: FieldVisitReportRepository | None = None,
        issue_repository: QualityIssueRepository | None = None,
        apartment_repository: ProjectApartmentRepository | None = None,
    ) -> None:
        self.project_repository = project_repository or ProjectRepository()
        self.report_repository = report_repository or FieldVisitReportRepository()
        self.issue_repository = issue_repository or QualityIssueRepository()
        self.apartment_repository = (
            apartment_repository or ProjectApartmentRepository()
        )

    def build_dashboard_for_actor(
        self,
        *,
        organization_id: str,
        project_id: str,
        actor_role: str | None,
    ) -> ProjectSupervisionDashboardResponse:
        self._require_dashboard_permission(actor_role)
        return self.build_dashboard(
            organization_id=organization_id,
            project_id=project_id,
        )

    def build_trade_detail_for_actor(
        self,
        *,
        organization_id: str,
        project_id: str,
        trade_key: str,
        actor_role: str | None,
    ) -> SupervisionTradeDetailResponse:
        self._require_dashboard_permission(actor_role)
        return self.build_trade_detail(
            organization_id=organization_id,
            project_id=project_id,
            trade_key=trade_key,
        )

    def build_summaries_for_actor(
        self,
        *,
        organization_id: str,
        actor_role: str | None,
    ) -> SupervisionProjectSummariesResponse:
        self._require_dashboard_permission(actor_role)
        projects = self.project_repository.get_projects_by_organization(
            organization_id
        )
        items: list[SupervisionProjectSummary] = []

        for project in projects:
            project_id = str(project.get("id") or "").strip()
            if not project_id:
                continue

            try:
                dashboard = self.build_dashboard(
                    organization_id=organization_id,
                    project_id=project_id,
                )
            except NotFoundError:
                continue

            items.append(
                SupervisionProjectSummary(
                    project_id=project_id,
                    overall_status=dashboard.overall_status,
                    progress_percent=dashboard.kpis.progress_percent,
                )
            )

        return SupervisionProjectSummariesResponse(items=items)

    def build_dashboard(
        self,
        *,
        organization_id: str,
        project_id: str,
    ) -> ProjectSupervisionDashboardResponse:
        project, reports, issues, apartments = self._load_project_scope(
            organization_id=organization_id,
            project_id=project_id,
        )

        return aggregate_supervision_dashboard(
            project_id=project_id,
            project_name=str(project.get("project_name") or "").strip(),
            apartments=apartments,
            reports=reports,
            issues=issues,
        )

    def build_trade_detail(
        self,
        *,
        organization_id: str,
        project_id: str,
        trade_key: str,
    ) -> SupervisionTradeDetailResponse:
        project, reports, issues, apartments = self._load_project_scope(
            organization_id=organization_id,
            project_id=project_id,
        )

        detail = aggregate_supervision_trade_detail(
            project_id=project_id,
            project_name=str(project.get("project_name") or "").strip(),
            trade_key=trade_key,
            apartments=apartments,
            reports=reports,
            issues=issues,
        )
        if detail is None:
            raise NotFoundError(f"Trade {trade_key} not found for project {project_id}")

        return detail

    def _load_project_scope(
        self,
        *,
        organization_id: str,
        project_id: str,
    ) -> tuple[dict, list[dict], list[dict], list[dict]]:
        project = self.project_repository.get_project_by_id(project_id)
        if not project:
            raise NotFoundError(f"Project {project_id} not found")

        project_org_id = str(project.get("organization_id") or "").strip()
        if project_org_id and project_org_id != organization_id:
            raise NotFoundError(f"Project {project_id} not found")

        reports = self.report_repository.list_by_organization(
            organization_id,
            project_id=project_id,
            include_hidden=True,
        )
        issues = self.issue_repository.list_by_project(
            organization_id=organization_id,
            project_id=project_id,
            query=QualityIssueListQuery(limit=200, offset=0),
        )
        apartments = self.apartment_repository.list_by_project(project_id)

        return project, reports, issues, apartments

    @staticmethod
    def _require_dashboard_permission(actor_role: str | None) -> None:
        if not has_qc_permission(actor_role, "field_reports:read"):
            raise ForbiddenError("Missing field_reports:read permission")
        if not has_qc_permission(actor_role, "projects:read"):
            raise ForbiddenError("Missing projects:read permission")
