from app.db.supabase_client import (
    get_supabase_client
)

from app.schemas.finding import Finding


class FindingRepository:

    def __init__(self):

        self.client = (
            get_supabase_client()
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

    def create_findings(
        self,
        findings: list[Finding]
    ):

        created_findings = []

        for finding in findings:

            created_finding = (
                self.create_finding(
                    finding
                )
            )

            created_findings.append(
                created_finding
            )

        return created_findings