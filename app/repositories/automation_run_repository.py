from app.db.supabase_client import (
    supabase
)

from app.schemas.automation_run import (
    AutomationRun
)


class AutomationRunRepository:

    def __init__(self):

        self.client = (
            supabase
        )

        self.table_name = (
            "automation_runs"
        )

    def create_run(
        self,
        run: AutomationRun,
    ):

        response = (
            self.client
            .table(self.table_name)
            .insert(
                run.model_dump(
                    exclude_none=True
                )
            )
            .execute()
        )

        return response.data[0]

    def update_run(
        self,
        run_id: str,
        payload: dict,
    ):

        response = (
            self.client
            .table(self.table_name)
            .update(payload)
            .eq(
                "id",
                run_id
            )
            .execute()
        )

        return response.data[0]