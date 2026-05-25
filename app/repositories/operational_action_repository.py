from app.db.supabase_client import (
    supabase
)

from app.schemas.operational_action import (
    OperationalAction
)


class OperationalActionRepository:

    def __init__(self):

        self.client = (
            supabase
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

    def get_open_actions_by_project(
        self,
        project_id: str
    ):

        response = (
            self.client
            .table(self.table_name)
            .select("*")
            .eq(
                "status",
                "OPEN"
            )
            .eq(
                "project_id",
                project_id
            )
            .execute()
        )

        return response.data
    
    def get_exceptions_by_project(
        self,
        project_id: str
    ):

        response = (
            self.client
            .table(self.table_name)
            .select("*")
            .eq(
                "status",
                "OPEN"
            )
            .eq(
                "action_type",
                "ESCALATION"
            )
            .eq(
                "project_id",
                project_id
            )
            .execute()
        )

        return response.data

def close_action(
    self,
    action_id: str
):

    response = (
        self.client
        .table(self.table_name)
        .update({
            "status":
                "CLOSED"
        })
        .eq(
            "id",
            action_id
        )
        .execute()
    )

    return response.data[0]