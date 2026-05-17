from app.integrations.email.base_provider import (
    BaseEmailProvider
)


class MicrosoftProvider(
    BaseEmailProvider
):
    def get_unread_messages(self):
        return []

    def send_email(
        self,
        to,
        subject,
        body
    ):
        return {
            "status": "SENT",
            "provider": "microsoft"
        }

    def download_attachments(
        self,
        message_id
    ):
        return []