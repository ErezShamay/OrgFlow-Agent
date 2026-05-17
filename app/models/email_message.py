class EmailMessage:
    def __init__(
        self,
        message_id,
        subject,
        sender,
        body,
        attachments=None
    ):
        self.message_id = (
            message_id
        )

        self.subject = (
            subject
        )

        self.sender = (
            sender
        )

        self.body = (
            body
        )

        self.attachments = (
            attachments or []
        )