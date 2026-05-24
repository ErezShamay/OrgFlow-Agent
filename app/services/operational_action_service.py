from app.repositories.operational_action_repository import (
    OperationalActionRepository
)


class OperationalActionService:

    def __init__(self):

        self.repository = (
            OperationalActionRepository()
        )

    def get_open_actions(
        self
    ):

        return (
            self.repository
            .get_open_actions()
        )

    def get_escalations(
        self
    ):

        actions = (
            self.repository
            .get_open_actions()
        )

        escalations = []

        for action in actions:

            if (
                action[
                    "action_type"
                ]
                == "ESCALATION"
            ):

                escalations.append(
                    action
                )

        return escalations