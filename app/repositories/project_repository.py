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
        project=None,
        project_name: str | None = None,
        supervisor_name: str | None = None,
        supervisor_email: str | None = None,
        organization_id: str | None = None,
        status: str = "ACTIVE",
    ):

        payload = {
            "project_name":
                (
                    project.project_name
                    if project
                    else project_name
                ),

            "supervisor_name":
                (
                    project.supervisor_name
                    if project
                    else supervisor_name
                ),

            "supervisor_email":
                (
                    project.supervisor_email
                    if project
                    else supervisor_email
                ),

            "organization_id":
                (
                    project.organization_id
                    if project
                    else organization_id
                ),

            "status":
                (
                    project.status
                    if project
                    else status
                ),
        }

        payload = {
            key: value
            for key, value
            in payload.items()
            if value is not None
        }

        response = (
            self._insert_project(
                payload
            )
        )

        return response.data[0]

    def _insert_project(
        self,
        payload: dict,
    ):

        try:

            return (
                self.client
                .table("projects")
                .insert(payload)
                .execute()
            )

        except Exception as error:

            if (
                "duplicate key value"
                not in str(error)
            ):

                raise

            existing_projects = (
                self.find_by_name(
                    payload[
                        "project_name"
                    ]
                )
            )

            class ExistingResponse:
                data = existing_projects

            return ExistingResponse()

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

    def find_by_name(
        self,
        project_name: str,
    ):

        response = (
            self.client
            .table("projects")
            .select("*")
            .ilike(
                "project_name",
                f"%{project_name}%"
            )
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
