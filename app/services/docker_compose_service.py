from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
COMPOSE_FILE = PROJECT_ROOT / "docker-compose.yml"

STACK_SERVICES = [
    "api",
    "ui",
    "worker",
    "nginx",
    "prometheus",
    "grafana",
]


class DockerComposeService:
    def get_stack_definition(self) -> dict:
        return {
            "compose_file": "docker-compose.yml",
            "services": STACK_SERVICES,
            "networks": ["orgflow-net"],
            "volumes": ["prometheus-data", "grafana-data"],
        }

    def validate_compose_file(self) -> dict:
        exists = COMPOSE_FILE.is_file()
        services_found = []
        if exists:
            content = COMPOSE_FILE.read_text(encoding="utf-8")
            services_found = [
                service
                for service in STACK_SERVICES
                if f"{service}:" in content
            ]
        return {
            "valid": exists and len(services_found) == len(STACK_SERVICES),
            "compose_file_exists": exists,
            "services_defined": services_found,
            "expected_services": STACK_SERVICES,
        }

    def get_startup_commands(self) -> dict:
        return {
            "up": "docker compose up -d",
            "down": "docker compose down",
            "logs": "docker compose logs -f",
            "build": "docker compose build",
            "ps": "docker compose ps",
        }
