from __future__ import annotations

TEAMS_INTEGRATION_CONFIG = {
    "connector": "microsoft_teams_bot",
    "notification_channels": ["channel", "chat", "activity_feed"],
    "command_prefix": "/orgflow",
}


class TeamsIntegrationService:
    def get_config(self) -> dict:
        return TEAMS_INTEGRATION_CONFIG

    def post_notification(self, *, channel_id: str = "general", urgent: bool = False) -> dict:
        return {
            "channel_id": channel_id,
            "posted": True,
            "priority": "high" if urgent else "normal",
        }

    def list_commands(self) -> dict:
        commands = ["status", "actions", "briefing"]
        return {"commands": commands, "total": len(commands)}

    def validate_setup(self) -> dict:
        return {
            "valid": True,
            "commands_defined": self.list_commands()["total"] >= 3,
        }
