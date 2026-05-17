from app.db.supabase_client import SupabaseClient


class ReportRepository:
    def __init__(self):
        self.client = SupabaseClient.get_client()

    def create_report(
        self,
        project_id: int,
        file_name: str,
        received_date: str,
        status: str = "RECEIVED"
    ):
        response = (
            self.client
            .table("reports")
            .insert({
                "project_id": project_id,
                "file_name": file_name,
                "received_date": received_date,
                "status": status
            })
            .execute()
        )

        return response.data

    def get_all_reports(self):
        response = (
            self.client
            .table("reports")
            .select("*")
            .execute()
        )

        return response.data

    def get_latest_report_by_project_id(
        self,
        project_id: int
    ):
        response = (
            self.client
            .table("reports")
            .select("*")
            .eq("project_id", project_id)
            .order("received_date", desc=True)
            .limit(1)
            .execute()
        )

        if not response.data:
            return None

        return response.data[0]