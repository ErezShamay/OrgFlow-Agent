from __future__ import annotations

from app.db.schema_registry import TABLES, get_tenant_scoped_tables


class TenantDataIsolationService:
    def validate_record(
        self,
        *,
        table_name: str,
        record: dict,
        organization_id: str,
    ) -> dict:
        schema = TABLES.get(table_name)
        if not schema:
            return {
                "valid": False,
                "issue": "UNKNOWN_TABLE",
                "table": table_name,
            }
        if not schema.tenant_column:
            return {
                "valid": True,
                "table": table_name,
                "tenant_scoped": False,
            }

        record_org = record.get(schema.tenant_column)
        valid = record_org == organization_id
        return {
            "valid": valid,
            "table": table_name,
            "tenant_scoped": True,
            "tenant_column": schema.tenant_column,
            "expected_organization_id": organization_id,
            "record_organization_id": record_org,
        }

    def filter_by_tenant(
        self,
        *,
        table_name: str,
        records: list[dict],
        organization_id: str,
    ) -> dict:
        schema = TABLES.get(table_name)
        if not schema or not schema.tenant_column:
            return {
                "table": table_name,
                "records": records,
                "filtered_count": 0,
            }

        column = schema.tenant_column
        scoped = [
            item for item in records if item.get(column) == organization_id
        ]
        leaked = len(records) - len(scoped)
        return {
            "table": table_name,
            "records": scoped,
            "input_count": len(records),
            "output_count": len(scoped),
            "leaked_count": leaked,
            "isolated": leaked == 0 or len(scoped) == len(records),
        }

    def get_isolation_report(self) -> dict:
        tenant_tables = get_tenant_scoped_tables()
        return {
            "tenant_scoped_tables": tenant_tables,
            "table_count": len(tenant_tables),
            "isolation_strategy": "ROW_LEVEL_SECURITY_AND_APP_FILTER",
            "required_header": "X-Organization-ID",
        }
