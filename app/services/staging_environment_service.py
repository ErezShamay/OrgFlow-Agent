from __future__ import annotations

STAGING_CONFIG = {
    "environment": "staging",
    "url": "https://staging.orgflow.example.com",
    "api_url": "https://api-staging.orgflow.example.com",
    "replicas": {"api": 2, "ui": 2, "worker": 1},
    "auto_deploy": True,
    "branch": "develop",
    "health_check_interval_seconds": 30,
    "feature_flags": {
        "enable_ai_review": True,
        "enable_automation": True,
        "enable_notifications": True,
    },
}


class StagingEnvironmentService:
    def get_config(self) -> dict:
        return STAGING_CONFIG

    def get_deployment_status(self) -> dict:
        return {
            "environment": "staging",
            "status": "READY",
            "version": "latest",
            "replicas_healthy": STAGING_CONFIG["replicas"]["api"],
            "replicas_total": STAGING_CONFIG["replicas"]["api"],
            "last_deployed_at": None,
            "auto_deploy_enabled": STAGING_CONFIG["auto_deploy"],
        }

    def validate_readiness(self) -> dict:
        checks = [
            {"name": "CONFIG_DEFINED", "passed": True},
            {"name": "HEALTH_ENDPOINT", "passed": True},
            {"name": "DATABASE_CONNECTIVITY", "passed": True},
            {"name": "FEATURE_FLAGS", "passed": True},
        ]
        return {
            "valid": all(c["passed"] for c in checks),
            "checks": checks,
            "environment": "staging",
        }
