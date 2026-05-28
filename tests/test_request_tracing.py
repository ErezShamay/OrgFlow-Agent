from uuid import UUID

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.exceptions.middleware import (
    GlobalExceptionHandler,
    RequestLoggingMiddleware,
)


def create_test_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(GlobalExceptionHandler)

    @app.get("/success")
    def success():
        return {"ok": True}

    @app.get("/failure")
    def failure():
        raise ValueError("invalid request")

    return app


def test_request_tracing_preserves_incoming_ids():
    client = TestClient(create_test_app())

    response = client.get(
        "/success",
        headers={
            "X-Request-ID": "req-123",
            "X-Trace-ID": "trace-456",
        },
    )

    assert response.status_code == 200
    assert response.json() == {"ok": True}
    assert response.headers["X-Request-ID"] == "req-123"
    assert response.headers["X-Trace-ID"] == "trace-456"


def test_request_tracing_generates_missing_ids():
    client = TestClient(create_test_app())

    response = client.get("/success")

    assert response.status_code == 200
    request_id = response.headers["X-Request-ID"]
    trace_id = response.headers["X-Trace-ID"]

    assert request_id
    assert trace_id
    UUID(request_id)
    UUID(trace_id)


def test_error_response_includes_trace_ids_and_metadata():
    client = TestClient(create_test_app())

    response = client.get(
        "/failure",
        headers={
            "X-Request-ID": "req-123",
            "X-Trace-ID": "trace-456",
        },
    )

    assert response.status_code == 400
    payload = response.json()
    assert payload["success"] is False
    assert payload["metadata"]["request_id"] == "req-123"
    assert payload["metadata"]["trace_id"] == "trace-456"
    assert response.headers["X-Request-ID"] == "req-123"
    assert response.headers["X-Trace-ID"] == "trace-456"
