from __future__ import annotations

ONBOARDING_CONFIG = {
    "flow_id": "orgflow_signup_v1",
    "steps": ["welcome", "organization", "invite_team", "first_project", "tour"],
    "completion_redirect": "/projects",
    "estimated_minutes": 8,
}


class OnboardingFlowService:
    def get_config(self) -> dict:
        return ONBOARDING_CONFIG

    def list_steps(self) -> dict:
        steps = [
            {"id": "welcome", "title": "Welcome", "skippable": False},
            {"id": "organization", "title": "Create organization", "skippable": False},
            {"id": "invite_team", "title": "Invite teammates", "skippable": True},
            {"id": "first_project", "title": "Create first project", "skippable": False},
            {"id": "tour", "title": "Product tour", "skippable": True},
        ]
        return {"steps": steps, "total": len(steps)}

    def evaluate_progress(self, *, completed_steps: list[str]) -> dict:
        required = {"welcome", "organization", "first_project"}
        done = set(completed_steps)
        return {
            "completed_count": len(done),
            "total_steps": len(ONBOARDING_CONFIG["steps"]),
            "complete": required.issubset(done),
            "missing_required": sorted(required - done),
        }

    def validate_setup(self) -> dict:
        return {
            "valid": True,
            "flow_id": ONBOARDING_CONFIG["flow_id"],
            "steps_configured": self.list_steps()["total"] >= 4,
        }
