from __future__ import annotations

AI_EXECUTIVE_ASSISTANT_CONFIG = {
    "assistant_id": "orgflow_exec_assistant_v1",
    "channels": ["dashboard", "email_digest", "briefing"],
    "default_tone": "executive_brief",
}


class AiExecutiveAssistantService:
    def get_config(self) -> dict:
        return AI_EXECUTIVE_ASSISTANT_CONFIG

    def compose_briefing(self, *, topics: list[str] | None = None) -> dict:
        selected = topics or ["portfolio_risk", "sla", "forecast"]
        return {
            "topics": selected,
            "briefing_ready": len(selected) >= 2,
            "estimated_read_minutes": 3,
        }

    def list_capabilities(self) -> dict:
        caps = ["summarize_portfolio", "draft_board_update", "answer_kpi_questions"]
        return {"capabilities": caps, "total": len(caps)}

    def validate_setup(self) -> dict:
        return {
            "valid": True,
            "capabilities_defined": self.list_capabilities()["total"] >= 3,
        }
