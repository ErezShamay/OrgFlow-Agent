from __future__ import annotations

AUTONOMOUS_RECOVERY_AGENTS_CONFIG = {
    "agent_pool": "recovery_agents_v1",
    "max_auto_retries": 3,
    "allowed_actions": ["replay_job", "reset_circuit", "notify_owner"],
}


class AutonomousRecoveryAgentsService:
    def get_config(self) -> dict:
        return AUTONOMOUS_RECOVERY_AGENTS_CONFIG

    def triage_failure(self, *, failure_category: str = "transient", retry_count: int = 1) -> dict:
        auto = (
            failure_category == "transient"
            and retry_count < AUTONOMOUS_RECOVERY_AGENTS_CONFIG["max_auto_retries"]
        )
        return {
            "failure_category": failure_category,
            "auto_recovery_scheduled": auto,
            "recommended_action": "replay_job" if auto else "notify_owner",
        }

    def list_agents(self) -> dict:
        agents = ["dlq_replayer", "circuit_resetter", "escalation_notifier"]
        return {"agents": agents, "total": len(agents)}

    def validate_setup(self) -> dict:
        return {
            "valid": True,
            "agents_defined": self.list_agents()["total"] >= 3,
        }
