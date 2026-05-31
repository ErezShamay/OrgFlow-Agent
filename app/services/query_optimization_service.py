from __future__ import annotations

from collections import defaultdict
from typing import Any


class QueryOptimizationService:
    SLOW_QUERY_THRESHOLD_MS = 500

    def analyze_query(
        self,
        *,
        table: str,
        filters: list[str] | None = None,
        estimated_rows: int = 1000,
    ) -> dict:
        filters = filters or []
        uses_index = any(
            token in ("id", "organization_id", "project_id")
            for token in filters
        )
        estimated_cost = estimated_rows
        if not uses_index and estimated_rows > 100:
            estimated_cost = estimated_rows * 10

        return {
            "table": table,
            "filters": filters,
            "uses_index": uses_index,
            "estimated_cost": estimated_cost,
            "recommendation": (
                "OK"
                if uses_index
                else "ADD_INDEX_OR_NARROW_FILTER"
            ),
            "slow_risk": estimated_cost > self.SLOW_QUERY_THRESHOLD_MS,
        }

    def batch_load(
        self,
        *,
        parent_records: list[dict],
        child_records: list[dict],
        parent_key: str,
        foreign_key: str,
    ) -> dict:
        grouped: dict[Any, list[dict]] = defaultdict(list)
        for child in child_records:
            grouped[child.get(foreign_key)].append(child)

        enriched = []
        query_count_before = len(parent_records)
        for parent in parent_records:
            key = parent.get(parent_key)
            enriched.append({
                **parent,
                "_children": grouped.get(key, []),
            })

        return {
            "records": enriched,
            "query_count_before": query_count_before + len(child_records),
            "query_count_after": 2,
            "n_plus_one_resolved": True,
        }

    def get_optimization_report(self) -> dict:
        return {
            "slow_query_threshold_ms": self.SLOW_QUERY_THRESHOLD_MS,
            "recommendations": [
                {
                    "pattern": "N+1_PROJECT_ACTIONS",
                    "fix": "Use batch_load with project_id grouping",
                },
                {
                    "pattern": "UNFILTERED_TABLE_SCAN",
                    "fix": "Always filter by organization_id for tenant tables",
                },
            ],
        }
