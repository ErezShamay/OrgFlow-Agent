from typing import Any

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

    def build_critical_stale_issue_messages(
        self,
        digests,
    ):
        reminders = []

        for digest in digests:
            supervisor_email = digest.get("supervisor_email")
            supervisor_name = digest.get("supervisor_name") or "מפקח"
            issues = digest.get("issues") or []

            if not issues:
                continue

            lines = []
            for issue in issues:
                location = issue.get("location")
                trade = issue.get("trade")
                days_open = issue.get("days_open")
                detail_parts = [
                    part
                    for part in (
                        f"מיקום: {location}" if location else None,
                        f"מלאכה: {trade}" if trade else None,
                        f"פתוח {days_open} ימים" if days_open is not None else None,
                    )
                    if part
                ]
                detail_suffix = f" ({', '.join(detail_parts)})" if detail_parts else ""
                lines.append(
                    f"- {issue.get('project_name')}: "
                    f"{issue.get('title')}{detail_suffix}"
                )

            issue_count = len(issues)
            subject = (
                f"התראת ליקוי קריטי - {issue_count} ליקויים פתוחים מעל 7 ימים"
            )
            body = (
                f"שלום {supervisor_name},\n\n"
                f"לפי מערכת OrgFlow, יש {issue_count} ליקוי/ים קריטיים "
                f"פתוחים מעל 7 ימים:\n\n"
                f"{chr(10).join(lines)}\n\n"
                f"אנא טפלו בליקויים בהקדם או עדכנו סטטוס בדוח הביקור הבא.\n\n"
                f"תודה,\n"
                f"OrgFlow QC"
            )

            reminders.append(
                {
                    "to": supervisor_email,
                    "subject": subject,
                    "body": body,
                    "issues": issues,
                }
            )

        return reminders

    def build_open_report_reminder_messages(
        self,
        digests,
    ):
        reminders = []

        for digest in digests:
            supervisor_email = digest.get("supervisor_email")
            supervisor_name = digest.get("supervisor_name") or "מפקח"
            reports = digest.get("reports") or []

            if not reports:
                continue

            lines = []
            for report in reports:
                visit_date = report.get("visit_date")
                visit_type = report.get("visit_type")
                days_open = report.get("days_open")
                detail_parts = [
                    part
                    for part in (
                        f"תאריך ביקור: {visit_date}" if visit_date else None,
                        f"סוג: {visit_type}" if visit_type else None,
                        f"פתוח {days_open} ימים" if days_open is not None else None,
                    )
                    if part
                ]
                detail_suffix = f" ({', '.join(detail_parts)})" if detail_parts else ""
                lines.append(
                    f"- {report.get('project_name')}: "
                    f"דוח ביקור{detail_suffix}"
                )

            report_count = len(reports)
            subject = (
                f"תזכורת - {report_count} דוח/ות ביקור פתוחים מעל 3 ימים"
            )
            body = (
                f"שלום {supervisor_name},\n\n"
                f"לפי מערכת OrgFlow, יש {report_count} דוח/ות ביקור "
                f"במצב 'בעבודה' שלא נסגרו מעל 3 ימים:\n\n"
                f"{chr(10).join(lines)}\n\n"
                f"אנא סגרו את הדוח/ות בהקדם כדי שהליקויים ייכנסו ל-registry.\n\n"
                f"תודה,\n"
                f"OrgFlow QC"
            )

            reminders.append(
                {
                    "to": supervisor_email,
                    "subject": subject,
                    "body": body,
                    "reports": reports,
                }
            )

        return reminders

    def build_new_critical_issue_messages(
        self,
        digests: list[dict[str, Any]],
        *,
        report_id: str,
    ) -> list[dict[str, Any]]:
        reminders = []

        for digest in digests:
            supervisor_email = digest.get("supervisor_email")
            supervisor_name = digest.get("supervisor_name") or "מפקח"
            issues = digest.get("issues") or []

            if not issues:
                continue

            lines = []
            for issue in issues:
                location = issue.get("location")
                trade = issue.get("trade")
                detail_parts = [
                    part
                    for part in (
                        f"מיקום: {location}" if location else None,
                        f"מלאכה: {trade}" if trade else None,
                    )
                    if part
                ]
                detail_suffix = (
                    f" ({', '.join(detail_parts)})" if detail_parts else ""
                )
                lines.append(
                    f"- {issue.get('project_name')}: "
                    f"{issue.get('title')}{detail_suffix}"
                )

            issue_count = len(issues)
            subject = (
                f"ליקוי קריטי חדש מדוח ביקור - {issue_count} ליקוי/ים"
            )
            body = (
                f"שלום {supervisor_name},\n\n"
                f"בעקבות Finalize של דוח ביקור ({report_id}), "
                f"זוהו {issue_count} ליקוי/ים קריטיים חדשים:\n\n"
                f"{chr(10).join(lines)}\n\n"
                f"אנא טפלו בליקויים בהקדם.\n\n"
                f"תודה,\n"
                f"OrgFlow QC"
            )

            reminders.append(
                {
                    "to": supervisor_email,
                    "subject": subject,
                    "body": body,
                    "issues": issues,
                }
            )

        return reminders

    def build_draft_contractor_issue_messages(
        self,
        digests: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Heads-up email when a draft defect is recorded (L3 — not portal-visible)."""
        reminders: list[dict[str, Any]] = []

        for digest in digests:
            contractor_email = (digest.get("contractor_email") or "").strip()
            if not contractor_email:
                continue

            contractor_name = (
                digest.get("contractor_name") or "קבלן"
            ).strip()
            project_name = (
                digest.get("project_name") or "הפרויקט"
            ).strip()
            issue_title = str(digest.get("issue_title") or "ליקוי").strip()
            trade = str(digest.get("trade") or "").strip()
            location = str(digest.get("location") or "").strip()

            detail_parts = [
                part
                for part in (
                    f"מלאכה: {trade}" if trade else None,
                    f"מיקום: {location}" if location else None,
                )
                if part
            ]
            detail_suffix = (
                f" ({', '.join(detail_parts)})" if detail_parts else ""
            )

            subject = f"ליקוי חדש נרשם בדוח פיקוח - {project_name}"
            body = (
                f"שלום {contractor_name},\n\n"
                f"נרשם ליקוי חדש בדוח פיקוח בפרויקט {project_name}:\n"
                f"- {issue_title}{detail_suffix}\n\n"
                "הליקוי יופיע במערכת לאחר פרסום הדוח.\n\n"
                "תודה,\n"
                "OrgFlow"
            )

            reminders.append(
                {
                    "to": contractor_email,
                    "subject": subject,
                    "body": body,
                    "issue_id": digest.get("issue_id"),
                    "report_id": digest.get("report_id"),
                }
            )

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