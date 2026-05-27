from app.db.supabase_client import (
    supabase
)


class ProfileRepository:

    def __init__(self):

        self.client = (
            supabase
        )

        self.table_name = (
            "profiles"
        )

    # ==========================================
    # GETTERS
    # ==========================================

    def get_profile_by_id(
        self,
        profile_id: str,
    ):

        response = (
            self.client
            .table(self.table_name)
            .select("*")
            .eq(
                "id",
                profile_id
            )
            .limit(1)
            .execute()
        )

        if not response.data:

            return None

        return response.data[0]