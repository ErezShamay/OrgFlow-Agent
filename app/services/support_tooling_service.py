from __future__ import annotations

SUPPORT_CONFIG = {
    "provider": "intercom",
    "in_app_chat": True,
    "ticket_escalation_hours": 4,
    "sla_by_plan": {"starter": 48, "growth": 24, "enterprise": 4},
}


class SupportToolingService:
    def get_config(self) -> dict:
        return SUPPORT_CONFIG

    def list_channels(self) -> dict:
        channels = [
            {"id": "in_app_chat", "enabled": True},
            {"id": "email", "address": "support@orgflow.example.com"},
            {"id": "status_page", "url": "https://status.orgflow.example.com"},
        ]
        return {"channels": channels, "total": len(channels)}

    def evaluate_sla(self, *, plan: str, hours_open: float) -> dict:
        sla = SUPPORT_CONFIG["sla_by_plan"].get(plan, 48)
        return {
            "within_sla": hours_open <= sla,
            "plan": plan,
            "sla_hours": sla,
            "hours_open": hours_open,
        }

    def validate_setup(self) -> dict:
        return {
            "valid": True,
            "provider": SUPPORT_CONFIG["provider"],
            "channels_configured": self.list_channels()["total"] >= 2,
        }
