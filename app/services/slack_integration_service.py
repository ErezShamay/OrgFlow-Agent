from __future__ import annotations

SLACK_INTEGRATION_CONFIG = {
    "app_id": "orgflow_slack_app",
    "signing_secret_env": "SLACK_SIGNING_SECRET",
    "event_subscriptions": ["message.channels", "app_mention"],
}


class SlackIntegrationService:
    def get_config(self) -> dict:
        return SLACK_INTEGRATION_CONFIG

    def handle_event(self, *, event_type: str = "app_mention") -> dict:
        supported = event_type in SLACK_INTEGRATION_CONFIG["event_subscriptions"]
        return {"event_type": event_type, "handled": supported}

    def list_slash_commands(self) -> dict:
        commands = ["/orgflow-status", "/orgflow-actions", "/orgflow-brief"]
        return {"commands": commands, "total": len(commands)}

    def validate_setup(self) -> dict:
        return {
            "valid": True,
            "commands_defined": self.list_slash_commands()["total"] >= 3,
        }
