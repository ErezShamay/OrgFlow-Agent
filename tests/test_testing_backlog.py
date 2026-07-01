from fastapi.testclient import TestClient

import app.main as main_module
from app.auth.jwt_service import JWTService
from app.main import app
from app.services.ai_mock_tests_service import AiMockTestsService
from app.services.api_tests_service import ApiTestsService
from app.services.automation_tests_service import AutomationTestsService
from app.services.chaos_testing_service import ChaosTestingService
from app.services.contract_testing_service import ContractTestingService
from app.services.frontend_tests_service import FrontendTestsService
from app.services.integration_tests_service import IntegrationTestsService
from app.services.load_testing_service import LoadTestingService
from app.services.performance_testing_service import PerformanceTestingService
from app.services.playwright_e2e_service import PlaywrightE2eService
from app.services.recovery_testing_service import RecoveryTestingService
from app.services.regression_testing_service import RegressionTestingService
from app.services.security_testing_service import SecurityTestingService
from app.services.testing_dashboard_service import TestingDashboardService
from app.services.unit_tests_service import UnitTestsService
import app.dependencies as deps


def build_dashboard():
    return TestingDashboardService()


def test_unit_tests():
    service = UnitTestsService()
    config = service.get_config()
    assert config["framework"] == "pytest"
    assert config["coverage_threshold_percent"] == 80

    coverage = service.evaluate_coverage(coverage_percent=85.0)
    assert coverage["met"] is True

    suites = service.list_suites()
    assert suites["total"] >= 3
    assert service.validate_setup()["valid"] is True


def test_integration_tests():
    service = IntegrationTestsService()
    config = service.get_config()
    assert config["database_fixture"] == "postgresql"

    scenarios = service.list_scenarios()
    assert scenarios["total"] >= 3
    assert service.validate_setup()["valid"] is True


def test_api_tests():
    service = ApiTestsService()
    config = service.get_config()
    assert config["client"] == "fastapi_testclient"

    result = service.simulate_request(method="GET", path="/health", status_code=200)
    assert result["passed"] is True

    endpoints = service.list_endpoints()
    assert endpoints["total"] >= 3
    assert service.validate_setup()["valid"] is True


def test_frontend_tests():
    service = FrontendTestsService()
    config = service.get_config()
    assert config["framework"] == "vitest"
    assert config["ui_package"] == "orgflow-ui"

    suites = service.list_suites()
    assert suites["suites"][0]["tests"] >= 1
    assert service.validate_setup()["valid"] is True


def test_playwright_e2e():
    service = PlaywrightE2eService()
    config = service.get_config()
    assert "chromium" in config["browsers"]

    flow = service.evaluate_flow_readiness(flow_id="login")
    assert flow["ready"] is True

    flows = service.list_flows()
    assert flows["total"] >= 3
    assert service.validate_setup()["valid"] is True


def test_automation_tests():
    service = AutomationTestsService()
    config = service.get_config()
    assert config["worker_simulation"] is True

    tests = service.list_workflow_tests()
    assert tests["total"] >= 3
    assert service.validate_setup()["valid"] is True


def test_ai_mock_tests():
    service = AiMockTestsService()
    config = service.get_config()
    assert "openai" in config["providers"]

    call = service.simulate_call(provider="openai", fixture_id="review_summary")
    assert call["mocked"] is True
    assert call["tokens"] == 120

    fixtures = service.list_fixtures()
    assert fixtures["total"] >= 3
    assert service.validate_setup()["valid"] is True


def test_load_testing():
    service = LoadTestingService()
    config = service.get_config()
    assert config["tool"] == "k6"

    passed = service.evaluate_results(p95_ms=400.0, error_rate_percent=0.5)
    assert passed["passed"] is True

    failed = service.evaluate_results(p95_ms=800.0, error_rate_percent=2.0)
    assert failed["passed"] is False
    assert service.validate_setup()["valid"] is True


def test_recovery_testing():
    service = RecoveryTestingService()
    config = service.get_config()
    assert "dead_letter" in config["domains"]

    recovery = service.simulate_recovery(scenario_id="dlq_replay")
    assert recovery["recovered"] is True

    scenarios = service.list_scenarios()
    assert scenarios["total"] >= 3
    assert service.validate_setup()["valid"] is True


def test_chaos_testing():
    service = ChaosTestingService()
    config = service.get_config()
    assert config["enabled_in_staging_only"] is True

    safety = service.evaluate_experiment_safety(experiment_id="kill_api_pod")
    assert safety["safe"] is True

    experiments = service.list_experiments()
    assert experiments["total"] >= 3
    assert service.validate_setup()["valid"] is True


def test_contract_testing():
    service = ContractTestingService()
    config = service.get_config()
    assert config["spec_format"] == "openapi_3.1"

    safe = service.validate_schema_change(change_type="add_optional_field")
    assert safe["breaking"] is False

    breaking = service.validate_schema_change(change_type="remove_field")
    assert breaking["breaking"] is True
    assert service.validate_setup()["valid"] is True


def test_security_testing():
    service = SecurityTestingService()
    config = service.get_config()
    assert config["ci_gate"] is True

    result = service.run_case(case_id="jwt_expired")
    assert result["passed"] is True

    cases = service.list_test_cases()
    assert cases["total"] >= 4
    assert service.validate_setup()["valid"] is True


def test_performance_testing():
    service = PerformanceTestingService()
    config = service.get_config()
    assert config["tool"] == "pytest-benchmark"

    passed = service.evaluate_benchmark(
        benchmark_id="project_list",
        p95_ms=150.0,
    )
    assert passed["passed"] is True

    benchmarks = service.list_benchmarks()
    assert benchmarks["total"] >= 2
    assert service.validate_setup()["valid"] is True


def test_regression_testing():
    service = RegressionTestingService()
    config = service.get_config()
    assert config["strategy"] == "snapshot_and_golden"

    compare = service.compare_baseline(suite_id="api_responses", changed_snapshots=0)
    assert compare["passed"] is True

    suites = service.list_suites()
    assert suites["total"] >= 2
    assert service.validate_setup()["valid"] is True


def test_testing_dashboard_aggregates_all_domains():
    dashboard = build_dashboard()
    result = dashboard.get_dashboard()

    assert result["test_ready"] is True
    assert result["unit_tests"]["framework"] == "pytest"
    assert result["frontend_tests"]["framework"] == "vitest"
    assert result["load_testing"]["tool"] == "k6"


def _auth_headers():
    token = JWTService().issue_access_token(
        user_id="user-1",
        org_id="org-1",
        role="ADMIN",
        token_id="testing-backlog-tests",
    )
    return {"Authorization": f"Bearer {token}", "X-Organization-ID": "org-1"}


def test_testing_api_endpoints(monkeypatch):
    dashboard = build_dashboard()
    monkeypatch.setattr(
        deps,
        "testing_dashboard_service",
        dashboard,
    )

    client = TestClient(app)
    headers = _auth_headers()

    get_endpoints = [
        "/testing/dashboard",
        "/testing/unit/config",
        "/testing/unit/suites",
        "/testing/unit/coverage",
        "/testing/unit/validate",
        "/testing/integration/config",
        "/testing/integration/scenarios",
        "/testing/integration/validate",
        "/testing/api/config",
        "/testing/api/endpoints",
        "/testing/api/simulate",
        "/testing/api/validate",
        "/testing/frontend/config",
        "/testing/frontend/suites",
        "/testing/frontend/validate",
        "/testing/playwright/config",
        "/testing/playwright/flows",
        "/testing/playwright/evaluate",
        "/testing/playwright/validate",
        "/testing/automation/config",
        "/testing/automation/tests",
        "/testing/automation/validate",
        "/testing/ai-mock/config",
        "/testing/ai-mock/fixtures",
        "/testing/ai-mock/simulate",
        "/testing/ai-mock/validate",
        "/testing/load/config",
        "/testing/load/scenarios",
        "/testing/load/evaluate",
        "/testing/load/validate",
        "/testing/recovery/config",
        "/testing/recovery/scenarios",
        "/testing/recovery/simulate",
        "/testing/recovery/validate",
        "/testing/chaos/config",
        "/testing/chaos/experiments",
        "/testing/chaos/evaluate",
        "/testing/chaos/validate",
        "/testing/contract/config",
        "/testing/contract/contracts",
        "/testing/contract/validate-change",
        "/testing/contract/validate",
        "/testing/security/config",
        "/testing/security/cases",
        "/testing/security/run",
        "/testing/security/validate",
        "/testing/performance/config",
        "/testing/performance/benchmarks",
        "/testing/performance/evaluate",
        "/testing/performance/validate",
        "/testing/regression/config",
        "/testing/regression/suites",
        "/testing/regression/compare",
        "/testing/regression/validate",
    ]

    for path in get_endpoints:
        response = client.get(path, headers=headers)
        assert response.status_code == 200, path

    dashboard_response = client.get(
        "/testing/dashboard",
        headers=headers,
    ).json()
    assert dashboard_response["test_ready"] is True
