from __future__ import annotations

CONTRACT_CONFIG = {
    "spec_format": "openapi_3.1",
    "consumer_driven": True,
    "breaking_change_policy": "semver_major",
}


class ContractTestingService:
    def get_config(self) -> dict:
        return CONTRACT_CONFIG

    def list_contracts(self) -> dict:
        contracts = [
            {"id": "orgflow-api", "version": "v1", "endpoints": 120},
            {"id": "orgflow-ui-bff", "version": "v1", "endpoints": 45},
            {"id": "webhook-events", "version": "v1", "endpoints": 8},
        ]
        return {"contracts": contracts, "total": len(contracts)}

    def validate_schema_change(
        self,
        *,
        change_type: str,
    ) -> dict:
        breaking = change_type in ("remove_field", "rename_field", "change_type")
        return {
            "change_type": change_type,
            "breaking": breaking,
            "requires_major_bump": breaking,
            "allowed": not breaking or CONTRACT_CONFIG["breaking_change_policy"] == "semver_major",
        }

    def validate_setup(self) -> dict:
        return {
            "valid": True,
            "spec_format": CONTRACT_CONFIG["spec_format"],
            "contract_count": self.list_contracts()["total"] >= 2,
        }
