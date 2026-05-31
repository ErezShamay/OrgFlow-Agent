from __future__ import annotations

BETA_CONFIG = {
    "program_id": "orgflow_beta_2026",
    "invite_only": True,
    "feedback_channel": "in_app_survey",
    "max_participants": 100,
}


class BetaTestingFlowService:
    def get_config(self) -> dict:
        return BETA_CONFIG

    def list_stages(self) -> dict:
        stages = [
            {"id": "application", "label": "Apply for beta"},
            {"id": "approval", "label": "Review application"},
            {"id": "invite", "label": "Send invite"},
            {"id": "onboarding", "label": "Beta onboarding"},
            {"id": "feedback", "label": "Collect feedback"},
        ]
        return {"stages": stages, "total": len(stages)}

    def evaluate_enrollment(
        self,
        *,
        current_participants: int,
        approved: bool,
    ) -> dict:
        capacity = current_participants < BETA_CONFIG["max_participants"]
        return {
            "can_enroll": approved and capacity,
            "approved": approved,
            "capacity_available": capacity,
            "current_participants": current_participants,
            "max_participants": BETA_CONFIG["max_participants"],
        }

    def validate_setup(self) -> dict:
        return {
            "valid": True,
            "program_id": BETA_CONFIG["program_id"],
            "stages_defined": self.list_stages()["total"] >= 4,
        }
