from __future__ import annotations

SHAREPOINT_INTEGRATION_CONFIG = {
    "connector": "microsoft_graph",
    "sync_mode": "incremental",
    "scopes": ["Sites.Read.All", "Files.Read.All"],
}


class SharepointIntegrationService:
    def get_config(self) -> dict:
        return SHAREPOINT_INTEGRATION_CONFIG

    def sync_library(self, *, site_id: str = "site-1", files_found: int = 5) -> dict:
        return {
            "site_id": site_id,
            "synced": files_found > 0,
            "files_indexed": files_found,
        }

    def list_sync_targets(self) -> dict:
        targets = ["document_libraries", "lists", "metadata"]
        return {"targets": targets, "total": len(targets)}

    def validate_setup(self) -> dict:
        return {
            "valid": True,
            "targets_defined": self.list_sync_targets()["total"] >= 3,
        }
