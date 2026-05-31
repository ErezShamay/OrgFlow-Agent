from __future__ import annotations

WHATSAPP_INTEGRATION_CONFIG = {
    "provider": "meta_cloud_api",
    "webhook_path": "/integrations/whatsapp/webhook",
    "supported_message_types": ["text", "template", "document"],
}


class WhatsappIntegrationService:
    def get_config(self) -> dict:
        return WHATSAPP_INTEGRATION_CONFIG

    def validate_webhook(self, *, signature_valid: bool = True) -> dict:
        return {
            "accepted": signature_valid,
            "provider": WHATSAPP_INTEGRATION_CONFIG["provider"],
        }

    def list_templates(self) -> dict:
        templates = ["action_reminder", "escalation_alert", "daily_digest"]
        return {"templates": templates, "total": len(templates)}

    def validate_setup(self) -> dict:
        return {
            "valid": True,
            "templates_defined": self.list_templates()["total"] >= 3,
        }
