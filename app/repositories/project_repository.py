from app.db.supabase_client import (
    SupabaseClient
)


class ProjectRepository:

    def __init__(self):

        self.client = (
            SupabaseClient
            .get_client()
        )

    def create_project(
        self,
        project_name: str,
        supervisor_name: str,
        supervisor_email: str = None
    ):

        existing = (
            self.client
            .table("projects")
            .select("*")
            .eq(
                "project_name",
                project_name
            )
            .limit(1)
            .execute()
        )

        if existing.data:
            return existing.data[0]

        response = (
            self.client
            .table("projects")
            .insert({
                "project_name":
                    project_name,

                "supervisor_name":
                    supervisor_name,

                "supervisor_email":
                    supervisor_email,

                "status":
                    "ACTIVE"
            })
            .execute()
        )

        return response.data[0]

    def get_projects_by_organization(
        self,
        organization_id: str
    ):

        response = (
            self.client
            .table("projects")
            .select("*")
            .eq(
                "organization_id",
                organization_id
            )
            .execute()
        )

    return response.data

        response = (
            self.client
            .table("projects")
            .select("*")
            .execute()
        )

        return response.data

    def find_by_name(
        self,
        project_name: str
    ):

        normalized = (
            project_name
            .replace(
                "פרויקט",
                ""
            )
            .strip()
        )

        response = (
            self.client
            .table("projects")
            .select("*")
            .ilike(
                "project_name",
                f"%{normalized}%"
            )
            .execute()
        )

        return response.data

    # backward compatibility
    def find_project_by_name(
        self,
        project_name: str
    ):

        projects = (
            self.find_by_name(
                project_name
            )
        )

        if not projects:

            return {
                "match_status":
                    "NOT_FOUND",

                "projects":
                    []
            }

        return {
            "match_status":
                "EXACT_MATCH",

            "project":
                projects[0],

            "projects":
                projects
        }

        def get_project_by_id(
            self,
            project_id: str
        ):
            response = (
                self.client
                .table("projects")
                .select("*")
                .eq("id", project_id)
                .limit(1)
                .execute()
            )

            if not response.data:
                return None

            return response.data[0]