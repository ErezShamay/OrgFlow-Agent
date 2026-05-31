from __future__ import annotations

AI_ANOMALY_DETECTION_CONFIG = {
    "detector_id": "orgflow_anomaly_v1",
    "sensitivity": "medium",
    "lookback_days": 30,
    "dimensions": ["actions", "reports", "ai_usage"],
}


class AiAnomalyDetectionService:
    def get_config(self) -> dict:
        return AI_ANOMALY_DETECTION_CONFIG

    def scan(self, *, metric: str = "actions", current_value: float = 120.0, baseline: float = 40.0) -> dict:
        deviation = abs(current_value - baseline) / max(baseline, 1)
        return {
            "metric": metric,
            "anomaly_detected": deviation >= 1.5,
            "deviation_ratio": round(deviation, 2),
        }

    def list_detectors(self) -> dict:
        detectors = ["spike", "drop", "seasonal_drift"]
        return {"detectors": detectors, "total": len(detectors)}

    def validate_setup(self) -> dict:
        return {
            "valid": True,
            "detectors_defined": self.list_detectors()["total"] >= 3,
        }
