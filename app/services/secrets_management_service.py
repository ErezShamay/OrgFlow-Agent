from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

SECRET_ENV_VARS = [
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "GEMINI_API_KEY",
    "SUPABASE_KEY",
    "RESEND_API_KEY",
    "JWT_SECRET",
]

FORBIDDEN_COMMITTED_FILES = [
    ".env",
    ".env.local",
    ".env.production",
    "credentials.json",
]


class SecretsManagementService:
    def list_managed_secrets(self) -> dict:
        return {
            "secrets": [
                {"name": name, "rotation_supported": True}
                for name in SECRET_ENV_VARS
            ],
            "total": len(SECRET_ENV_VARS),
        }

    def validate_repository_hygiene(self) -> dict:
        tracked = self._list_tracked_files()
        violations = [
            filename
            for filename in FORBIDDEN_COMMITTED_FILES
            if filename in tracked
        ]

        example_env = PROJECT_ROOT / ".env.example"
        gitignore = PROJECT_ROOT / ".gitignore"
        gitignore_covers_env = False
        if gitignore.is_file():
            gitignore_covers_env = ".env" in gitignore.read_text(encoding="utf-8")

        return {
            "valid": len(violations) == 0 and gitignore_covers_env,
            "committed_secret_files": violations,
            "example_env_present": example_env.is_file(),
            "gitignore_covers_env": gitignore_covers_env,
            "checked_files": len(FORBIDDEN_COMMITTED_FILES),
        }

    def _list_tracked_files(self) -> set[str]:
        import subprocess

        try:
            result = subprocess.run(
                ["git", "ls-files"],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                check=True,
            )
        except (OSError, subprocess.CalledProcessError):
            return set()

        return {line.strip() for line in result.stdout.splitlines() if line.strip()}

    def get_rotation_policy(self) -> dict:
        return {
            "rotation_interval_days": 90,
            "grace_period_hours": 24,
            "supported_secrets": SECRET_ENV_VARS,
            "automated_rotation": False,
            "manual_rotation_endpoint": "/secrets/rotation-status",
        }
