from __future__ import annotations

RECOVERY_TEST_CONFIG = {
    "framework": "pytest",
    "domains": ["dead_letter", "circuit_breaker", "automation_replay"],
}


class RecoveryTestingService:
    def get_config(self) -> dict:
        return RECOVERY_TEST_CONFIG

    def list_scenarios(self) -> dict:
        scenarios = [
            {"id": "dlq_replay", "expected_outcome": "success"},
            {"id": "manual_recovery", "expected_outcome": "success"},
            {"id": "circuit_reopen", "expected_outcome": "degraded_then_healthy"},
            {"id": "auto_recovery_rule", "expected_outcome": "success"},
        ]
        return {"scenarios": scenarios, "total": len(scenarios)}

    def simulate_recovery(self, *, scenario_id: str) -> dict:
        scenarios = {s["id"]: s for s in self.list_scenarios()["scenarios"]}
        scenario = scenarios.get(scenario_id)
        if not scenario:
            return {"recovered": False, "scenario_id": scenario_id}
        return {
            "recovered": scenario["expected_outcome"] in ("success", "degraded_then_healthy"),
            "scenario_id": scenario_id,
            "outcome": scenario["expected_outcome"],
        }

    def validate_setup(self) -> dict:
        return {
            "valid": True,
            "domains": RECOVERY_TEST_CONFIG["domains"],
            "scenario_count": self.list_scenarios()["total"] >= 3,
        }
