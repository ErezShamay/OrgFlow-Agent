from __future__ import annotations

ABUSE_SIGNALS = [
    "HIGH_REQUEST_VELOCITY",
    "CREDENTIAL_STUFFING",
    "BOT_USER_AGENT",
    "SUSPICIOUS_GEO",
    "REPEATED_4XX",
    "REPEATED_401",
]


class ApiAbuseProtectionService:
    def get_protection_config(self) -> dict:
        return {
            "enabled": True,
            "signals_monitored": ABUSE_SIGNALS,
            "auto_block_threshold": 100,
            "temporary_block_minutes": 15,
            "captcha_challenge_enabled": False,
            "ip_allowlist_supported": True,
        }

    def evaluate_client(
        self,
        *,
        client_id: str,
        requests_per_minute: int = 0,
        failed_auth_count: int = 0,
        suspicious_user_agent: bool = False,
    ) -> dict:
        signals: list[str] = []
        score = 0

        if requests_per_minute > 500:
            signals.append("HIGH_REQUEST_VELOCITY")
            score += 40
        if failed_auth_count >= 10:
            signals.append("CREDENTIAL_STUFFING")
            score += 35
        if suspicious_user_agent:
            signals.append("BOT_USER_AGENT")
            score += 15

        action = "ALLOW"
        if score >= 70:
            action = "BLOCK"
        elif score >= 40:
            action = "CHALLENGE"

        return {
            "client_id": client_id,
            "abuse_score": score,
            "signals": signals,
            "action": action,
            "blocked": action == "BLOCK",
        }

    def validate_setup(self) -> dict:
        config = self.get_protection_config()
        return {
            "valid": config["enabled"] and len(config["signals_monitored"]) >= 4,
            "signals_count": len(config["signals_monitored"]),
        }
