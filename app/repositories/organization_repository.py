from app.db.supabase_client import (
    SupabaseClient
)


class OrganizationRepository:

    def __init__(self):

        self.client = (
            SupabaseClient
            .get_client()
        )

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

        result = []

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

            result.append({
                "id":
                    organization["id"],

                "organization_name":
                    organization[
                        "organization_name"
                    ],

                "contact_email":
                    organization[
                        "contact_email"
                    ],

                "projects":
                    projects_response.data
            })

        return result