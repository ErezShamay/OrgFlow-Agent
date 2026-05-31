from __future__ import annotations

AUTH_HARDENING_CONTROLS = [
    {"id": "JWT_SIGNATURE_VALIDATION", "enabled": True},
    {"id": "TOKEN_EXPIRY_ENFORCED", "enabled": True},
    {"id": "REFRESH_TOKEN_ROTATION", "enabled": True},
    {"id": "SESSION_TIMEOUT", "enabled": True, "timeout_minutes": 60},
    {"id": "ORG_HEADER_REQUIRED", "enabled": True},
    {"id": "ROLE_BASED_ACCESS", "enabled": True},
    {"id": "AUDIT_LOGIN_EVENTS", "enabled": True},
]


class AuthHardeningService:
    def get_controls(self) -> dict:
        enabled = [c for c in AUTH_HARDENING_CONTROLS if c.get("enabled")]
        return {
            "controls": AUTH_HARDENING_CONTROLS,
            "total": len(AUTH_HARDENING_CONTROLS),
            "enabled_count": len(enabled),
            "all_enabled": len(enabled) == len(AUTH_HARDENING_CONTROLS),
        }

    def evaluate_token_policy(
        self,
        *,
        access_token_ttl_minutes: int = 15,
        refresh_token_ttl_days: int = 7,
        algorithm: str = "HS256",
    ) -> dict:
        issues: list[str] = []
        if access_token_ttl_minutes > 60:
            issues.append("ACCESS_TOKEN_TTL_TOO_LONG")
        if refresh_token_ttl_days > 30:
            issues.append("REFRESH_TOKEN_TTL_TOO_LONG")
        if algorithm not in {"HS256", "RS256"}:
            issues.append("UNSUPPORTED_ALGORITHM")

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "access_token_ttl_minutes": access_token_ttl_minutes,
            "refresh_token_ttl_days": refresh_token_ttl_days,
            "algorithm": algorithm,
        }

    def validate_setup(self) -> dict:
        controls = self.get_controls()
        return {
            "valid": controls["all_enabled"],
            "controls": controls,
        }
