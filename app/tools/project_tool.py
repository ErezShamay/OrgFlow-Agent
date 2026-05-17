from app.repositories.project_repository import (
    ProjectRepository
)


class ProjectTool:
    def __init__(self):
        self.repository = (
            ProjectRepository()
        )

    def find_project_by_name(
        self,
        project_name: str
    ):
        projects = (
            self.repository
            .find_by_name(
                project_name
            )
        )

        if not projects:
            return {
                "match_status":
                    "NOT_FOUND",

                "project": None,

                "projects": []
            }

        if len(projects) == 1:
            return {
                "match_status":
                    "EXACT_MATCH",

                "project":
                    projects[0],

                "projects":
                    projects
            }

        return {
            "match_status":
                "MULTIPLE_MATCHES",

            "project":
                projects[0],

            "projects":
                projects
        }

    def get_all_projects(self):
        return (
            self.repository
            .get_all_projects()
        )

    # backward compatibility
    def get_active_projects(self):
        projects = (
            self.repository
            .get_all_projects()
        )

        active_projects = []

        for project in projects:
            if (
                project.get("status")
                == "ACTIVE"
            ):
                active_projects.append(
                    project
                )

        return active_projects