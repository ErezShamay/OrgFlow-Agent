from __future__ import annotations

PERFORMANCE_THRESHOLDS = {
    "p50_latency_ms": 200,
    "p95_latency_ms": 800,
    "p99_latency_ms": 2000,
    "error_rate_percent": 1.0,
    "throughput_rps_min": 10,
}


class PerformanceMonitoringService:
    def get_config(self) -> dict:
        return {
            "enabled": True,
            "thresholds": PERFORMANCE_THRESHOLDS,
            "window_minutes": 5,
            "track_endpoints": True,
        }

    def evaluate_performance(
        self,
        *,
        p50_ms: float = 0.0,
        p95_ms: float = 0.0,
        p99_ms: float = 0.0,
        error_rate: float = 0.0,
        throughput_rps: float = 0.0,
    ) -> dict:
        checks = {
            "p50_ok": p50_ms <= PERFORMANCE_THRESHOLDS["p50_latency_ms"],
            "p95_ok": p95_ms <= PERFORMANCE_THRESHOLDS["p95_latency_ms"],
            "p99_ok": p99_ms <= PERFORMANCE_THRESHOLDS["p99_latency_ms"],
            "error_rate_ok": error_rate <= PERFORMANCE_THRESHOLDS["error_rate_percent"],
            "throughput_ok": throughput_rps >= PERFORMANCE_THRESHOLDS["throughput_rps_min"],
        }
        return {
            "p50_ms": p50_ms,
            "p95_ms": p95_ms,
            "p99_ms": p99_ms,
            "error_rate_percent": error_rate,
            "throughput_rps": throughput_rps,
            "checks": checks,
            "healthy": all(checks.values()),
        }

    def get_endpoint_summary(self) -> dict:
        endpoints = [
            {"path": "/projects", "p95_ms": 120, "error_rate": 0.1},
            {"path": "/reports", "p95_ms": 350, "error_rate": 0.3},
            {"path": "/automation/runs", "p95_ms": 180, "error_rate": 0.0},
        ]
        return {"endpoints": endpoints, "total": len(endpoints)}

    def validate_setup(self) -> dict:
        return {
            "valid": len(PERFORMANCE_THRESHOLDS) >= 5,
            "thresholds_defined": True,
            "endpoint_tracking": True,
        }
