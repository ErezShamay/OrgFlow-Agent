from pathlib import Path

from app.config.settings import load_settings


def test_load_settings_reads_environment_specific_env_file(
    monkeypatch,
    tmp_path: Path,
):
    monkeypatch.chdir(tmp_path)

    (tmp_path / ".env").write_text(
        "\n".join(
            [
                "ENVIRONMENT=local",
                "FRONTEND_URL=http://localhost:3000",
                "AI_PROVIDER=ollama",
                "DEFAULT_AI_MODEL=mistral",
                "AI_MAX_RETRIES=2",
                "ORG_FLOW_LLM_MODE=mock",
                "OPENAI_MODEL=gpt-5.5",
                "LOG_LEVEL=INFO",
                "EMAIL_PROVIDER=gmail",
                "FEATURE_AUTOMATION=true",
            ]
        ),
        encoding="utf-8",
    )
    (tmp_path / ".env.local").write_text(
        "FEATURE_AUTOMATION=false\n",
        encoding="utf-8",
    )

    monkeypatch.setenv("ENVIRONMENT", "local")
    settings = load_settings()

    assert settings.ENVIRONMENT == "local"
    assert settings.FEATURE_FLAGS.enable_automation is False


def test_load_settings_parses_feature_flags_from_environment(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "local")
    monkeypatch.setenv("FRONTEND_URL", "http://localhost:3000")
    monkeypatch.setenv("AI_PROVIDER", "ollama")
    monkeypatch.setenv("DEFAULT_AI_MODEL", "mistral")
    monkeypatch.setenv("AI_MAX_RETRIES", "2")
    monkeypatch.setenv("ORG_FLOW_LLM_MODE", "mock")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-5.5")
    monkeypatch.setenv("LOG_LEVEL", "INFO")
    monkeypatch.setenv("EMAIL_PROVIDER", "gmail")
    monkeypatch.setenv("FEATURE_NOTIFICATIONS", "false")
    monkeypatch.setenv("FEATURE_AUTOMATION", "0")
    monkeypatch.setenv("FEATURE_AI_REVIEW", "true")
    monkeypatch.setenv("FEATURE_EMAIL_DELIVERY", "yes")

    settings = load_settings()

    assert settings.FEATURE_FLAGS.enable_notifications is False
    assert settings.FEATURE_FLAGS.enable_automation is False
    assert settings.FEATURE_FLAGS.enable_ai_review is True
    assert settings.FEATURE_FLAGS.enable_email_delivery is True


def test_load_settings_parses_cors_extra_origins(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "local")
    monkeypatch.setenv("FRONTEND_URL", "http://localhost:3000")
    monkeypatch.setenv("AI_PROVIDER", "ollama")
    monkeypatch.setenv("DEFAULT_AI_MODEL", "mistral")
    monkeypatch.setenv("AI_MAX_RETRIES", "2")
    monkeypatch.setenv("ORG_FLOW_LLM_MODE", "mock")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-5.5")
    monkeypatch.setenv("LOG_LEVEL", "INFO")
    monkeypatch.setenv("EMAIL_PROVIDER", "gmail")
    monkeypatch.setenv(
        "CORS_EXTRA_ORIGINS",
        "https://app.vercel.app/, https://preview.vercel.app",
    )

    settings = load_settings()

    assert settings.get_cors_extra_origins() == [
        "https://app.vercel.app",
        "https://preview.vercel.app",
    ]
