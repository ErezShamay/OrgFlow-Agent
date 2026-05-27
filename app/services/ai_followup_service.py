from datetime import (
    datetime,
    timedelta,
    timezone,
)

from app.repositories.operational_action_repository import (
    OperationalActionRepository
)

from app.services.automation_notification_service import (
    AutomationNotificationService
)


class AIFollowupService:

    def __init__(self):

        self.repository = (
            OperationalActionRepository()
        )

        self.automation_notifications = (
            AutomationNotificationService()
        )

    # ==========================================
    # MAIN LOOP
    # ==========================================

    def run_followup_cycle(
        self,
    ):

        print(
            "[AI_FOLLOWUP] Starting follow-up cycle"
        )

        actions = (
            self.repository
            .get_open_actions()
        )

        for action in actions:

            try:

                self.process_action(
                    action
                )

            except Exception as error:

                print(
                    "[AI_FOLLOWUP] Failed processing:",
                    action.get("id"),
                    str(error),
                )

        print(
            "[AI_FOLLOWUP] Follow-up cycle completed"
        )

    # ==========================================
    # PROCESS ACTION
    # ==========================================

    def process_action(
        self,
        action: dict,
    ):

        created_at = (
            action.get(
                "created_at"
            )
        )

        if not created_at:
            return

        created_at = (
            datetime.fromisoformat(
                created_at.replace(
                    "Z",
                    "+00:00"
                )
            )
        )

        now = (
            datetime.now(
                timezone.utc
            )
        )

        age = (
            now - created_at
        )

        # ======================================
        # FOLLOW-UP CONDITIONS
        # ======================================

        should_followup = (

            action.get(
                "status"
            ) == "OPEN"

            and

            age > timedelta(
                hours=24
            )
        )

        if not should_followup:
            return

        self.create_followup(
            action
        )

    # ==========================================
    # CREATE FOLLOW-UP
    # ==========================================

    def create_followup(
        self,
        action: dict,
    ):

        assigned_to = (
            action.get(
                "assigned_to"
            )
        )

        # ======================================
        # NOTIFICATION
        # ======================================

        if assigned_to:

            self.automation_notifications.notification_service.create_notification(

                profile_id=
                    assigned_to,

                title=
                    "AI Follow-Up",

                message=
                    (
                        f"הפעולה "
                        f"'{action['title']}' "
                        f"עדיין פתוחה ודורשת טיפול"
                    ),

                notification_type=
                    "AI_FOLLOWUP",
            )

        # ======================================
        # ACTIVITY
        # ======================================

        self.automation_notifications.create_automation_activity(

            project_id=
                action["project_id"],

            activity_type=
                "AI_FOLLOWUP",

            title=
                "AI ביצע Follow-Up",

            description=
                (
                    f"AI זיהה שהפעולה "
                    f"'{action['title']}' "
                    f"עדיין פתוחה"
                ),
        )

        print(
            "[AI_FOLLOWUP] Follow-up created:",
            action["id"]
        )