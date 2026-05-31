from __future__ import annotations

READINESS_CATEGORIES = [
    {
        "name": "INFRASTRUCTURE",
        "weight": 20,
        "checks": [
            "Docker images built",
            "docker-compose stack validated",
            "Nginx reverse proxy configured",
            "HTTPS certificates ready",
        ],
    },
    {
        "name": "CI_CD",
        "weight": 15,
        "checks": [
            "GitHub Actions pipeline configured",
            "Staging auto-deploy enabled",
            "Production manual gate enabled",
        ],
    },
    {
        "name": "MONITORING",
        "weight": 20,
        "checks": [
            "Prometheus metrics collection",
            "Grafana dashboards",
            "Uptime monitoring active",
            "Centralized logging configured",
        ],
    },
    {
        "name": "SCALING",
        "weight": 15,
        "checks": [
            "Horizontal autoscaling configured",
            "Worker autoscaling configured",
            "CDN and caching enabled",
        ],
    },
    {
        "name": "RESILIENCE",
        "weight": 20,
        "checks": [
            "Disaster recovery plan documented",
            "Backup restore tested",
            "Rollout checklist complete",
        ],
    },
    {
        "name": "SECURITY",
        "weight": 10,
        "checks": [
            "Production secrets configured",
            "TLS modern protocols enabled",
            "Environment separation validated",
        ],
    },
]


class ProductionReadinessService:
    def get_review_framework(self) -> dict:
        total_checks = sum(
            len(cat["checks"]) for cat in READINESS_CATEGORIES
        )
        return {
            "categories": READINESS_CATEGORIES,
            "total_categories": len(READINESS_CATEGORIES),
            "total_checks": total_checks,
        }

    def run_review(
        self,
        passed_checks: list[str] | None = None,
    ) -> dict:
        passed = set(passed_checks or [])
        category_results = []
        total_score = 0.0

        for category in READINESS_CATEGORIES:
            passed_in_category = [
                check for check in category["checks"] if check in passed
            ]
            category_score = (
                len(passed_in_category) / len(category["checks"])
                * category["weight"]
            )
            total_score += category_score
            category_results.append({
                "name": category["name"],
                "weight": category["weight"],
                "passed": len(passed_in_category),
                "total": len(category["checks"]),
                "score": round(category_score, 1),
                "checks": [
                    {
                        "label": check,
                        "passed": check in passed,
                    }
                    for check in category["checks"]
                ],
            })

        return {
            "categories": category_results,
            "overall_score": round(total_score, 1),
            "ready": total_score >= 80.0,
            "threshold": 80.0,
        }

    def get_blockers(
        self,
        passed_checks: list[str] | None = None,
    ) -> dict:
        passed = set(passed_checks or [])
        blockers = []
        for category in READINESS_CATEGORIES:
            for check in category["checks"]:
                if check not in passed:
                    blockers.append({
                        "category": category["name"],
                        "check": check,
                    })
        return {
            "blockers": blockers,
            "count": len(blockers),
        }
