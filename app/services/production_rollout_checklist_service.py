from __future__ import annotations

ROLLOUT_CHECKLIST = [
    {"id": "pre-deploy-backup", "category": "PRE_DEPLOY", "label": "Run pre-deploy backup"},
    {"id": "migration-review", "category": "PRE_DEPLOY", "label": "Review pending migrations"},
    {"id": "feature-flags", "category": "PRE_DEPLOY", "label": "Verify feature flags"},
    {"id": "staging-smoke", "category": "PRE_DEPLOY", "label": "Staging smoke tests passed"},
    {"id": "deploy-api", "category": "DEPLOY", "label": "Deploy API service"},
    {"id": "deploy-ui", "category": "DEPLOY", "label": "Deploy UI service"},
    {"id": "deploy-workers", "category": "DEPLOY", "label": "Deploy worker service"},
    {"id": "run-migrations", "category": "DEPLOY", "label": "Apply database migrations"},
    {"id": "health-check", "category": "POST_DEPLOY", "label": "Verify health endpoints"},
    {"id": "smoke-tests", "category": "POST_DEPLOY", "label": "Run production smoke tests"},
    {"id": "monitoring", "category": "POST_DEPLOY", "label": "Confirm monitoring alerts"},
    {"id": "rollback-plan", "category": "POST_DEPLOY", "label": "Document rollback plan"},
]


class ProductionRolloutChecklistService:
    def get_checklist(self) -> dict:
        categories = sorted({item["category"] for item in ROLLOUT_CHECKLIST})
        return {
            "items": ROLLOUT_CHECKLIST,
            "total": len(ROLLOUT_CHECKLIST),
            "categories": categories,
        }

    def evaluate_checklist(
        self,
        completed_ids: list[str] | None = None,
    ) -> dict:
        completed = set(completed_ids or [])
        items = []
        for item in ROLLOUT_CHECKLIST:
            items.append({
                **item,
                "completed": item["id"] in completed,
            })
        completed_count = sum(1 for item in items if item["completed"])
        return {
            "items": items,
            "completed_count": completed_count,
            "total": len(items),
            "ready": completed_count == len(items),
            "completion_percent": round(
                completed_count / len(items) * 100,
                1,
            ),
        }

    def get_next_items(
        self,
        completed_ids: list[str] | None = None,
    ) -> dict:
        evaluation = self.evaluate_checklist(completed_ids)
        pending = [
            item for item in evaluation["items"] if not item["completed"]
        ]
        return {
            "next_items": pending[:3],
            "pending_count": len(pending),
        }
