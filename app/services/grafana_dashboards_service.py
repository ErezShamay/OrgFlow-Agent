from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DASHBOARDS_DIR = PROJECT_ROOT / "deploy/grafana/dashboards"

DASHBOARD_CATALOG = [
    {
        "uid": "orgflow-overview",
        "title": "OrgFlow Overview",
        "panels": ["request_rate", "error_rate", "p95_latency"],
        "file": "deploy/grafana/dashboards/orgflow-overview.json",
    },
    {
        "uid": "orgflow-ai",
        "title": "AI Runtime Metrics",
        "panels": ["token_usage", "ai_latency", "provider_failures"],
        "file": "deploy/grafana/dashboards/orgflow-ai.json",
    },
    {
        "uid": "orgflow-automation",
        "title": "Automation Metrics",
        "panels": ["job_success_rate", "queue_depth", "retry_count"],
        "file": "deploy/grafana/dashboards/orgflow-automation.json",
    },
]


class GrafanaDashboardsService:
    def get_config(self) -> dict:
        return {
            "provider": "grafana",
            "port": 3001,
            "provisioning_path": "deploy/grafana/dashboards",
            "dashboard_count": len(DASHBOARD_CATALOG),
        }

    def list_dashboards(self) -> dict:
        return {"dashboards": DASHBOARD_CATALOG, "total": len(DASHBOARD_CATALOG)}

    def validate_provisioning(self) -> dict:
        existing = [
            entry["uid"]
            for entry in DASHBOARD_CATALOG
            if (PROJECT_ROOT / entry["file"]).is_file()
        ]
        return {
            "valid": len(existing) >= 1,
            "dashboards_found": existing,
            "expected": len(DASHBOARD_CATALOG),
        }

    def get_dashboard(self, uid: str) -> dict:
        for entry in DASHBOARD_CATALOG:
            if entry["uid"] == uid:
                path = PROJECT_ROOT / entry["file"]
                return {
                    "found": True,
                    "uid": uid,
                    "title": entry["title"],
                    "panels": entry["panels"],
                    "file_exists": path.is_file(),
                }
        return {"found": False, "uid": uid}
