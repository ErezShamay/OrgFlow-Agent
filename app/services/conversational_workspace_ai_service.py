from __future__ import annotations

CONVERSATIONAL_WORKSPACE_AI_CONFIG = {
    "session_store": "redis",
    "max_context_messages": 20,
    "tools_enabled": ["search", "create_action", "summarize_timeline"],
}


class ConversationalWorkspaceAiService:
    def get_config(self) -> dict:
        return CONVERSATIONAL_WORKSPACE_AI_CONFIG

    def chat(self, *, message: str = "Summarize today", project_id: str = "p1") -> dict:
        return {
            "project_id": project_id,
            "reply_generated": len(message.strip()) > 0,
            "tools_available": len(CONVERSATIONAL_WORKSPACE_AI_CONFIG["tools_enabled"]),
        }

    def list_tools(self) -> dict:
        tools = CONVERSATIONAL_WORKSPACE_AI_CONFIG["tools_enabled"]
        return {"tools": tools, "total": len(tools)}

    def validate_setup(self) -> dict:
        return {
            "valid": True,
            "tools_defined": self.list_tools()["total"] >= 3,
        }
