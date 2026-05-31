from __future__ import annotations

MULTI_TENANT_CONFIG = {
    "isolation_model": "organization_scoped_rls",
    "tenant_header": "X-Organization-ID",
    "cross_tenant_queries_blocked": True,
    "shared_schema": True,
}


class MultiTenantReadinessService:
    def get_config(self) -> dict:
        return MULTI_TENANT_CONFIG

    def list_checklist(self) -> dict:
        items = [
            {"id": "rls_policies", "label": "RLS policies enforced", "critical": True},
            {"id": "tenant_header", "label": "Tenant header validated", "critical": True},
            {"id": "jwt_org_claim", "label": "JWT org claim matches header", "critical": True},
            {"id": "audit_isolation", "label": "Audit logs tenant-scoped", "critical": False},
            {"id": "storage_prefix", "label": "File storage prefixed by org", "critical": True},
        ]
        return {"items": items, "total": len(items)}

    def evaluate_readiness(self, *, passed_item_ids: list[str]) -> dict:
        items = self.list_checklist()["items"]
        critical_ids = {i["id"] for i in items if i["critical"]}
        passed = set(passed_item_ids)
        return {
            "ready": critical_ids.issubset(passed),
            "passed": len(passed),
            "total": len(items),
            "missing_critical": sorted(critical_ids - passed),
        }

    def validate_setup(self) -> dict:
        return {
            "valid": True,
            "isolation_model": MULTI_TENANT_CONFIG["isolation_model"],
            "checklist_items": self.list_checklist()["total"] >= 4,
        }
