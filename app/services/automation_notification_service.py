from app.services.notification_service import (
    NotificationService
)

from app.repositories.workspace_activity_repository import (
    WorkspaceActivityRepository
)


class AutomationNotificationService:

    def __init__(self):

        self.notification_service = (
            NotificationService()
        )

    # ==========================================
    # SLA OVERDUE
    # ==========================================

    def send_sla_overdue_notification(
        self,
        action: dict,
    ):

        assigned_to = (
            action.get(
                "assigned_to"
            )
        )

        if not assigned_to:
            return

        self.notification_service.create_notification(

            profile_id=
                assigned_to,

            title=
                "חריגת SLA זוהתה",

            message=
                (
                    f"הפעולה "
                    f"'{action['title']}' "
                    f"חרגה מזמן הטיפול"
                ),

            notification_type=
                "SLA_OVERDUE",
        )

    # ==========================================
    # AUTO ESCALATION
    # ==========================================

    def send_auto_escalation_notification(
        self,
        escalation: dict,
    ):

        assigned_to = (
            escalation.get(
                "assigned_to"
            )
        )

        if not assigned_to:
            return

        self.notification_service.create_notification(

            profile_id=
                assigned_to,

            title=
                "נוצרה הסלמה אוטומטית",

            message=
                (
                    f"המערכת יצרה "
                    f"הסלמה חדשה עבור "
                    f"'{escalation['title']}'"
                ),

            notification_type=
                "AUTO_ESCALATION",
        )

    # ==========================================
    # CREATE ACTIVITY
    # ==========================================

    def create_automation_activity(
        self,
        project_id: str,
        title: str,
        description: str,
        activity_type: str,
    ):

        WorkspaceActivityRepository.create_activity(

            project_id=
                project_id,

            activity_type=
                activity_type,

            title=
                title,

            description=
                description,
        )