from __future__ import annotations

from dotenv import load_dotenv
from pydantic import AnyHttpUrl, BaseModel, ValidationError, field_validator, model_validator
import os
from typing import Literal, Optional

from app.config.supabase_key import supabase_key_jwt_role

# Delay importing ConfigurationError to avoid circular import during package
# initialization. We'll import it only if validation fails.

class FeatureFlags(BaseModel):
    enable_notifications: bool = True
    enable_automation: bool = True
    enable_ai_review: bool = True
    enable_email_delivery: bool = True

    @staticmethod
    def from_env() -> "FeatureFlags":
        def parse_bool(name: str, default: bool) -> bool:
            raw_value = os.getenv(name)
            if raw_value is None:
                return default

            normalized = raw_value.strip().lower()
            return normalized in ("1", "true", "yes", "on")

        return FeatureFlags(
            enable_notifications=parse_bool("FEATURE_NOTIFICATIONS", True),
            enable_automation=parse_bool("FEATURE_AUTOMATION", True),
            enable_ai_review=parse_bool("FEATURE_AI_REVIEW", True),
            enable_email_delivery=parse_bool("FEATURE_EMAIL_DELIVERY", True),
        )

ALLOWED_AI_PROVIDERS = (
    "ollama",
    "openai",
    "anthropic",
    "gemini",
)

ALLOWED_LLM_MODES = (
    "mock",
    "openai",
)

ALLOWED_EMAIL_PROVIDERS = (
    "gmail",
    "microsoft",
)

ALLOWED_LOG_LEVELS = (
    "DEBUG",
    "INFO",
    "WARNING",
    "ERROR",
    "CRITICAL",
)


class Settings(BaseModel):
    ENVIRONMENT: Literal["local", "development", "staging", "production", "test"]
    FRONTEND_URL: AnyHttpUrl
    AI_PROVIDER: Literal["ollama", "openai", "anthropic", "gemini"]
    AI_FALLBACK_PROVIDERS: Optional[str] = None
    DEFAULT_AI_MODEL: str
    AI_MAX_RETRIES: int
    ORG_FLOW_LLM_MODE: Literal["mock", "openai"]
    OPENAI_MODEL: str
    OPENAI_API_KEY: Optional[str]
    OPENAI_API_KEYS: Optional[str] = None
    OPENAI_ACTIVE_KEY_INDEX: int = 0
    ANTHROPIC_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    LOG_LEVEL: str
    RESEND_API_KEY: Optional[str]
    SUPABASE_URL: Optional[AnyHttpUrl]
    SUPABASE_KEY: Optional[str]
    EMAIL_PROVIDER: Literal["gmail", "microsoft"]
    CONFIG_CACHE_TTL_SECONDS: int = 60
    IDEMPOTENCY_TTL_SECONDS: int = 3600
    IDEMPOTENCY_HEADER: str = "X-Idempotency-Key"
    DB_RETRY_MAX_ATTEMPTS: int = 3
    DB_RETRY_BASE_DELAY_SECONDS: float = 0.1
    DB_OPERATION_TIMEOUT_SECONDS: float = 5.0
    AUTH_JWT_SECRET: str = "dev-secret-change-me-at-least-32-chars"
    AUTH_JWT_ALGORITHM: str = "HS256"
    AUTH_SESSION_TIMEOUT_MINUTES: int = 60
    AUTH_REFRESH_TOKEN_TTL_MINUTES: int = 1440
    CORS_EXTRA_ORIGINS: Optional[str] = None
    FEATURE_FLAGS: FeatureFlags

    @field_validator("FRONTEND_URL", mode="before")
    @classmethod
    def normalize_frontend_url(cls, value: object) -> object:
        if isinstance(value, str):
            return value.rstrip("/")
        return value

    @field_validator("DEFAULT_AI_MODEL", "OPENAI_MODEL")
    def validate_non_empty_string(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("must be a non-empty string")
        return value.strip()

    @field_validator("LOG_LEVEL", mode="before")
    def normalize_log_level(cls, value: str) -> str:
        return value.upper().strip()

    @field_validator("LOG_LEVEL")
    def validate_log_level(cls, value: str) -> str:
        if value not in ALLOWED_LOG_LEVELS:
            raise ValueError(
                f"must be one of {ALLOWED_LOG_LEVELS}, got {value}"
            )
        return value

    @field_validator("ORG_FLOW_LLM_MODE")
    def validate_llm_mode(cls, value: str) -> str:
        if value not in ALLOWED_LLM_MODES:
            raise ValueError(
                f"must be one of {ALLOWED_LLM_MODES}, got {value}"
            )
        return value

    @field_validator("EMAIL_PROVIDER")
    def validate_email_provider(cls, value: str) -> str:
        if value not in ALLOWED_EMAIL_PROVIDERS:
            raise ValueError(
                f"must be one of {ALLOWED_EMAIL_PROVIDERS}, got {value}"
            )
        return value

    @field_validator("AI_PROVIDER")
    def validate_ai_provider(cls, value: str) -> str:
        if value not in ALLOWED_AI_PROVIDERS:
            raise ValueError(
                f"must be one of {ALLOWED_AI_PROVIDERS}, got {value}"
            )
        return value

    @model_validator(mode="after")
    def validate_consistency(self):
        if (
            self.ORG_FLOW_LLM_MODE == "openai"
            and not self.OPENAI_API_KEY
            and not self.get_openai_api_keys()
        ):
            raise ValueError("OPENAI_API_KEY must be set when ORG_FLOW_LLM_MODE=openai")

        if bool(self.SUPABASE_URL) ^ bool(self.SUPABASE_KEY):
            raise ValueError(
                "Both SUPABASE_URL and SUPABASE_KEY must be set together"
            )
        if self.SUPABASE_KEY and self.ENVIRONMENT != "test":
            key_role = supabase_key_jwt_role(self.SUPABASE_KEY)
            if key_role == "anon":
                raise ValueError(
                    "SUPABASE_KEY must be the Supabase service_role secret "
                    "(Project Settings → API), not the anon/public key"
                )
        if self.OPENAI_ACTIVE_KEY_INDEX < 0:
            raise ValueError("OPENAI_ACTIVE_KEY_INDEX must be >= 0")
        self.get_ai_fallback_providers()
        if self.CONFIG_CACHE_TTL_SECONDS <= 0:
            raise ValueError("CONFIG_CACHE_TTL_SECONDS must be > 0")
        if self.IDEMPOTENCY_TTL_SECONDS <= 0:
            raise ValueError("IDEMPOTENCY_TTL_SECONDS must be > 0")
        if not self.IDEMPOTENCY_HEADER.strip():
            raise ValueError("IDEMPOTENCY_HEADER must be non-empty")
        if self.DB_RETRY_MAX_ATTEMPTS <= 0:
            raise ValueError("DB_RETRY_MAX_ATTEMPTS must be > 0")
        if self.DB_RETRY_BASE_DELAY_SECONDS < 0:
            raise ValueError("DB_RETRY_BASE_DELAY_SECONDS must be >= 0")
        if self.DB_OPERATION_TIMEOUT_SECONDS <= 0:
            raise ValueError("DB_OPERATION_TIMEOUT_SECONDS must be > 0")
        if not self.AUTH_JWT_SECRET.strip():
            raise ValueError("AUTH_JWT_SECRET must be non-empty")
        if not self.AUTH_JWT_ALGORITHM.strip():
            raise ValueError("AUTH_JWT_ALGORITHM must be non-empty")
        if self.AUTH_SESSION_TIMEOUT_MINUTES <= 0:
            raise ValueError("AUTH_SESSION_TIMEOUT_MINUTES must be > 0")
        if self.AUTH_REFRESH_TOKEN_TTL_MINUTES <= 0:
            raise ValueError("AUTH_REFRESH_TOKEN_TTL_MINUTES must be > 0")
        return self

    def get_openai_api_keys(self) -> list[str]:
        if not self.OPENAI_API_KEYS:
            return []
        return [part.strip() for part in self.OPENAI_API_KEYS.split(",") if part.strip()]

    def get_active_openai_api_key(self) -> Optional[str]:
        key_ring = self.get_openai_api_keys()
        if key_ring:
            index = self.OPENAI_ACTIVE_KEY_INDEX % len(key_ring)
            return key_ring[index]
        return self.OPENAI_API_KEY

    def get_ai_fallback_providers(self) -> list[str]:
        if not self.AI_FALLBACK_PROVIDERS:
            return []
        values = [
            part.strip().lower()
            for part in self.AI_FALLBACK_PROVIDERS.split(",")
            if part.strip()
        ]
        for value in values:
            if value not in ALLOWED_AI_PROVIDERS:
                raise ValueError(
                    f"AI_FALLBACK_PROVIDERS contains unsupported provider: {value}"
                )
        return values

    def get_ai_provider_chain(self) -> list[str]:
        ordered = [self.AI_PROVIDER, *self.get_ai_fallback_providers()]
        deduplicated: list[str] = []
        for provider in ordered:
            if provider not in deduplicated:
                deduplicated.append(provider)
        return deduplicated

    def get_cors_extra_origins(self) -> list[str]:
        if not self.CORS_EXTRA_ORIGINS:
            return []
        origins: list[str] = []
        for part in self.CORS_EXTRA_ORIGINS.split(","):
            normalized = part.strip().rstrip("/")
            if normalized:
                origins.append(normalized)
        return origins


def _env(name: str, default: str | None = None) -> str | None:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    return raw


def load_settings() -> Settings:
    try:
        environment = (_env("ENVIRONMENT", "local") or "local").strip().lower()

        # Base .env + environment-specific overrides.
        load_dotenv()
        load_dotenv(f".env.{environment}", override=True)

        data = {
            "ENVIRONMENT": environment,
            "FRONTEND_URL": os.getenv("FRONTEND_URL", "http://localhost:3000"),
            "AI_PROVIDER": os.getenv("AI_PROVIDER", "ollama"),
            "AI_FALLBACK_PROVIDERS": os.getenv("AI_FALLBACK_PROVIDERS"),
            "DEFAULT_AI_MODEL": os.getenv("DEFAULT_AI_MODEL", "mistral"),
            "AI_MAX_RETRIES": int(os.getenv("AI_MAX_RETRIES", "2")),
            "ORG_FLOW_LLM_MODE": _env("ORG_FLOW_LLM_MODE", "mock"),
            "OPENAI_MODEL": os.getenv("OPENAI_MODEL", "gpt-5.5"),
            "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
            "OPENAI_API_KEYS": os.getenv("OPENAI_API_KEYS"),
            "OPENAI_ACTIVE_KEY_INDEX": int(os.getenv("OPENAI_ACTIVE_KEY_INDEX", "0")),
            "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY"),
            "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY"),
            "LOG_LEVEL": os.getenv("LOG_LEVEL", "INFO"),
            "RESEND_API_KEY": os.getenv("RESEND_API_KEY"),
            "SUPABASE_URL": os.getenv("SUPABASE_URL"),
            "SUPABASE_KEY": os.getenv("SUPABASE_KEY"),
            "EMAIL_PROVIDER": os.getenv("EMAIL_PROVIDER", "gmail"),
            "CONFIG_CACHE_TTL_SECONDS": int(os.getenv("CONFIG_CACHE_TTL_SECONDS", "60")),
            "IDEMPOTENCY_TTL_SECONDS": int(os.getenv("IDEMPOTENCY_TTL_SECONDS", "3600")),
            "IDEMPOTENCY_HEADER": os.getenv("IDEMPOTENCY_HEADER", "X-Idempotency-Key"),
            "DB_RETRY_MAX_ATTEMPTS": int(os.getenv("DB_RETRY_MAX_ATTEMPTS", "3")),
            "DB_RETRY_BASE_DELAY_SECONDS": float(
                os.getenv("DB_RETRY_BASE_DELAY_SECONDS", "0.1")
            ),
            "DB_OPERATION_TIMEOUT_SECONDS": float(
                os.getenv("DB_OPERATION_TIMEOUT_SECONDS", "5.0")
            ),
            "AUTH_JWT_SECRET": _env(
                "AUTH_JWT_SECRET",
                "dev-secret-change-me-at-least-32-chars",
            ),
            "AUTH_JWT_ALGORITHM": _env("AUTH_JWT_ALGORITHM", "HS256"),
            "AUTH_SESSION_TIMEOUT_MINUTES": int(
                os.getenv("AUTH_SESSION_TIMEOUT_MINUTES", "60")
            ),
            "AUTH_REFRESH_TOKEN_TTL_MINUTES": int(
                os.getenv("AUTH_REFRESH_TOKEN_TTL_MINUTES", "1440")
            ),
            "CORS_EXTRA_ORIGINS": os.getenv("CORS_EXTRA_ORIGINS"),
            "FEATURE_FLAGS": FeatureFlags.from_env(),
        }

        return Settings(**data)
    except ValidationError as exc:
        from app.exceptions.exceptions import ConfigurationError

        raise ConfigurationError(
            message="Configuration validation failed",
            details={"errors": exc.errors()},
        )


settings = load_settings()
