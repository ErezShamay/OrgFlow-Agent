from __future__ import annotations

AI_METRICS = [
    {"name": "ai_tokens_used_total", "type": "counter", "labels": ["provider", "model"]},
    {"name": "ai_request_duration_seconds", "type": "histogram", "labels": ["provider"]},
    {"name": "ai_request_errors_total", "type": "counter", "labels": ["provider", "error_code"]},
    {"name": "ai_cost_usd_total", "type": "counter", "labels": ["provider", "model"]},
    {"name": "ai_cache_hits_total", "type": "counter", "labels": ["provider"]},
]


class AiMetricsService:
    def get_config(self) -> dict:
        return {
            "enabled": True,
            "providers": ["openai", "anthropic", "gemini"],
            "track_tokens": True,
            "track_cost": True,
            "track_latency": True,
        }

    def get_metrics_catalog(self) -> dict:
        return {"metrics": AI_METRICS, "total": len(AI_METRICS)}

    def get_snapshot(
        self,
        *,
        tokens_used: int = 0,
        avg_latency_ms: float = 0.0,
        error_rate: float = 0.0,
    ) -> dict:
        return {
            "tokens_used_total": tokens_used,
            "avg_latency_ms": avg_latency_ms,
            "error_rate_percent": error_rate,
            "providers_active": 3,
        }

    def validate_setup(self) -> dict:
        return {
            "valid": True,
            "metrics_defined": len(AI_METRICS) >= 5,
            "cost_tracking": True,
            "latency_tracking": True,
        }
