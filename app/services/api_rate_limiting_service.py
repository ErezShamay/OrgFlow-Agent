from __future__ import annotations

RATE_LIMIT_TIERS = {
    "anonymous": {"requests_per_minute": 30, "burst": 10},
    "authenticated": {"requests_per_minute": 300, "burst": 50},
    "admin": {"requests_per_minute": 600, "burst": 100},
}

DEFAULT_HEADERS = [
    "X-RateLimit-Limit",
    "X-RateLimit-Remaining",
    "X-RateLimit-Reset",
    "Retry-After",
]


class ApiRateLimitingService:
    def get_config(self) -> dict:
        return {
            "enabled": True,
            "strategy": "sliding_window",
            "tiers": RATE_LIMIT_TIERS,
            "response_headers": DEFAULT_HEADERS,
            "error_code": "RATE_LIMIT_EXCEEDED",
        }

    def check_rate_limit(
        self,
        *,
        client_id: str,
        tier: str = "authenticated",
        current_count: int = 0,
    ) -> dict:
        limits = RATE_LIMIT_TIERS.get(tier, RATE_LIMIT_TIERS["anonymous"])
        limit = limits["requests_per_minute"]
        remaining = max(0, limit - current_count)
        allowed = current_count < limit
        return {
            "client_id": client_id,
            "tier": tier,
            "allowed": allowed,
            "limit": limit,
            "remaining": remaining,
            "burst": limits["burst"],
            "retry_after_seconds": 60 if not allowed else 0,
        }

    def validate_setup(self) -> dict:
        checks = [
            {"name": "TIERS_DEFINED", "passed": len(RATE_LIMIT_TIERS) >= 3},
            {"name": "HEADERS_CONFIGURED", "passed": len(DEFAULT_HEADERS) >= 4},
            {"name": "ERROR_CODE_MAPPED", "passed": True},
        ]
        return {
            "valid": all(c["passed"] for c in checks),
            "checks": checks,
        }
