from __future__ import annotations

from app.db.schema_registry import TABLES, get_tenant_scoped_tables


class RlsPolicyService:
    def list_policies(self) -> dict:
        policies = []
        for table_name, schema in TABLES.items():
            for policy in schema.rls_policies:
                policies.append({
                    "table": table_name,
                    "policy_name": policy.name,
                    "command": policy.command,
                    "using": policy.using_expression,
                    "check": policy.check_expression,
                })
        return {
            "policies": policies,
            "policy_count": len(policies),
            "tenant_scoped_tables": get_tenant_scoped_tables(),
        }

    def validate_coverage(self) -> dict:
        gaps = []
        for table_name, schema in TABLES.items():
            if not schema.tenant_column:
                continue
            if not schema.rls_policies:
                gaps.append({
                    "table": table_name,
                    "issue": "MISSING_RLS",
                    "tenant_column": schema.tenant_column,
                })
        return {
            "valid": len(gaps) == 0,
            "gaps": gaps,
            "covered_tables": len(get_tenant_scoped_tables()) - len(gaps),
        }

    def get_table_policies(self, table_name: str) -> dict:
        schema = TABLES.get(table_name)
        if not schema:
            return {"table": table_name, "policies": [], "found": False}
        return {
            "table": table_name,
            "found": True,
            "tenant_column": schema.tenant_column,
            "policies": [
                {
                    "policy_name": policy.name,
                    "command": policy.command,
                    "using": policy.using_expression,
                }
                for policy in schema.rls_policies
            ],
        }
