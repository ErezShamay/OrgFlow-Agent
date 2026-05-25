from app.db.supabase_client import (
    supabase
)


class WeeklyReportRepository:

    def __init__(self):
        self.client = supabase

    def create_report(
        self,
        project_id,
        report_source,
        email_subject
    ):

        response = (
            self.client
            .table(
                "weekly_reports"
            )
            .insert({
                "project_id":
                    project_id,

                "report_source":
                    report_source,

                "email_subject":
                    email_subject
            })
            .execute()
        )

        return response.data[0]

    def get_all_reports(self):

        response = (
            self.client
            .table("weekly_reports")
            .select("*")
            .execute()
        )

        return response.data

    def get_reports_by_project(
        self,
        project_id: str
    ):

        response = (
            self.client
            .table("weekly_reports")
            .select("*")
            .eq(
                "project_id",
                project_id
            )
            .execute()
        )

        return response.data