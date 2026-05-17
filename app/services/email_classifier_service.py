class EmailClassifierService:
    def classify(
        self,
        message
    ):
        subject = (
            message["subject"]
            .lower()
        )

        body = (
            message["body"]
            .lower()
        )

        full_text = (
            f"{subject} {body}"
        )

        report_keywords = [
            "דוח",
            "weekly report",
            "report",
            "סיכום שבועי"
        ]

        has_report_keyword = (
            any(
                keyword in full_text
                for keyword in report_keywords
            )
        )

        has_attachment = (
            len(
                message.get(
                    "attachments",
                    []
                )
            ) > 0
        )

        if (
            has_report_keyword
            and
            has_attachment
        ):
            return {
                "classification":
                    "WEEKLY_REPORT",

                "confidence":
                    0.9
            }

        return {
            "classification":
                "UNKNOWN",

            "confidence":
                0.2
        }