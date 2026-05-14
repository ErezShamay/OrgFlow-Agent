from app.agent.intent_detector import IntentDetector


class StepExecutor:
    def __init__(self, project_tool, report_tool, notification_tool):
        self.project_tool = project_tool
        self.report_tool = report_tool
        self.notification_tool = notification_tool

    def execute_check_missing_reports(self):
        active_projects = self.project_tool.get_active_projects()
        weekly_reports = self.report_tool.get_weekly_reports()

        missing_projects = self.report_tool.find_missing_reports(
            active_projects=active_projects,
            weekly_reports=weekly_reports
        )

        return {
            "step_type": IntentDetector.CHECK_MISSING_REPORTS,
            "status": "SUCCESS",
            "data": {
                "active_projects": active_projects,
                "weekly_reports": weekly_reports,
                "missing_projects": missing_projects
            },
            "actions": [
                "Loaded active projects",
                "Loaded weekly reports",
                "Compared active projects with weekly reports"
            ]
        }

    def execute_build_reminders(self, missing_projects):
        reminders = self.notification_tool.build_reminder_messages(
            missing_projects
        )

        return {
            "step_type": IntentDetector.SEND_REMINDERS,
            "status": "WAITING_FOR_CONFIRMATION",
            "data": {
                "reminders": reminders
            },
            "actions": [
                "Built reminder messages",
                "Waiting for user confirmation"
            ]
        }