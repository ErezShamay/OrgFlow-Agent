from __future__ import annotations

from datetime import UTC, datetime, timedelta


class DataRetentionService:
    DEFAULT_POLICIES: dict[str, dict] = {
        "ai_execution_logs": {
            "retention_days": 90,
            "action": "ARCHIVE_THEN_DELETE",
        },
        "audit_log": {
            "retention_days": 365,
            "action": "ARCHIVE",
        },
        "weekly_reports": {
            "retention_days": 730,
            "action": "SOFT_DELETE",
        },
        "automation_runs": {
            "retention_days": 180,
            "action": "DELETE",
        },
    }

    def list_policies(self) -> dict:
        policies = []
        for table, config in self.DEFAULT_POLICIES.items():
            policies.append({
                "table": table,
                **config,
            })
        return {
            "policies": policies,
            "policy_count": len(policies),
        }

    def evaluate_record(
        self,
        *,
        table_name: str,
        created_at: str,
        reference_time: datetime | None = None,
    ) -> dict:
        policy = self.DEFAULT_POLICIES.get(table_name)
        if not policy:
            return {
                "table": table_name,
                "eligible_for_purge": False,
                "reason": "NO_POLICY",
            }

        reference = reference_time or datetime.now(UTC)
        created = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        age_days = (reference - created).days
        retention_days = policy["retention_days"]
        eligible = age_days > retention_days

        return {
            "table": table_name,
            "age_days": age_days,
            "retention_days": retention_days,
            "eligible_for_purge": eligible,
            "recommended_action": policy["action"] if eligible else "RETAIN",
        }

    def simulate_purge(
        self,
        *,
        table_name: str,
        records: list[dict],
        created_at_field: str = "created_at",
    ) -> dict:
        to_purge = []
        to_retain = []
        for record in records:
            created_at = record.get(created_at_field)
            if not created_at:
                to_retain.append(record)
                continue
            result = self.evaluate_record(
                table_name=table_name,
                created_at=created_at,
            )
            if result["eligible_for_purge"]:
                to_purge.append(record)
            else:
                to_retain.append(record)

        return {
            "table": table_name,
            "purge_count": len(to_purge),
            "retain_count": len(to_retain),
            "records_to_purge": to_purge,
        }

    def get_next_review_date(self) -> str:
        return (datetime.now(UTC) + timedelta(days=7)).date().isoformat()
