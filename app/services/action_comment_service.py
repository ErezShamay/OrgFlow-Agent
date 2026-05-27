from app.schemas.action_comment import (
    ActionComment
)

from app.repositories.action_comment_repository import (
    ActionCommentRepository
)

from app.repositories.workspace_activity_repository import (
    WorkspaceActivityRepository
)

from app.repositories.operational_action_repository import (
    OperationalActionRepository
)


class ActionCommentService:

    def __init__(self):

        self.repository = (
            ActionCommentRepository()
        )

        self.action_repository = (
            OperationalActionRepository()
        )

    # ==========================================
    # CREATE
    # ==========================================

    def create_comment(
        self,
        action_id: str,
        comment: str,
        created_by: str,
    ):

        created_comment = (
            self.repository
            .create_comment(

                ActionComment(

                    action_id=
                        action_id,

                    comment=
                        comment,

                    created_by=
                        created_by,
                )
            )
        )

        action = (
            self.action_repository
            .get_action_by_id(
                action_id
            )
        )

        if action:

            WorkspaceActivityRepository.create_activity(

                project_id=
                    action["project_id"],

                activity_type=
                    "ACTION_COMMENT",

                title=
                    "נוספה הערה לפעולה",

                description=
                    f"{action['title']}",
            )

        return created_comment

    # ==========================================
    # GETTERS
    # ==========================================

    def get_comments_by_action(
        self,
        action_id: str,
    ):

        return (
            self.repository
            .get_comments_by_action(
                action_id
            )
        )