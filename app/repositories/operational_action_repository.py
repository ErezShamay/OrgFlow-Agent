from app.db.supabase_client import (
    SupabaseClient
)

from app.schemas.operational_action import (
    OperationalAction
)


class OperationalActionRepository:

    def __init__(self):

        self.client = (
            SupabaseClient
            .get_client()
        )

        self.table_name = (
            "operational_actions"
        )

    def create_action(
        self,
        action: OperationalAction
    ):

        payload = (
            action.model_dump(
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

    def get_open_actions(
        self
    ):

        response = (
            self.client
            .table(self.table_name)
            .select("*")
            .eq(
                "status",
                "OPEN"
            )
            .execute()
        )

        return response.data