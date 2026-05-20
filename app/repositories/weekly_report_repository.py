from app.db.supabase_client import (
    SupabaseClient
)


class WeeklyReportRepository:

    def __init__(self):

        self.client = (
            SupabaseClient
            .get_client()
        )

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