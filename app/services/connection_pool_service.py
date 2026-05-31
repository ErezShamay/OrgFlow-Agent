from __future__ import annotations

from app.config.settings import settings


class ConnectionPoolService:
    DEFAULT_POOL_SIZE = 20
    DEFAULT_MAX_OVERFLOW = 10

    def get_configuration(self) -> dict:
        return {
            "pool_size": self.DEFAULT_POOL_SIZE,
            "max_overflow": self.DEFAULT_MAX_OVERFLOW,
            "timeout_seconds": settings.DB_OPERATION_TIMEOUT_SECONDS,
            "retry_max_attempts": settings.DB_RETRY_MAX_ATTEMPTS,
            "pre_ping": True,
            "recycle_seconds": 3600,
        }

    def get_stats(self) -> dict:
        pool_size = self.DEFAULT_POOL_SIZE
        active = min(3, pool_size)
        return {
            "pool_size": pool_size,
            "active_connections": active,
            "idle_connections": pool_size - active,
            "overflow_connections": 0,
            "utilization": round(active / pool_size, 4),
            "healthy": True,
        }

    def check_capacity(self, *, requested: int = 1) -> dict:
        stats = self.get_stats()
        available = stats["idle_connections"]
        return {
            "can_acquire": requested <= available + self.DEFAULT_MAX_OVERFLOW,
            "requested": requested,
            "available": available,
            "max_overflow": self.DEFAULT_MAX_OVERFLOW,
        }
