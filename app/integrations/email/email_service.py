import os

from dotenv import load_dotenv

from app.integrations.email.gmail_provider import (
    GmailProvider
)

from app.integrations.email.microsoft_provider import (
    MicrosoftProvider
)


load_dotenv()


class EmailService:
    def __init__(self):
        provider_name = os.getenv(
            "EMAIL_PROVIDER",
            "gmail"
        )

        if provider_name == "microsoft":
            self.provider = (
                MicrosoftProvider()
            )
        else:
            self.provider = (
                GmailProvider()
            )

    def send_email(
        self,
        to,
        subject,
        body
    ):
        return (
            self.provider
            .send_email(
                to=to,
                subject=subject,
                body=body
            )
        )

    def get_unread_messages(self):
        return (
            self.provider
            .get_unread_messages()
        )

    def download_attachments(
        self,
        message_id
    ):
        return (
            self.provider
            .download_attachments(
                message_id
            )
        )