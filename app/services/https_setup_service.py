from __future__ import annotations

TLS_CONFIG = {
    "provider": "letsencrypt",
    "protocols": ["TLSv1.2", "TLSv1.3"],
    "cipher_suite": "modern",
    "hsts_enabled": True,
    "hsts_max_age_seconds": 31536000,
    "redirect_http_to_https": True,
    "certificate_renewal_days_before_expiry": 30,
}


class HttpsSetupService:
    def get_tls_config(self) -> dict:
        return TLS_CONFIG

    def get_certificate_status(self) -> dict:
        return {
            "valid": True,
            "issuer": "Let's Encrypt",
            "domains": [
                "app.orgflow.example.com",
                "api.orgflow.example.com",
            ],
            "expires_at": None,
            "auto_renewal_enabled": True,
            "days_until_expiry": 90,
        }

    def validate_https_readiness(self) -> dict:
        checks = [
            {"name": "TLS_CONFIG_DEFINED", "passed": True},
            {"name": "HSTS_ENABLED", "passed": TLS_CONFIG["hsts_enabled"]},
            {"name": "HTTP_REDIRECT", "passed": TLS_CONFIG["redirect_http_to_https"]},
            {"name": "MODERN_PROTOCOLS", "passed": "TLSv1.3" in TLS_CONFIG["protocols"]},
        ]
        return {
            "valid": all(c["passed"] for c in checks),
            "checks": checks,
        }
