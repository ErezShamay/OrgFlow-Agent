from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
NGINX_CONF = PROJECT_ROOT / "deploy/nginx/nginx.conf"

UPSTREAMS = [
    {"name": "api_backend", "target": "api:8000"},
    {"name": "ui_backend", "target": "ui:3000"},
]

ROUTES = [
    {"path": "/api/", "upstream": "api_backend", "strip_prefix": False},
    {"path": "/", "upstream": "ui_backend", "strip_prefix": False},
    {"path": "/health", "upstream": "api_backend", "strip_prefix": False},
]


class NginxReverseProxyService:
    def get_config(self) -> dict:
        return {
            "config_file": "deploy/nginx/nginx.conf",
            "upstreams": UPSTREAMS,
            "routes": ROUTES,
            "listen_port": 80,
            "ssl_termination": "nginx",
        }

    def validate_config(self) -> dict:
        exists = NGINX_CONF.is_file()
        upstreams_found = []
        if exists:
            content = NGINX_CONF.read_text(encoding="utf-8")
            upstreams_found = [
                upstream["name"]
                for upstream in UPSTREAMS
                if upstream["name"] in content
            ]
        return {
            "valid": exists and len(upstreams_found) == len(UPSTREAMS),
            "config_exists": exists,
            "upstreams_found": upstreams_found,
            "expected_upstreams": [u["name"] for u in UPSTREAMS],
        }

    def get_routes(self) -> dict:
        return {"routes": ROUTES, "total": len(ROUTES)}
