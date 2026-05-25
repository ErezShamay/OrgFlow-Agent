from app.db.supabase_client import supabase


class WorkflowRunRepository:
    def __init__(self):
        self.client = supabase

    def create_workflow_run(
        self,
        workflow_type: str,
        user_request: str,
        status: str,
        summary: str,
        detected_intents: list,
        actions: list
    ):
        response = (
            self.client
            .table("workflow_runs")
            .insert({
                "workflow_type": workflow_type,
                "user_request": user_request,
                "status": status,
                "summary": summary,
                "detected_intents": detected_intents,
                "actions": actions
            })
            .execute()
        )

        return response.data

    def get_all_workflow_runs(self):
        response = (
            self.client
            .table("workflow_runs")
            .select("*")
            .order("created_at", desc=True)
            .execute()
        )

        return response.data