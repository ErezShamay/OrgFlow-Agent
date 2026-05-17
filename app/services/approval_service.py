from app.repositories.approval_repository import (
    ApprovalRepository
)

from app.tools.notification_tool import (
    NotificationTool
)


class ApprovalService:
    def __init__(self):
        self.repository = ApprovalRepository()

        self.notification_tool = (
            NotificationTool()
        )

    def create_request(
        self,
        workflow_type: str,
        payload: dict
    ):
        return (
            self.repository
            .create_approval_request(
                workflow_type=
                workflow_type,

                payload=payload
            )
        )

    def approve(
        self,
        approval_id: int
    ):
        approval_request = (
            self.repository
            .get_approval_request(
                approval_id
            )
        )

        if not approval_request:
            return {
                "status": "FAILED",
                "summary":
                    "Approval request "
                    "not found."
            }

        updated_request = (
            self.repository
            .approve_request(
                approval_id
            )
        )

        workflow_type = (
            approval_request
            ["workflow_type"]
        )

        payload = (
            approval_request
            ["payload"]
        )

        execution_result = None

        if workflow_type == "SEND_REMINDERS":
            reminders = (
                payload["reminders"]
            )

            execution_result = (
                self.notification_tool
                .send_reminders(
                    reminders
                )
            )

        return {
            "status": "SUCCESS",

            "approval_request":
                updated_request,

            "execution_result":
                execution_result
        }

    def get_request(
        self,
        approval_id: int
    ):
        return (
            self.repository
            .get_approval_request(
                approval_id
            )
        )