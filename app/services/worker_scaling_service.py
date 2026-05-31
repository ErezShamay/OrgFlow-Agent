from __future__ import annotations

WORKER_SCALING_CONFIG = {
    "queue_name": "orgflow-automation",
    "min_workers": 1,
    "max_workers": 8,
    "target_queue_depth": 50,
    "scale_up_threshold": 100,
    "scale_down_threshold": 10,
    "worker_concurrency": 4,
}


class WorkerScalingService:
    def get_config(self) -> dict:
        return WORKER_SCALING_CONFIG

    def get_worker_status(self) -> dict:
        return {
            "active_workers": 2,
            "min_workers": WORKER_SCALING_CONFIG["min_workers"],
            "max_workers": WORKER_SCALING_CONFIG["max_workers"],
            "queue_depth": 35,
            "processing_rate_per_minute": 120,
            "autoscaling_enabled": True,
        }

    def simulate_scale_decision(
        self,
        *,
        queue_depth: int = 35,
        active_workers: int = 2,
    ) -> dict:
        action = "NONE"
        target = active_workers
        if queue_depth > WORKER_SCALING_CONFIG["scale_up_threshold"]:
            action = "SCALE_UP"
            target = min(
                active_workers + 1,
                WORKER_SCALING_CONFIG["max_workers"],
            )
        elif (
            queue_depth < WORKER_SCALING_CONFIG["scale_down_threshold"]
            and active_workers > WORKER_SCALING_CONFIG["min_workers"]
        ):
            action = "SCALE_DOWN"
            target = max(
                active_workers - 1,
                WORKER_SCALING_CONFIG["min_workers"],
            )

        return {
            "action": action,
            "current_workers": active_workers,
            "target_workers": target,
            "queue_depth": queue_depth,
        }
