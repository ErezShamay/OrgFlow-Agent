from app.db.supabase_client import (
    supabase
)


class ProjectRepository:

    def __init__(self):

        self.client = (
            supabase
        )

    def create_project(
        self,
        project
    ):

        response = (
            self.client
            .table("projects")
            .insert({
                "project_name":
                    project.project_name,

                "supervisor_name":
                    project.supervisor_name,

                "supervisor_email":
                    project.supervisor_email,

                "organization_id":
                    project.organization_id,

                "status":
                    project.status,
            })
            .execute()
        )

        return response.data[0]

    def get_all_projects(
        self,
    ):

        response = (
            self.client
            .table("projects")
            .select("*")
            .execute()
        )

        return response.data

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

    def get_project_by_id(
        self,
        project_id: str
    ):

        response = (
            self.client
            .table("projects")
            .select("*")
            .eq(
                "id",
                project_id
            )
            .limit(1)
            .execute()
        )

        if not response.data:
            return None

        return response.data[0]