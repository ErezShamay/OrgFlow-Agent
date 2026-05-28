from __future__ import annotations

import threading
from datetime import UTC, datetime, timedelta
from typing import Any

from app.config.settings import Settings, load_settings


SENSITIVE_FIELD_TOKENS = ("KEY", "SECRET", "TOKEN", "PASSWORD")


class ConfigManager:
    """Thread-safe configuration access with periodic refresh."""

    def __init__(self, ttl_seconds: int = 60) -> None:
        self._ttl_seconds = ttl_seconds
        self._lock = threading.Lock()
        self._settings: Settings = load_settings()
        self._expires_at = datetime.now(UTC) + timedelta(seconds=ttl_seconds)

    def get_settings(self) -> Settings:
        with self._lock:
            if datetime.now(UTC) >= self._expires_at:
                self._settings = load_settings()
                self._expires_at = datetime.now(UTC) + timedelta(seconds=self._ttl_seconds)
            return self._settings

    def force_reload(self) -> Settings:
        with self._lock:
            self._settings = load_settings()
            self._expires_at = datetime.now(UTC) + timedelta(seconds=self._ttl_seconds)
            return self._settings

    def get_safe_snapshot(self) -> dict[str, Any]:
        settings = self.get_settings()
        payload = settings.model_dump()
        safe_payload: dict[str, Any] = {}
        for key, value in payload.items():
            if any(token in key.upper() for token in SENSITIVE_FIELD_TOKENS):
                safe_payload[key] = "***"
            else:
                safe_payload[key] = value
        return safe_payload

    def get_secret_rotation_status(self) -> dict[str, Any]:
        settings = self.get_settings()
        openai_keys = settings.get_openai_api_keys()
        return {
            "openai": {
                "ring_size": len(openai_keys),
                "active_index": settings.OPENAI_ACTIVE_KEY_INDEX if openai_keys else None,
                "fallback_single_key_configured": bool(settings.OPENAI_API_KEY),
            }
        }


config_manager = ConfigManager()
