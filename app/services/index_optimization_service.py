from __future__ import annotations

from app.db.schema_registry import TABLES


class IndexOptimizationService:
    def list_indexes(self) -> dict:
        indexes = []
        for table_name, schema in TABLES.items():
            for index in schema.indexes:
                indexes.append({
                    "table": table_name,
                    "name": index.name,
                    "columns": list(index.columns),
                    "unique": index.unique,
                })
        return {
            "indexes": indexes,
            "index_count": len(indexes),
        }

    def get_recommendations(self) -> dict:
        recommendations = []
        for table_name, schema in TABLES.items():
            if schema.tenant_column and not any(
                schema.tenant_column in index.columns
                for index in schema.indexes
            ):
                recommendations.append({
                    "table": table_name,
                    "priority": "HIGH",
                    "suggested_index": f"{table_name}_{schema.tenant_column}_idx",
                    "columns": [schema.tenant_column],
                    "reason": "Tenant filter queries need organization index",
                })
            if schema.soft_delete_column and not any(
                schema.soft_delete_column in index.columns
                for index in schema.indexes
            ):
                recommendations.append({
                    "table": table_name,
                    "priority": "MEDIUM",
                    "suggested_index": f"{table_name}_active_idx",
                    "columns": [schema.soft_delete_column],
                    "reason": "Soft-delete filters benefit from partial index",
                })
        return {
            "recommendations": recommendations,
            "recommendation_count": len(recommendations),
        }

    def analyze_table(self, table_name: str) -> dict:
        schema = TABLES.get(table_name)
        if not schema:
            return {"table": table_name, "found": False}
        return {
            "table": table_name,
            "found": True,
            "existing_indexes": [
                {"name": index.name, "columns": list(index.columns)}
                for index in schema.indexes
            ],
            "index_count": len(schema.indexes),
        }
