from __future__ import annotations

SAAS_READINESS_CATEGORIES = [
    {
        "name": "MULTI_TENANCY",
        "weight": 20,
        "checks": ["RLS enforced", "Tenant header validated", "Org isolation tested"],
    },
    {
        "name": "BILLING",
        "weight": 20,
        "checks": ["Stripe integrated", "Plans configured", "Usage quotas enforced"],
    },
    {
        "name": "ONBOARDING",
        "weight": 15,
        "checks": ["Signup flow live", "Demo data available", "Customer onboarding playbook"],
    },
    {
        "name": "SUPPORT",
        "weight": 10,
        "checks": ["Support channels live", "SLA defined", "Status page published"],
    },
    {
        "name": "DOCUMENTATION",
        "weight": 15,
        "checks": ["User docs published", "API docs complete", "Internal runbooks ready"],
    },
    {
        "name": "GO_TO_MARKET",
        "weight": 20,
        "checks": ["Website live", "Pricing published", "Marketing assets ready"],
    },
]


class SaasReadinessService:
    def get_config(self) -> dict:
        total_checks = sum(len(c["checks"]) for c in SAAS_READINESS_CATEGORIES)
        return {
            "threshold_percent": 85.0,
            "categories": len(SAAS_READINESS_CATEGORIES),
            "total_checks": total_checks,
        }

    def list_categories(self) -> dict:
        return {
            "categories": SAAS_READINESS_CATEGORIES,
            "total": len(SAAS_READINESS_CATEGORIES),
        }

    def run_assessment(self, *, passed_checks: list[str] | None = None) -> dict:
        passed = set(passed_checks or [])
        category_results = []
        total_score = 0.0

        for category in SAAS_READINESS_CATEGORIES:
            passed_in_category = [
                check for check in category["checks"] if check in passed
            ]
            category_score = (
                len(passed_in_category) / len(category["checks"]) * category["weight"]
            )
            total_score += category_score
            category_results.append({
                "name": category["name"],
                "passed": len(passed_in_category),
                "total": len(category["checks"]),
                "score": round(category_score, 1),
            })

        threshold = 85.0
        return {
            "categories": category_results,
            "overall_score": round(total_score, 1),
            "ready": total_score >= threshold,
            "threshold": threshold,
        }

    def validate_setup(self) -> dict:
        return {
            "valid": True,
            "categories_defined": len(SAAS_READINESS_CATEGORIES) >= 5,
            "total_checks": self.get_config()["total_checks"] >= 10,
        }
