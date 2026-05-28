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
        from app.config.settings import settings


        class EmailService:
            def __init__(self):
                provider_name = settings.EMAIL_PROVIDER

                if provider_name == "microsoft":
                    self.provider = (
                        MicrosoftProvider()
                    )
                else:
                    self.provider = (
                        GmailProvider()
                    )
        return (
            self.provider
            .download_attachments(
                message_id
            )
        )