from __future__ import annotations

LOGGING_CONFIG = {
    "provider": "structured_json",
    "aggregation": "loki",
    "retention_days": 30,
    "log_levels": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
    "fields": ["timestamp", "level", "message", "trace_id", "org_id"],
}


class CentralizedLoggingService:
    def get_config(self) -> dict:
        return LOGGING_CONFIG

    def get_log_streams(self) -> dict:
        streams = [
            {"name": "api", "source": "orgflow-api", "volume_mb_per_day": 250},
            {"name": "ui", "source": "orgflow-ui", "volume_mb_per_day": 80},
            {"name": "worker", "source": "orgflow-worker", "volume_mb_per_day": 120},
            {"name": "nginx", "source": "nginx", "volume_mb_per_day": 400},
        ]
        return {"streams": streams, "total": len(streams)}

    def validate_setup(self) -> dict:
        return {
            "valid": True,
            "structured_logging": LOGGING_CONFIG["provider"] == "structured_json",
            "trace_id_field": "trace_id" in LOGGING_CONFIG["fields"],
            "retention_days": LOGGING_CONFIG["retention_days"],
        }

    def search_logs(
        self,
        *,
        query: str = "",
        level: str | None = None,
        limit: int = 100,
    ) -> dict:
        sample = [
            {
                "timestamp": "2026-05-29T10:00:00Z",
                "level": "INFO",
                "message": "Request processed",
                "trace_id": "trace-abc123",
            },
        ]
        if level:
            sample = [entry for entry in sample if entry["level"] == level]
        return {
            "query": query,
            "level": level,
            "results": sample[:limit],
            "total": len(sample),
        }
