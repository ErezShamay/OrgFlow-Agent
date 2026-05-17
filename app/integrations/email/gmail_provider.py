import os.path

from google.auth.transport.requests import (
    Request
)

from google.oauth2.credentials import (
    Credentials
)

from google_auth_oauthlib.flow import (
    InstalledAppFlow
)

from googleapiclient.discovery import (
    build
)

from app.integrations.email.base_provider import (
    BaseEmailProvider
)


SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send"
]


class GmailProvider(
    BaseEmailProvider
):
    def __init__(self):
        self.service = (
            self._authenticate()
        )

    def _authenticate(self):
        creds = None

        if os.path.exists("token.json"):
            creds = Credentials.from_authorized_user_file(
                "token.json",
                SCOPES
            )

        if (
            not creds
            or
            not creds.valid
        ):
            if (
                creds
                and
                creds.expired
                and
                creds.refresh_token
            ):
                creds.refresh(
                    Request()
                )

            else:
                flow = (
                    InstalledAppFlow
                    .from_client_secrets_file(
                        "credentials.json",
                        SCOPES
                    )
                )

                creds = (
                    flow.run_local_server(
                        port=0
                    )
                )

            with open(
                "token.json",
                "w"
            ) as token:
                token.write(
                    creds.to_json()
                )

        return build(
            "gmail",
            "v1",
            credentials=creds
        )

    def get_unread_messages(self):
        response = (
            self.service.users()
            .messages()
            .list(
                userId="me",
                labelIds=["UNREAD"]
            )
            .execute()
        )

        messages = (
            response.get(
                "messages",
                []
            )
        )

        return messages

    def send_email(
        self,
        to,
        subject,
        body
    ):
        import base64

        from email.mime.text import (
            MIMEText
        )

        message = MIMEText(body)

        message["to"] = to

        message["subject"] = (
            subject
        )

        raw_message = (
            base64.urlsafe_b64encode(
                message
                .as_bytes()
            )
            .decode()
        )

        send_result = (
            self.service.users()
            .messages()
            .send(
                userId="me",
                body={
                    "raw":
                        raw_message
                }
            )
            .execute()
        )

        return {
            "status":
                "SENT",

            "provider":
                "gmail",

            "message_id":
                send_result["id"]
        }

    def download_attachments(
        self,
        message_id
    ):
        return []