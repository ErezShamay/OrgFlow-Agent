from app.repositories.workflow_run_repository import (
    WorkflowRunRepository
)


class WorkflowStore:
    def __init__(self):
        self.repository = WorkflowRunRepository()

    def save_workflow_run(
        self,
        workflow_type: str,
        user_request: str,
        status: str,
        summary: str,
        detected_intents: list,
        actions: list
    ):
        return self.repository.create_workflow_run(
            workflow_type=workflow_type,
            user_request=user_request,
            status=status,
            summary=summary,
            detected_intents=detected_intents,
            actions=actions
        )

    def save(
        self,
        workflow_run_or_id,
        workflow_run=None
    ):
        if (
            isinstance(workflow_run_or_id, dict)
            and workflow_run is None
        ):
            workflow_data = workflow_run_or_id
        else:
            workflow_data = workflow_run or {}

        return self.repository.create_workflow_run(
            workflow_type=workflow_data.get(
                "type",
                workflow_data.get(
                    "workflow_type",
                    "UNKNOWN"
                )
            ),
            user_request=workflow_data.get(
                "user_request",
                ""
            ),
            status=workflow_data.get(
                "status",
                "UNKNOWN"
            ),
            summary=workflow_data.get(
                "summary",
                ""
            ),
            detected_intents=workflow_data.get(
                "detected_intents",
                []
            ),
            actions=workflow_data.get(
                "actions",
                []
            )
        )

    def get_all_workflow_runs(self):
        return self.repository.get_all_workflow_runs()