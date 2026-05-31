from __future__ import annotations

SCALING_CONFIG = {
    "strategy": "horizontal_pod_autoscaler",
    "min_replicas": 2,
    "max_replicas": 10,
    "target_cpu_percent": 70,
    "target_memory_percent": 80,
    "scale_up_cooldown_seconds": 60,
    "scale_down_cooldown_seconds": 300,
}


class HorizontalScalingService:
    def get_config(self) -> dict:
        return SCALING_CONFIG

    def get_scaling_status(self) -> dict:
        return {
            "current_replicas": 3,
            "min_replicas": SCALING_CONFIG["min_replicas"],
            "max_replicas": SCALING_CONFIG["max_replicas"],
            "cpu_utilization_percent": 45.0,
            "memory_utilization_percent": 52.0,
            "autoscaling_enabled": True,
            "last_scale_event": None,
        }

    def simulate_scale_decision(
        self,
        *,
        cpu_percent: float = 45.0,
        memory_percent: float = 52.0,
        current_replicas: int = 3,
    ) -> dict:
        action = "NONE"
        target = current_replicas
        if cpu_percent > SCALING_CONFIG["target_cpu_percent"]:
            action = "SCALE_UP"
            target = min(current_replicas + 1, SCALING_CONFIG["max_replicas"])
        elif (
            cpu_percent < SCALING_CONFIG["target_cpu_percent"] * 0.5
            and current_replicas > SCALING_CONFIG["min_replicas"]
        ):
            action = "SCALE_DOWN"
            target = max(current_replicas - 1, SCALING_CONFIG["min_replicas"])

        return {
            "action": action,
            "current_replicas": current_replicas,
            "target_replicas": target,
            "cpu_percent": cpu_percent,
            "memory_percent": memory_percent,
        }
