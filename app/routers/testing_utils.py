"""Testing / QA utility routes.

Extracted from app/main.py during the 2026-07 architecture-modularization
refactor. Shared service singletons live in app/dependencies.py; shared
request models live in app/schemas/api_requests.py.
"""
from __future__ import annotations


from fastapi import APIRouter
import app.dependencies as deps


router = APIRouter()


@router.get("/testing/dashboard")
def get_testing_dashboard():
    return deps.testing_dashboard_service.get_dashboard()


@router.get("/testing/unit/config")
def get_testing_unit_config():
    return deps.testing_dashboard_service.get_unit_config()


@router.get("/testing/unit/suites")
def list_testing_unit_suites():
    return deps.testing_dashboard_service.list_unit_suites()


@router.get("/testing/unit/coverage")
def evaluate_testing_unit_coverage(coverage_percent: float = 0.0):
    return deps.testing_dashboard_service.evaluate_unit_coverage(
        coverage_percent=coverage_percent,
    )


@router.get("/testing/unit/validate")
def validate_testing_unit():
    return deps.testing_dashboard_service.validate_unit_tests()


@router.get("/testing/integration/config")
def get_testing_integration_config():
    return deps.testing_dashboard_service.get_integration_config()


@router.get("/testing/integration/scenarios")
def list_testing_integration_scenarios():
    return deps.testing_dashboard_service.list_integration_scenarios()


@router.get("/testing/integration/validate")
def validate_testing_integration():
    return deps.testing_dashboard_service.validate_integration_tests()


@router.get("/testing/api/config")
def get_testing_api_config():
    return deps.testing_dashboard_service.get_api_config()


@router.get("/testing/api/endpoints")
def list_testing_api_endpoints():
    return deps.testing_dashboard_service.list_api_endpoints()


@router.get("/testing/api/simulate")
def simulate_testing_api_request(
    method: str = "GET",
    path: str = "/health",
    status_code: int = 200,
):
    return deps.testing_dashboard_service.simulate_api_request(
        method=method,
        path=path,
        status_code=status_code,
    )


@router.get("/testing/api/validate")
def validate_testing_api():
    return deps.testing_dashboard_service.validate_api_tests()


@router.get("/testing/frontend/config")
def get_testing_frontend_config():
    return deps.testing_dashboard_service.get_frontend_config()


@router.get("/testing/frontend/suites")
def list_testing_frontend_suites():
    return deps.testing_dashboard_service.list_frontend_suites()


@router.get("/testing/frontend/validate")
def validate_testing_frontend():
    return deps.testing_dashboard_service.validate_frontend_tests()


@router.get("/testing/playwright/config")
def get_testing_playwright_config():
    return deps.testing_dashboard_service.get_playwright_config()


@router.get("/testing/playwright/flows")
def list_testing_playwright_flows():
    return deps.testing_dashboard_service.list_playwright_flows()


@router.get("/testing/playwright/evaluate")
def evaluate_testing_playwright_flow(flow_id: str = "login"):
    return deps.testing_dashboard_service.evaluate_playwright_flow(flow_id=flow_id)


@router.get("/testing/playwright/validate")
def validate_testing_playwright():
    return deps.testing_dashboard_service.validate_playwright()


@router.get("/testing/automation/config")
def get_testing_automation_config():
    return deps.testing_dashboard_service.get_automation_config()


@router.get("/testing/automation/tests")
def list_testing_automation_tests():
    return deps.testing_dashboard_service.list_automation_tests()


@router.get("/testing/automation/validate")
def validate_testing_automation():
    return deps.testing_dashboard_service.validate_automation_tests()


@router.get("/testing/ai-mock/config")
def get_testing_ai_mock_config():
    return deps.testing_dashboard_service.get_ai_mock_config()


@router.get("/testing/ai-mock/fixtures")
def list_testing_ai_mock_fixtures():
    return deps.testing_dashboard_service.list_ai_mock_fixtures()


@router.get("/testing/ai-mock/simulate")
def simulate_testing_ai_mock(
    provider: str = "openai",
    fixture_id: str = "review_summary",
):
    return deps.testing_dashboard_service.simulate_ai_mock(
        provider=provider,
        fixture_id=fixture_id,
    )


@router.get("/testing/ai-mock/validate")
def validate_testing_ai_mock():
    return deps.testing_dashboard_service.validate_ai_mock_tests()


@router.get("/testing/load/config")
def get_testing_load_config():
    return deps.testing_dashboard_service.get_load_config()


@router.get("/testing/load/scenarios")
def list_testing_load_scenarios():
    return deps.testing_dashboard_service.list_load_scenarios()


@router.get("/testing/load/evaluate")
def evaluate_testing_load(
    p95_ms: float = 0.0,
    error_rate_percent: float = 0.0,
):
    return deps.testing_dashboard_service.evaluate_load_results(
        p95_ms=p95_ms,
        error_rate_percent=error_rate_percent,
    )


@router.get("/testing/load/validate")
def validate_testing_load():
    return deps.testing_dashboard_service.validate_load_testing()


@router.get("/testing/recovery/config")
def get_testing_recovery_config():
    return deps.testing_dashboard_service.get_recovery_config()


@router.get("/testing/recovery/scenarios")
def list_testing_recovery_scenarios():
    return deps.testing_dashboard_service.list_recovery_scenarios()


@router.get("/testing/recovery/simulate")
def simulate_testing_recovery(scenario_id: str = "dlq_replay"):
    return deps.testing_dashboard_service.simulate_recovery(scenario_id=scenario_id)


@router.get("/testing/recovery/validate")
def validate_testing_recovery():
    return deps.testing_dashboard_service.validate_recovery_testing()


@router.get("/testing/chaos/config")
def get_testing_chaos_config():
    return deps.testing_dashboard_service.get_chaos_config()


@router.get("/testing/chaos/experiments")
def list_testing_chaos_experiments():
    return deps.testing_dashboard_service.list_chaos_experiments()


@router.get("/testing/chaos/evaluate")
def evaluate_testing_chaos_safety(experiment_id: str = "kill_api_pod"):
    return deps.testing_dashboard_service.evaluate_chaos_safety(
        experiment_id=experiment_id,
    )


@router.get("/testing/chaos/validate")
def validate_testing_chaos():
    return deps.testing_dashboard_service.validate_chaos_testing()


@router.get("/testing/contract/config")
def get_testing_contract_config():
    return deps.testing_dashboard_service.get_contract_config()


@router.get("/testing/contract/contracts")
def list_testing_contracts():
    return deps.testing_dashboard_service.list_contracts()


@router.get("/testing/contract/validate-change")
def validate_testing_contract_change(change_type: str = "add_optional_field"):
    return deps.testing_dashboard_service.validate_contract_change(
        change_type=change_type,
    )


@router.get("/testing/contract/validate")
def validate_testing_contract():
    return deps.testing_dashboard_service.validate_contract_testing()


@router.get("/testing/security/config")
def get_testing_security_config():
    return deps.testing_dashboard_service.get_security_test_config()


@router.get("/testing/security/cases")
def list_testing_security_cases():
    return deps.testing_dashboard_service.list_security_test_cases()


@router.get("/testing/security/run")
def run_testing_security_case(case_id: str = "jwt_expired"):
    return deps.testing_dashboard_service.run_security_test_case(case_id=case_id)


@router.get("/testing/security/validate")
def validate_testing_security():
    return deps.testing_dashboard_service.validate_security_testing()


@router.get("/testing/performance/config")
def get_testing_performance_config():
    return deps.testing_dashboard_service.get_performance_test_config()


@router.get("/testing/performance/benchmarks")
def list_testing_performance_benchmarks():
    return deps.testing_dashboard_service.list_performance_benchmarks()


@router.get("/testing/performance/evaluate")
def evaluate_testing_performance_benchmark(
    benchmark_id: str = "project_list",
    p95_ms: float = 0.0,
):
    return deps.testing_dashboard_service.evaluate_performance_benchmark(
        benchmark_id=benchmark_id,
        p95_ms=p95_ms,
    )


@router.get("/testing/performance/validate")
def validate_testing_performance():
    return deps.testing_dashboard_service.validate_performance_testing()


@router.get("/testing/regression/config")
def get_testing_regression_config():
    return deps.testing_dashboard_service.get_regression_config()


@router.get("/testing/regression/suites")
def list_testing_regression_suites():
    return deps.testing_dashboard_service.list_regression_suites()


@router.get("/testing/regression/compare")
def compare_testing_regression_baseline(
    suite_id: str = "api_responses",
    changed_snapshots: int = 0,
):
    return deps.testing_dashboard_service.compare_regression_baseline(
        suite_id=suite_id,
        changed_snapshots=changed_snapshots,
    )


@router.get("/testing/regression/validate")
def validate_testing_regression():
    return deps.testing_dashboard_service.validate_regression_testing()


