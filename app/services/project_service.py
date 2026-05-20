from app.repositories.project_repository import (
    ProjectRepository
)


class ProjectService:

    def __init__(self):

        self.project_repository = (
            ProjectRepository()
        )

    def create_project(
        self,
        project_name: str,
        supervisor_name: str,
        supervisor_email: str | None = None,
    ):

        return (
            self.project_repository
            .create_project(
                project_name=
                    project_name,

                supervisor_name=
                    supervisor_name,

                supervisor_email=
                    supervisor_email,
            )
        )