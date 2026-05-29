DEFAULT_FAILURE_THRESHOLD = 5
DEFAULT_COOLDOWN_MINUTES = 10
DEFAULT_HALF_OPEN_SUCCESS_THRESHOLD = 2


class CircuitBreakerThresholdService:
    def __init__(self):
        self._thresholds: dict[str, dict] = {}
        self._prefix_defaults: dict[str, dict] = {
            "ai:": {
                "failure_threshold": 3,
                "cooldown_minutes": 5,
                "half_open_success_threshold": 2,
            },
            "automation:": {
                "failure_threshold": 5,
                "cooldown_minutes": 10,
                "half_open_success_threshold": 2,
            },
        }

    def set_threshold(
        self,
        breaker_key: str,
        failure_threshold: int = DEFAULT_FAILURE_THRESHOLD,
        cooldown_minutes: int = DEFAULT_COOLDOWN_MINUTES,
        half_open_success_threshold: int = DEFAULT_HALF_OPEN_SUCCESS_THRESHOLD,
    ):
        self._thresholds[breaker_key] = {
            "failure_threshold": failure_threshold,
            "cooldown_minutes": cooldown_minutes,
            "half_open_success_threshold": half_open_success_threshold,
        }
        return self.get_threshold(breaker_key)

    def get_threshold(self, breaker_key: str) -> dict:
        if breaker_key in self._thresholds:
            return dict(self._thresholds[breaker_key])

        for prefix, defaults in self._prefix_defaults.items():
            if breaker_key.startswith(prefix):
                return dict(defaults)

        return {
            "failure_threshold": DEFAULT_FAILURE_THRESHOLD,
            "cooldown_minutes": DEFAULT_COOLDOWN_MINUTES,
            "half_open_success_threshold": DEFAULT_HALF_OPEN_SUCCESS_THRESHOLD,
        }

    def list_thresholds(self) -> list[dict]:
        return [
            {
                "breaker_key": breaker_key,
                **config,
            }
            for breaker_key, config in self._thresholds.items()
        ]
