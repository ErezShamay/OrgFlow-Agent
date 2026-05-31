from __future__ import annotations

RECOMMENDED_CORS = {
    "allow_credentials": True,
    "allow_methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    "allow_headers": [
        "Authorization",
        "Content-Type",
        "X-Organization-ID",
        "X-Request-ID",
        "Idempotency-Key",
    ],
    "max_age_seconds": 600,
    "wildcard_origins_allowed": False,
}


class CorsHardeningService:
    def get_recommended_config(self) -> dict:
        return RECOMMENDED_CORS

    def evaluate_config(
        self,
        *,
        allow_origins: list[str],
        allow_methods: list[str] | None = None,
        allow_headers: list[str] | None = None,
        allow_credentials: bool = True,
    ) -> dict:
        methods = allow_methods or ["*"]
        headers = allow_headers or ["*"]
        issues: list[str] = []

        if "*" in allow_origins:
            issues.append("WILDCARD_ORIGIN")
        if "*" in methods:
            issues.append("WILDCARD_METHODS")
        if "*" in headers:
            issues.append("WILDCARD_HEADERS")
        if allow_credentials and "*" in allow_origins:
            issues.append("CREDENTIALS_WITH_WILDCARD_ORIGIN")

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "origin_count": len(allow_origins),
            "allow_credentials": allow_credentials,
        }

    def validate_production_readiness(
        self,
        *,
        allow_origins: list[str] | None = None,
    ) -> dict:
        origins = allow_origins or [
            "https://app.orgflow.example.com",
        ]
        evaluation = self.evaluate_config(
            allow_origins=origins,
            allow_methods=RECOMMENDED_CORS["allow_methods"],
            allow_headers=RECOMMENDED_CORS["allow_headers"],
            allow_credentials=RECOMMENDED_CORS["allow_credentials"],
        )
        return {
            **evaluation,
            "recommended": RECOMMENDED_CORS,
        }
