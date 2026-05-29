from app.ai.provider_outage_handler import AIProviderOutageHandler
from app.config.settings import settings
from app.services.provider_isolation_service import ProviderIsolationService


class AIProviderFailoverService:
    def __init__(
        self,
        outage_handler: AIProviderOutageHandler | None = None,
        isolation_service: ProviderIsolationService | None = None,
    ):
        self.outage_handler = outage_handler or AIProviderOutageHandler()
        self.isolation_service = (
            isolation_service or ProviderIsolationService()
        )

    def get_failover_chain(self, primary_provider: str | None = None) -> list[str]:
        primary = (primary_provider or settings.AI_PROVIDER or "openai").lower()
        fallbacks = [
            provider.lower()
            for provider in settings.get_ai_fallback_providers()
        ]
        ordered: list[str] = []
        for provider in [primary, *fallbacks]:
            if provider not in ordered:
                ordered.append(provider)
        return ordered

    def select_available_provider(
        self,
        primary_provider: str | None = None,
    ) -> dict:
        chain = self.get_failover_chain(primary_provider)
        for provider in chain:
            if self.isolation_service.is_provider_isolated(provider):
                continue
            if not self.outage_handler.is_provider_available(provider):
                continue
            return {
                "provider": provider,
                "failover_used": provider != chain[0],
                "chain": chain,
            }
        return {
            "provider": None,
            "failover_used": True,
            "chain": chain,
            "error": "NO_AVAILABLE_PROVIDER",
        }

    def record_provider_failure(self, provider_name: str):
        self.outage_handler.register_failure(provider_name.lower())
        if not self.outage_handler.is_provider_available(provider_name):
            self.isolation_service.isolate_provider(
                provider_name,
                reason="outage_threshold_exceeded",
            )

    def record_provider_success(self, provider_name: str):
        self.outage_handler.register_success(provider_name.lower())
        self.isolation_service.release_provider(provider_name)

    def get_status(self) -> dict:
        chain = self.get_failover_chain()
        selected = self.select_available_provider()
        return {
            "primary_provider": chain[0] if chain else None,
            "failover_chain": chain,
            "selected_provider": selected.get("provider"),
            "failover_active": selected.get("failover_used", False),
            "isolated_providers": (
                self.isolation_service.list_isolated_providers()
            ),
        }
