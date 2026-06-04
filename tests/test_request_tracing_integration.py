from uuid import UUID

from fastapi.testclient import TestClient

from app.main import app


def ensure_test_routes():
    if not any(route.path == "/__test/error" for route in app.routes):

        @app.get("/__test/error")
        def test_error_route():
            raise ValueError("invalid request")


def test_app_root_preserves_incoming_trace_headers():
    ensure_test_routes()
    client = TestClient(app)

    response = client.get(
        "/",
        headers={
            "X-Request-ID": "req-123",
            "X-Trace-ID": "trace-456",
        },
    )

    assert response.status_code == 200
    assert response.json() == {"message": "OrgFlow AI Agent is running"}
    assert response.headers["X-Request-ID"] == "req-123"
    assert response.headers["X-Trace-ID"] == "trace-456"


def test_app_root_generates_missing_trace_headers():
    client = TestClient(app)

    response = client.get("/")

    assert response.status_code == 200
    assert UUID(response.headers["X-Request-ID"])
    assert UUID(response.headers["X-Trace-ID"])


def test_healthcheck_endpoint_returns_ok_and_trace_headers():
    client = TestClient(app)

    response = client.get("/healthcheck")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["service"] == "orgflow-agent"
    assert payload["environment"] in {"local", "test"}
    assert UUID(response.headers["X-Request-ID"])


def test_health_alias_matches_healthcheck():
    client = TestClient(app)

    health = client.get("/health")
    healthcheck = client.get("/healthcheck")

    assert health.status_code == 200
    assert health.json() == healthcheck.json()
    assert UUID(health.headers["X-Trace-ID"])


def test_readiness_endpoint_returns_ready_when_startup_has_run():
    with TestClient(app) as client:
        response = client.get("/readiness")

    assert response.status_code == 200
    assert response.json()["status"] == "ready"
    assert response.json()["checks"]["startup_complete"] is True
    assert response.json()["checks"]["scheduler_running"] is True
    assert response.json()["checks"]["automation_enabled"] is True


def test_liveness_endpoint_returns_alive_and_trace_headers():
    client = TestClient(app)

    response = client.get("/liveness")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "alive"
    assert payload["service"] == "orgflow-agent"
    assert payload["environment"] == "local"
    assert payload["timestamp"]
    assert UUID(response.headers["X-Request-ID"])
    assert UUID(response.headers["X-Trace-ID"])


def test_shutdown_event_stops_scheduler_gracefully():
    from app.automation.scheduler import scheduler

    with TestClient(app):
        assert scheduler.running is True

    assert scheduler.running is False


def test_global_exception_handler_returns_trace_headers_for_value_error():
    ensure_test_routes()
    client = TestClient(app)

    response = client.get(
        "/__test/error",
        headers={
            "X-Request-ID": "req-abc",
            "X-Trace-ID": "trace-def",
        },
    )

    assert response.status_code == 400
    assert response.headers["X-Request-ID"] == "req-abc"
    assert response.headers["X-Trace-ID"] == "trace-def"

    payload = response.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "VALIDATION_ERROR"
    assert payload["metadata"]["request_id"] == "req-abc"
    assert payload["metadata"]["trace_id"] == "trace-def"


def test_feature_flags_endpoint_returns_runtime_flags():
    client = TestClient(app)

    response = client.get("/feature-flags")

    assert response.status_code == 200
    payload = response.json()
    assert payload["environment"] == "local"
    assert payload["flags"]["enable_automation"] is True
    assert payload["flags"]["enable_notifications"] is True
