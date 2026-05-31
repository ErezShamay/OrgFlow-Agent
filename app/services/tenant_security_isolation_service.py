from __future__ import annotations

from app.services.tenant_data_isolation_service import TenantDataIsolationService


class TenantSecurityIsolationService:
    def __init__(
        self,
        isolation_service: TenantDataIsolationService | None = None,
    ):
        self.isolation_service = (
            isolation_service or TenantDataIsolationService()
        )

    def get_isolation_report(self) -> dict:
        report = self.isolation_service.get_isolation_report()
        return {
            **report,
            "security_controls": [
                "ROW_LEVEL_SECURITY",
                "ORG_HEADER_VALIDATION",
                "JWT_ORG_CLAIM_BINDING",
                "AUDIT_CROSS_TENANT_ACCESS",
            ],
        }

    def validate_cross_tenant_access(
        self,
        *,
        table_name: str,
        record: dict,
        requesting_org_id: str,
    ) -> dict:
        validation = self.isolation_service.validate_record(
            table_name=table_name,
            record=record,
            organization_id=requesting_org_id,
        )
        return {
            **validation,
            "access_denied": not validation.get("valid", False),
        }

    def simulate_tenant_leak_check(
        self,
        *,
        table_name: str,
        records: list[dict],
        organization_id: str,
    ) -> dict:
        filtered = self.isolation_service.filter_by_tenant(
            table_name=table_name,
            records=records,
            organization_id=organization_id,
        )
        return {
            **filtered,
            "secure": filtered.get("leaked_count", 0) == 0,
        }

    def validate_setup(self) -> dict:
        report = self.get_isolation_report()
        return {
            "valid": report["table_count"] > 0,
            "tenant_scoped_tables": report["table_count"],
            "strategy": report["isolation_strategy"],
        }
