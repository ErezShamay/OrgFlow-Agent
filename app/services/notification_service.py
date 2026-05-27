from app.schemas.notification import (
    Notification
)

from app.repositories.notification_repository import (
    NotificationRepository
)


class NotificationService:

    def __init__(self):

        self.repository = (
            NotificationRepository()
        )

    # ==========================================
    # CREATE
    # ==========================================

    def create_notification(
        self,
        profile_id: str,
        title: str,
        message: str,
        notification_type: str,
    ):

        return (
            self.repository
            .create_notification(

                Notification(

                    profile_id=
                        profile_id,

                    title=
                        title,

                    message=
                        message,

                    notification_type=
                        notification_type,
                )
            )
        )

    # ==========================================
    # GETTERS
    # ==========================================

    def get_notifications(
        self,
        profile_id: str,
    ):

        return (
            self.repository
            .get_notifications(
                profile_id
            )
        )

    def get_unread_notifications(
        self,
        profile_id: str,
    ):

        return (
            self.repository
            .get_unread_notifications(
                profile_id
            )
        )

    # ==========================================
    # UPDATE
    # ==========================================

    def mark_as_read(
        self,
        notification_id: str,
    ):

        return (
            self.repository
            .mark_as_read(
                notification_id
            )
        )