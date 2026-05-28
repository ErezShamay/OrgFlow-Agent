from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from app.config.settings import Settings
from app.exceptions.idempotency_middleware import IdempotencyMiddleware
from app.main import app


def create_idempotency_test_app() -> FastAPI:
    test_app = FastAPI()
    test_app.add_middleware(IdempotencyMiddleware)

    @test_app.post("/payments")
    async def create_payment(payload: dict):
        return JSONResponse({"ok": True, "payload": payload}, status_code=201)

    return test_app


def test_secret_rotation_uses_ring_key_by_index():
    settings = Settings(
        ENVIRONMENT="test",
        FRONTEND_URL="http://localhost:3000",
        AI_PROVIDER="ollama",
        DEFAULT_AI_MODEL="mistral",
        AI_MAX_RETRIES=1,
        ORG_FLOW_LLM_MODE="openai",
        OPENAI_MODEL="gpt-5.5",
        OPENAI_API_KEY=None,
        OPENAI_API_KEYS="key-a,key-b,key-c",
        OPENAI_ACTIVE_KEY_INDEX=4,
        LOG_LEVEL="INFO",
        RESEND_API_KEY=None,
        SUPABASE_URL=None,
        SUPABASE_KEY=None,
        EMAIL_PROVIDER="gmail",
        FEATURE_FLAGS={
            "enable_notifications": True,
            "enable_automation": True,
            "enable_ai_review": True,
            "enable_email_delivery": True,
        },
    )

    assert settings.get_openai_api_keys() == ["key-a", "key-b", "key-c"]
    assert settings.get_active_openai_api_key() == "key-b"


def test_idempotency_replays_successful_write_response():
    client = TestClient(create_idempotency_test_app())
    headers = {"X-Idempotency-Key": "payment-1"}

    first = client.post("/payments", json={"amount": 100}, headers=headers)
    second = client.post("/payments", json={"amount": 100}, headers=headers)

    assert first.status_code == 201
    assert second.status_code == 201
    assert second.headers["X-Idempotency-Replayed"] == "true"
    assert second.json() == first.json()


def test_idempotency_rejects_same_key_with_different_payload():
    client = TestClient(create_idempotency_test_app())
    headers = {"X-Idempotency-Key": "payment-2"}

    first = client.post("/payments", json={"amount": 100}, headers=headers)
    second = client.post("/payments", json={"amount": 200}, headers=headers)

    assert first.status_code == 201
    assert second.status_code == 409
    assert second.json()["error"]["code"] == "IDEMPOTENCY_KEY_REUSED"


def test_config_and_secret_rotation_endpoints_exist():
    client = TestClient(app)

    config_response = client.get("/config")
    rotation_response = client.get("/secrets/rotation-status")

    assert config_response.status_code == 200
    assert rotation_response.status_code == 200
    assert "config" in config_response.json()
    assert "openai" in rotation_response.json()
