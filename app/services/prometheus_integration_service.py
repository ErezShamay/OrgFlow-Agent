from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROMETHEUS_CONF = PROJECT_ROOT / "deploy/prometheus/prometheus.yml"

SCRAPE_JOBS = [
    {"job_name": "orgflow-api", "targets": ["api:8000"], "metrics_path": "/metrics"},
    {"job_name": "prometheus", "targets": ["prometheus:9090"], "metrics_path": "/metrics"},
]


class PrometheusIntegrationService:
    def get_config(self) -> dict:
        return {
            "config_path": "deploy/prometheus/prometheus.yml",
            "scrape_interval_seconds": 15,
            "evaluation_interval_seconds": 15,
            "jobs": SCRAPE_JOBS,
        }

    def validate_integration(self) -> dict:
        exists = PROMETHEUS_CONF.is_file()
        targets_found: list[str] = []
        if exists:
            content = PROMETHEUS_CONF.read_text(encoding="utf-8")
            for target in ["api:8000", "prometheus:9090", "/metrics"]:
                if target in content:
                    targets_found.append(target)
        return {
            "valid": exists and len(targets_found) >= 2,
            "config_exists": exists,
            "targets_found": targets_found,
        }

    def get_scrape_targets(self) -> dict:
        return {"jobs": SCRAPE_JOBS, "total": len(SCRAPE_JOBS)}
