from app.db.supabase_client import (
    supabase
)

from app.schemas.action_comment import (
    ActionComment
)


class ActionCommentRepository:

    def __init__(self):

        self.client = (
            supabase
        )

        self.table_name = (
            "action_comments"
        )

    # ==========================================
    # CREATE
    # ==========================================

    def create_comment(
        self,
        comment: ActionComment
    ):

        payload = (
            comment.model_dump(
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

    # ==========================================
    # GETTERS
    # ==========================================

    def get_comments_by_action(
        self,
        action_id: str
    ):

        response = (
            self.client
            .table(self.table_name)
            .select("*")
            .eq(
                "action_id",
                action_id
            )
            .order(
                "created_at",
                desc=False
            )
            .execute()
        )

        return response.data