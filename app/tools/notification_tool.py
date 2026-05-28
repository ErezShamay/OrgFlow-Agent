from app.config.settings import settings

import resend

resend.api_key = settings.RESEND_API_KEY


class NotificationTool:
    def build_reminder_messages(
        self,
        missing_projects
    ):
        reminders = []

        for project in missing_projects:
            supervisor_name = (
                project.get(
                    "supervisor_name"
                )
            )

            supervisor_email = (
                project.get(
                    "supervisor_email"
                )
            )

            project_name = (
                project.get(
                    "project_name"
                )
            )

            reminders.append({
                "to":
                    supervisor_email,

                "subject":
                    f"תזכורת לשליחת "
                    f"דוח שבועי - "
                    f"{project_name}",

                "body":
                    (
                        f"שלום "
                        f"{supervisor_name},\n\n"

                        f"לפי המערכת, "
                        f"טרם התקבל "
                        f"דוח שבועי עבור "
                        f"פרויקט "
                        f"{project_name}.\n"

                        f"אנא שלח את "
                        f"הדוח בהקדם.\n\n"

                        f"תודה,\n"
                        f"OrgFlow Agent"
                    )
            })

        return reminders

    def send_reminders(
        self,
        reminders
    ):
        sent_notifications = []

        for reminder in reminders:
            to_email = (
                reminder["to"]
            )

            if not to_email:
                sent_notifications.append({
                    "to": None,
                    "status": "SKIPPED"
                })

                continue

            try:
                response = (
                    resend.Emails.send({
                        "from":
                            "OrgFlow <onboarding@resend.dev>",

                        "to":
                            [to_email],

                        "subject":
                            reminder["subject"],

                        "text":
                            reminder["body"]
                    })
                )

                sent_notifications.append({
                    "to":
                        to_email,

                    "status":
                        "SENT",

                    "response":
                        response
                })

            except Exception as e:
                sent_notifications.append({
                    "to":
                        to_email,

                    "status":
                        "FAILED",

                    "error":
                        str(e)
                })

        return sent_notifications