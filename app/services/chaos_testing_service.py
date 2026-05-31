from __future__ import annotations

CHAOS_CONFIG = {
    "enabled_in_staging_only": True,
    "blast_radius": "single_pod",
    "auto_rollback": True,
}


class ChaosTestingService:
    def get_config(self) -> dict:
        return CHAOS_CONFIG

    def list_experiments(self) -> dict:
        experiments = [
            {"id": "kill_api_pod", "type": "pod_failure", "duration_seconds": 60},
            {"id": "db_latency_injection", "type": "latency", "duration_seconds": 120},
            {"id": "ai_provider_outage", "type": "dependency_failure", "duration_seconds": 90},
            {"id": "network_partition", "type": "network", "duration_seconds": 45},
        ]
        return {"experiments": experiments, "total": len(experiments)}

    def evaluate_experiment_safety(self, *, experiment_id: str) -> dict:
        experiments = {e["id"]: e for e in self.list_experiments()["experiments"]}
        experiment = experiments.get(experiment_id)
        if not experiment:
            return {"safe": False, "found": False}
        safe = (
            CHAOS_CONFIG["enabled_in_staging_only"]
            and experiment["duration_seconds"] <= 180
        )
        return {"found": True, "experiment_id": experiment_id, "safe": safe}

    def validate_setup(self) -> dict:
        return {
            "valid": True,
            "staging_only": CHAOS_CONFIG["enabled_in_staging_only"],
            "auto_rollback": CHAOS_CONFIG["auto_rollback"],
            "experiment_count": self.list_experiments()["total"] >= 3,
        }
