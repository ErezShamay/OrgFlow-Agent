from app.db.supabase_client import (
    supabase
)

from app.schemas.notification import (
    Notification
)


class NotificationRepository:

    def __init__(self):

        self.client = (
            supabase
        )

        self.table_name = (
            "notifications"
        )

    # ==========================================
    # CREATE
    # ==========================================

    def create_notification(
        self,
        notification: Notification
    ):

        payload = (
            notification.model_dump(
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

    def get_notifications(
        self,
        profile_id: str,
    ):

        response = (
            self.client
            .table(self.table_name)
            .select("*")
            .eq(
                "profile_id",
                profile_id
            )
            .order(
                "created_at",
                desc=True
            )
            .execute()
        )

        return response.data

    def get_unread_notifications(
        self,
        profile_id: str,
    ):

        response = (
            self.client
            .table(self.table_name)
            .select("*")
            .eq(
                "profile_id",
                profile_id
            )
            .eq(
                "is_read",
                False
            )
            .execute()
        )

        return response.data

    # ==========================================
    # UPDATE
    # ==========================================

    def mark_as_read(
        self,
        notification_id: str,
    ):

        response = (
            self.client
            .table(self.table_name)
            .update({
                "is_read": True
            })
            .eq(
                "id",
                notification_id
            )
            .execute()
        )

        return response.data[0]