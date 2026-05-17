from app.integrations.email.email_service import (
    EmailService
)


class InboxService:
    def __init__(self):
        self.email_service = (
            EmailService()
        )

    def get_unread_messages(self):
        return (
            self.email_service
            .get_unread_messages()
        )