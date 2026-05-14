class NotificationTool:
    def build_reminder_messages(self, missing_projects):
        reminders = []

        for project in missing_projects:
            supervisor_name = project.get("supervisor_name")
            supervisor_email = project.get("supervisor_email")
            project_name = project.get("project_name")

            reminders.append({
                "to": supervisor_email,
                "subject": f"תזכורת לשליחת דוח שבועי - {project_name}",
                "body": (
                    f"שלום {supervisor_name},\n\n"
                    f"לפי המערכת, טרם התקבל דוח שבועי עבור פרויקט {project_name}.\n"
                    f"אנא שלח את הדוח בהקדם.\n\n"
                    f"תודה,\n"
                    f"OrgFlow Agent"
                )
            })

        return reminders

    def send_reminders(self, reminders):
        sent_notifications = []

        for reminder in reminders:
            sent_notifications.append({
                "to": reminder["to"],
                "subject": reminder["subject"],
                "status": "SENT"
            })

        return sent_notifications