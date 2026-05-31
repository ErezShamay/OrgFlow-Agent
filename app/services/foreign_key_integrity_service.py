from __future__ import annotations

from app.db.schema_registry import TABLES


class ForeignKeyIntegrityService:
    def get_constraints(self) -> dict:
        constraints = []
        for table_name, schema in TABLES.items():
            for fk in schema.foreign_keys:
                constraints.append({
                    "table": table_name,
                    "column": fk.column,
                    "references_table": fk.references_table,
                    "references_column": fk.references_column,
                    "on_delete": fk.on_delete,
                })
        return {
            "constraints": constraints,
            "constraint_count": len(constraints),
        }

    def validate_references(
        self,
        *,
        table_name: str,
        records: list[dict],
        reference_data: dict[str, set[str]],
    ) -> dict:
        schema = TABLES.get(table_name)
        if not schema:
            return {
                "valid": False,
                "violations": [{"issue": "UNKNOWN_TABLE", "table": table_name}],
            }

        violations = []
        for index, record in enumerate(records):
            for fk in schema.foreign_keys:
                value = record.get(fk.column)
                if value is None:
                    continue
                valid_ids = reference_data.get(fk.references_table, set())
                if value not in valid_ids:
                    violations.append({
                        "row_index": index,
                        "column": fk.column,
                        "value": value,
                        "references_table": fk.references_table,
                        "issue": "ORPHAN_REFERENCE",
                    })

        return {
            "table": table_name,
            "valid": len(violations) == 0,
            "checked_rows": len(records),
            "violations": violations,
        }

    def validate_schema(self) -> dict:
        issues = []
        for table_name, schema in TABLES.items():
            for fk in schema.foreign_keys:
                if fk.references_table not in TABLES:
                    issues.append({
                        "table": table_name,
                        "column": fk.column,
                        "issue": "REFERENCES_UNKNOWN_TABLE",
                        "references_table": fk.references_table,
                    })
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "tables_with_fk": sum(
                1 for schema in TABLES.values() if schema.foreign_keys
            ),
        }
