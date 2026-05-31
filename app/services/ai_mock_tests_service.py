from __future__ import annotations

AI_MOCK_CONFIG = {
    "providers": ["openai", "anthropic", "gemini"],
    "default_fixture": "deterministic_responses",
    "record_replay": False,
}


class AiMockTestsService:
    def get_config(self) -> dict:
        return AI_MOCK_CONFIG

    def list_fixtures(self) -> dict:
        fixtures = [
            {"id": "review_summary", "tokens": 120, "latency_ms": 50},
            {"id": "action_recommendation", "tokens": 80, "latency_ms": 40},
            {"id": "portfolio_insight", "tokens": 200, "latency_ms": 60},
            {"id": "provider_fallback", "tokens": 100, "latency_ms": 120},
        ]
        return {"fixtures": fixtures, "total": len(fixtures)}

    def simulate_call(
        self,
        *,
        provider: str,
        fixture_id: str,
    ) -> dict:
        fixtures = {f["id"]: f for f in self.list_fixtures()["fixtures"]}
        fixture = fixtures.get(fixture_id)
        if not fixture:
            return {"mocked": False, "provider": provider}
        return {
            "mocked": True,
            "provider": provider,
            "fixture_id": fixture_id,
            "tokens": fixture["tokens"],
            "latency_ms": fixture["latency_ms"],
        }

    def validate_setup(self) -> dict:
        return {
            "valid": True,
            "providers_mocked": len(AI_MOCK_CONFIG["providers"]) >= 2,
            "fixture_count": self.list_fixtures()["total"] >= 3,
        }
