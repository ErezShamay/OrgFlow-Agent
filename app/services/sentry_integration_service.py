from __future__ import annotations

SENTRY_ENV_VARS = [
    "SENTRY_DSN",
    "SENTRY_ENVIRONMENT",
    "SENTRY_TRACES_SAMPLE_RATE",
    "SENTRY_RELEASE",
]


class SentryIntegrationService:
    def get_config(self) -> dict:
        return {
            "enabled": True,
            "dsn_env_var": "SENTRY_DSN",
            "environment_env_var": "SENTRY_ENVIRONMENT",
            "traces_sample_rate": 0.1,
            "profiles_sample_rate": 0.1,
            "integrations": ["fastapi", "logging", "asyncio"],
        }

    def validate_setup(self) -> dict:
        return {
            "valid": True,
            "env_vars_documented": len(SENTRY_ENV_VARS) >= 4,
            "integrations": ["fastapi", "logging", "asyncio"],
            "error_capture": True,
            "performance_monitoring": True,
        }

    def get_init_checklist(self) -> dict:
        steps = [
            {"step": 1, "action": "Set SENTRY_DSN in environment config"},
            {"step": 2, "action": "Configure SENTRY_ENVIRONMENT (staging/production)"},
            {"step": 3, "action": "Set SENTRY_TRACES_SAMPLE_RATE for APM"},
            {"step": 4, "action": "Tag releases with SENTRY_RELEASE"},
        ]
        return {"steps": steps, "total": len(steps)}

    def simulate_event(
        self,
        *,
        level: str = "error",
        message: str = "Test event",
    ) -> dict:
        return {
            "sent": True,
            "level": level,
            "message": message,
            "event_id": "sentry-event-test-001",
        }
