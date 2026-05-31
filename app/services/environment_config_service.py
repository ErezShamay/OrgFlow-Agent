from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

ENVIRONMENT_PROFILES = {
    "local": {
        "env_file": ".env",
        "debug": True,
        "log_level": "DEBUG",
        "replicas": 1,
    },
    "staging": {
        "env_file": "deploy/environments/staging.env.example",
        "debug": False,
        "log_level": "INFO",
        "replicas": 2,
    },
    "production": {
        "env_file": "deploy/environments/production.env.example",
        "debug": False,
        "log_level": "WARNING",
        "replicas": 3,
    },
}

REQUIRED_PRODUCTION_VARS = [
    "ENVIRONMENT",
    "FRONTEND_URL",
    "SUPABASE_URL",
    "SUPABASE_KEY",
    "JWT_SECRET",
    "OPENAI_API_KEY",
]


class EnvironmentConfigService:
    def list_profiles(self) -> dict:
        profiles = []
        for name, profile in ENVIRONMENT_PROFILES.items():
            env_path = PROJECT_ROOT / profile["env_file"]
            profiles.append({
                "name": name,
                **profile,
                "env_file_exists": env_path.is_file(),
            })
        return {"profiles": profiles, "total": len(profiles)}

    def get_profile(self, environment: str) -> dict:
        profile = ENVIRONMENT_PROFILES.get(environment)
        if profile is None:
            return {"found": False, "environment": environment}
        env_path = PROJECT_ROOT / profile["env_file"]
        return {
            "found": True,
            "environment": environment,
            **profile,
            "env_file_exists": env_path.is_file(),
            "required_vars": (
                REQUIRED_PRODUCTION_VARS
                if environment == "production"
                else []
            ),
        }

    def validate_production_config(self) -> dict:
        env_path = PROJECT_ROOT / ENVIRONMENT_PROFILES["production"]["env_file"]
        if not env_path.is_file():
            return {
                "valid": False,
                "missing_file": str(env_path.relative_to(PROJECT_ROOT)),
            }
        content = env_path.read_text(encoding="utf-8")
        defined = [
            var
            for var in REQUIRED_PRODUCTION_VARS
            if f"{var}=" in content
        ]
        missing = [
            var for var in REQUIRED_PRODUCTION_VARS if var not in defined
        ]
        return {
            "valid": len(missing) == 0,
            "defined": defined,
            "missing": missing,
            "env_file": str(env_path.relative_to(PROJECT_ROOT)),
        }
