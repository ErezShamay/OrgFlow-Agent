from app.db.supabase_client import (
    supabase,
)
from app.repositories.finding_repository import (
    FindingRepository,
)
from app.repositories.project_repository import (
    ProjectRepository,
)


class TenantScopeService:

    def __init__(self):
        self.project_repository = ProjectRepository()
        self.finding_repository = FindingRepository()

    def get_organization_scoped_project(
        self,
        project_id: str,
        organization_id: str,
    ) -> dict | None:
        project = (
            self.project_repository
            .get_project_by_id(project_id)
        )

        if not project:
            return None

        if str(project.get("organization_id") or "") != organization_id:
            return None

        return project

    def get_organization_project_ids(
        self,
        organization_id: str,
    ) -> list[str]:
        projects = (
            self.project_repository
            .get_projects_by_organization(
                organization_id
            )
        )

        return [
            project["id"]
            for project in projects
            if project.get("id")
        ]

    def resolve_project_id_for_finding(
        self,
        finding_id: str | None,
    ) -> str | None:
        if not finding_id:
            return None

        finding = (
            self.finding_repository
            .get_finding_by_id(finding_id)
        )

        if not finding:
            return None

        report_id = finding.get("report_id")

        if not report_id:
            return None

        response = (
            supabase
            .table("reports")
            .select("project_id")
            .eq(
                "id",
                report_id,
            )
            .limit(1)
            .execute()
        )

        if not response.data:
            return None

        return response.data[0].get("project_id")

    def action_belongs_to_organization(
        self,
        action: dict,
        organization_id: str,
        project_ids: set[str],
    ) -> bool:
        action_org = action.get("organization_id")

        if (
            action_org
            and action_org != organization_id
        ):
            return False

        project_id = action.get("project_id")

        if project_id:
            return project_id in project_ids

        interpretation_id = action.get(
            "interpretation_id"
        )

        if not interpretation_id:
            return False

        from app.repositories.ai_interpretation_repository import (
            AIInterpretationRepository,
        )

        interpretation = (
            AIInterpretationRepository()
            .get_review_by_id(
                interpretation_id
            )
        )

        if not interpretation:
            return False

        resolved_project_id = (
            self.resolve_project_id_for_finding(
                interpretation.get("finding_id")
            )
        )

        return (
            resolved_project_id in project_ids
            if resolved_project_id
            else False
        )

    def review_belongs_to_organization(
        self,
        review: dict,
        project_ids: set[str],
    ) -> bool:
        resolved_project_id = (
            self.resolve_project_id_for_finding(
                review.get("finding_id")
            )
        )

        return (
            resolved_project_id in project_ids
            if resolved_project_id
            else False
        )
