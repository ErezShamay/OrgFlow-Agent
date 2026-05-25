from app.db.supabase_client import (
    supabase
)


class OrganizationRepository:

    def __init__(self):

        self.client = supabase

    def get_all_organizations(self):

        organizations_response = (
            self.client
            .table("organizations")
            .select("*")
            .execute()
        )

        organizations = (
            organizations_response.data
        )

        for organization in organizations:

            projects_response = (
                self.client
                .table("projects")
                .select("*")
                .eq(
                    "organization_id",
                    organization["id"]
                )
                .execute()
            )

            organization["projects"] = (
                projects_response.data
            )

        return organizations