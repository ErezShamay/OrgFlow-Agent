from __future__ import annotations

ADMIN_PANEL_CONFIG = {
    "route_prefix": "/admin",
    "required_role": "ADMIN",
    "features_enabled": True,
    "impersonation_supported": True,
}


class AdminPanelService:
    def get_config(self) -> dict:
        return ADMIN_PANEL_CONFIG

    def list_modules(self) -> dict:
        modules = [
            {"id": "organizations", "label": "Organizations", "actions": ["list", "suspend"]},
            {"id": "users", "label": "Users", "actions": ["list", "reset_password"]},
            {"id": "billing", "label": "Billing", "actions": ["view_subscriptions"]},
            {"id": "feature_flags", "label": "Feature flags", "actions": ["toggle"]},
            {"id": "audit_logs", "label": "Audit logs", "actions": ["search", "export"]},
        ]
        return {"modules": modules, "total": len(modules)}

    def check_access(self, *, role: str) -> dict:
        allowed = role in {"ADMIN", "SUPER_ADMIN"}
        return {
            "allowed": allowed,
            "required_role": ADMIN_PANEL_CONFIG["required_role"],
            "role": role,
        }

    def validate_setup(self) -> dict:
        return {
            "valid": True,
            "modules_available": self.list_modules()["total"] >= 4,
            "impersonation": ADMIN_PANEL_CONFIG["impersonation_supported"],
        }
