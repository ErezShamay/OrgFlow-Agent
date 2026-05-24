from app.db.supabase_client import (
    SupabaseClient
)

from app.schemas.finding import (
    Finding
)


class FindingRepository:

    def __init__(self):

        self.client = (
            SupabaseClient
            .get_client()
        )

        self.table_name = (
            "findings"
        )

    def create_finding(
        self,
        finding: Finding
    ):

        payload = (
            finding.model_dump(
                exclude_none=True
            )
        )

        response = (
            self.client
            .table(self.table_name)
            .insert(payload)
            .execute()
        )

        return response.data[0]

    def get_finding_by_id(
        self,
        finding_id: str
    ):

        response = (
            self.client
            .table(self.table_name)
            .select("*")
            .eq(
                "id",
                finding_id
            )
            .limit(1)
            .execute()
        )

        if not response.data:
            return None

        return response.data[0]

    def get_findings_by_project(
        self,
        project_id: str
    ):

        response = (
            self.client
            .table(self.table_name)
            .select("*")
            .eq(
                "project_id",
                project_id
            )
            .execute()
        )

        return response.data

    def get_findings_by_type(
        self,
        finding_type: str
    ):

        response = (
            self.client
            .table(self.table_name)
            .select("*")
            .eq(
                "finding_type",
                finding_type
            )
            .execute()
        )

        return response.data

    def get_findings_by_severity(
        self,
        severity: str
    ):

        response = (
            self.client
            .table(self.table_name)
            .select("*")
            .eq(
                "severity",
                severity
            )
            .execute()
        )

        return response.data

    def get_open_findings(
        self
    ):

        response = (
            self.client
            .table(self.table_name)
            .select("*")
            .eq(
                "status",
                "detected"
            )
            .execute()
        )

        return response.data