class ProviderIsolationService:
    def __init__(self):
        self._isolated_providers: set[str] = set()

    def isolate_provider(self, provider_name: str, reason: str = "circuit_open"):
        self._isolated_providers.add(provider_name.lower())
        return {
            "provider": provider_name.lower(),
            "isolated": True,
            "reason": reason,
        }

    def release_provider(self, provider_name: str):
        self._isolated_providers.discard(provider_name.lower())
        return {
            "provider": provider_name.lower(),
            "isolated": False,
        }

    def is_provider_isolated(self, provider_name: str) -> bool:
        return provider_name.lower() in self._isolated_providers

    def list_isolated_providers(self) -> list[str]:
        return sorted(self._isolated_providers)

    def sync_from_breakers(self, breakers: list[dict]) -> list[str]:
        for breaker in breakers:
            breaker_key = breaker.get("breaker_key", "")
            if not breaker_key.startswith("ai:"):
                continue
            if breaker.get("state") != "OPEN":
                continue
            provider = breaker_key.split(":", 1)[-1]
            self.isolate_provider(provider, reason="circuit_breaker_open")
        return self.list_isolated_providers()
