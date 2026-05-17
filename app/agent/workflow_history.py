from app.agent.workflow_store import WorkflowStore


class WorkflowHistory:
    def __init__(self):
        self.store = WorkflowStore()

    def add_run(
        self,
        workflow_type_or_result,
        user_request=None,
        result=None
    ):
        if (
            isinstance(
                workflow_type_or_result,
                dict
            )
            and user_request is None
            and result is None
        ):
            workflow_run = workflow_type_or_result

            return self.store.save(
                workflow_run
            )

        workflow_type = workflow_type_or_result

        workflow_run = {
            "workflow_type": workflow_type,
            "user_request": user_request,
            "status": result.get(
                "status",
                "UNKNOWN"
            ),
            "summary": result.get(
                "summary",
                ""
            ),
            "detected_intents": result.get(
                "detected_intents",
                []
            ),
            "actions": result.get(
                "actions",
                []
            )
        }

        return self.store.save(
            workflow_run
        )

    def get_runs(self):
        return self.store.get_all_workflow_runs()