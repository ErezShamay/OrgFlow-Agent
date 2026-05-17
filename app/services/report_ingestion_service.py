from app.tools.project_tool import (
    ProjectTool
)

from app.repositories.weekly_report_repository import (
    WeeklyReportRepository
)


class ReportIngestionService:
    def __init__(self):
        self.project_tool = (
            ProjectTool()
        )

        self.report_repository = (
            WeeklyReportRepository()
        )

    def process_message(
        self,
        message
    ):
        subject = (
            message["subject"]
        )

        projects = (
            self.project_tool
            .get_all_projects()
        )

        matched_project = None

        for project in projects:
            project_name = (
                project[
                    "project_name"
                ]
            )

            if (
                project_name
                in subject
            ):
                matched_project = (
                    project
                )

                break

        if not matched_project:
            return {
                "status":
                    "NO_PROJECT_MATCH"
            }

        created_report = (
            self.report_repository
            .create_report(
                project_id=
                matched_project["id"],

                report_source=
                "EMAIL",

                email_subject=
                subject
            )
        )

        return {
            "status":
                "SUCCESS",

            "project":
                matched_project,

            "report":
                created_report
        }