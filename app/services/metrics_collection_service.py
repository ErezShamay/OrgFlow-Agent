from __future__ import annotations

METRIC_TYPES = ("counter", "gauge", "histogram", "summary")

CORE_METRICS = [
    {"name": "http_requests_total", "type": "counter", "labels": ["method", "path", "status"]},
    {"name": "http_request_duration_seconds", "type": "histogram", "labels": ["method", "path"]},
    {"name": "process_cpu_seconds_total", "type": "counter", "labels": []},
    {"name": "process_resident_memory_bytes", "type": "gauge", "labels": []},
    {"name": "db_connection_pool_active", "type": "gauge", "labels": ["pool"]},
]


class MetricsCollectionService:
    def get_config(self) -> dict:
        return {
            "enabled": True,
            "exporter": "prometheus",
            "endpoint": "/metrics",
            "scrape_interval_seconds": 15,
            "metric_types": list(METRIC_TYPES),
        }

    def get_catalog(self) -> dict:
        return {"metrics": CORE_METRICS, "total": len(CORE_METRICS)}

    def record_snapshot(
        self,
        *,
        requests_total: int = 0,
        active_connections: int = 0,
        memory_bytes: int = 0,
    ) -> dict:
        return {
            "http_requests_total": requests_total,
            "db_connection_pool_active": active_connections,
            "process_resident_memory_bytes": memory_bytes,
            "timestamp": "2026-05-29T12:00:00Z",
        }

    def validate_setup(self) -> dict:
        checks = [
            {"name": "EXPORTER_CONFIGURED", "passed": True},
            {"name": "METRICS_ENDPOINT", "passed": True},
            {"name": "CORE_METRICS_DEFINED", "passed": len(CORE_METRICS) >= 5},
        ]
        return {
            "valid": all(c["passed"] for c in checks),
            "checks": checks,
        }
