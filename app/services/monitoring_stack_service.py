from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROMETHEUS_CONF = PROJECT_ROOT / "deploy/prometheus/prometheus.yml"

MONITORING_COMPONENTS = [
    {"name": "prometheus", "port": 9090, "role": "metrics_collection"},
    {"name": "grafana", "port": 3001, "role": "visualization"},
]


class MonitoringStackService:
    def get_stack_definition(self) -> dict:
        return {
            "components": MONITORING_COMPONENTS,
            "prometheus_config": "deploy/prometheus/prometheus.yml",
            "scrape_interval_seconds": 15,
            "retention_days": 15,
        }

    def validate_stack(self) -> dict:
        exists = PROMETHEUS_CONF.is_file()
        targets_found = []
        if exists:
            content = PROMETHEUS_CONF.read_text(encoding="utf-8")
            for target in ["api:8000", "prometheus:9090"]:
                if target in content:
                    targets_found.append(target)
        return {
            "valid": exists and len(targets_found) >= 1,
            "prometheus_config_exists": exists,
            "scrape_targets_found": targets_found,
        }

    def get_metrics_catalog(self) -> dict:
        metrics = [
            {"name": "http_requests_total", "type": "counter"},
            {"name": "http_request_duration_seconds", "type": "histogram"},
            {"name": "automation_jobs_processed_total", "type": "counter"},
            {"name": "ai_tokens_used_total", "type": "counter"},
            {"name": "database_connection_pool_size", "type": "gauge"},
        ]
        return {"metrics": metrics, "total": len(metrics)}
