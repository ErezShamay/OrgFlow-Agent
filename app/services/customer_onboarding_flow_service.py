from __future__ import annotations

CUSTOMER_ONBOARDING_CONFIG = {
    "flow_id": "enterprise_customer_v1",
    "owner_role": "CUSTOMER_SUCCESS",
    "sla_days": 30,
    "deliverables": ["kickoff", "data_migration", "training", "go_live"],
}


class CustomerOnboardingFlowService:
    def get_config(self) -> dict:
        return CUSTOMER_ONBOARDING_CONFIG

    def list_milestones(self) -> dict:
        milestones = [
            {"id": "kickoff", "day_target": 3, "owner": "csm"},
            {"id": "sso_setup", "day_target": 7, "owner": "engineering"},
            {"id": "data_migration", "day_target": 14, "owner": "csm"},
            {"id": "training", "day_target": 21, "owner": "csm"},
            {"id": "go_live", "day_target": 30, "owner": "csm"},
        ]
        return {"milestones": milestones, "total": len(milestones)}

    def evaluate_progress(self, *, completed_milestones: list[str]) -> dict:
        required = {"kickoff", "training", "go_live"}
        done = set(completed_milestones)
        return {
            "on_track": required.issubset(done),
            "completed": len(done),
            "total": self.list_milestones()["total"],
            "missing_required": sorted(required - done),
        }

    def validate_setup(self) -> dict:
        return {
            "valid": True,
            "flow_id": CUSTOMER_ONBOARDING_CONFIG["flow_id"],
            "milestones_defined": self.list_milestones()["total"] >= 4,
        }
