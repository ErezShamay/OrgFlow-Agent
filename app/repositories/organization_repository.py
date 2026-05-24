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

        response = (
            self.client
            .table("organizations")
            .select("""
                *,
                projects(*)
            """)
            .execute()
        )

        return response.data