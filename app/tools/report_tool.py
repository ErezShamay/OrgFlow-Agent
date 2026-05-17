class ReportTool:
    def __init__(self):
        pass

    def get_weekly_reports(self):
        return [
            {
                "project_name":
                    "מגדלי הצפון",

                "submitted":
                    True
            },
            {
                "project_name":
                    "פארק הים",

                "submitted":
                    True
            }
        ]

    def find_missing_reports(
        self,
        active_projects,
        weekly_reports
    ):
        submitted_projects = []

        for report in weekly_reports:
            if report.get("submitted"):
                submitted_projects.append(
                    report["project_name"]
                )

        missing_projects = []

        for project in active_projects:
            if (
                project["project_name"]
                not in submitted_projects
            ):
                missing_projects.append(
                    project
                )

        return missing_projects

    def get_latest_report_by_project_id(
        self,
        project_id: str
    ):
        return {
            "id":
                "mock-report-id",

            "project_id":
                project_id,

            "report_date":
                "2026-05-17",

            "summary":
                "Weekly progress report",

            "status":
                "SUBMITTED"
        }

    def get_latest_report(
        self,
        project_name: str
    ):
        return {
            "project_name":
                project_name,

            "report_date":
                "2026-05-17",

            "summary":
                "Weekly progress report",

            "status":
                "SUBMITTED"
        }