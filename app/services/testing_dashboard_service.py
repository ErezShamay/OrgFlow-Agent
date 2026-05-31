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
from app.services.unit_tests_service import UnitTestsService


class TestingDashboardService:
    def __init__(
        self,
        unit_tests_service: UnitTestsService | None = None,
        integration_tests_service: IntegrationTestsService | None = None,
        api_tests_service: ApiTestsService | None = None,
        frontend_tests_service: FrontendTestsService | None = None,
        playwright_service: PlaywrightE2eService | None = None,
        automation_tests_service: AutomationTestsService | None = None,
        ai_mock_tests_service: AiMockTestsService | None = None,
        load_testing_service: LoadTestingService | None = None,
        recovery_testing_service: RecoveryTestingService | None = None,
        chaos_testing_service: ChaosTestingService | None = None,
        contract_testing_service: ContractTestingService | None = None,
        security_testing_service: SecurityTestingService | None = None,
        performance_testing_service: PerformanceTestingService | None = None,
        regression_testing_service: RegressionTestingService | None = None,
    ):
        self.unit_tests_service = unit_tests_service or UnitTestsService()
        self.integration_tests_service = (
            integration_tests_service or IntegrationTestsService()
        )
        self.api_tests_service = api_tests_service or ApiTestsService()
        self.frontend_tests_service = frontend_tests_service or FrontendTestsService()
        self.playwright_service = playwright_service or PlaywrightE2eService()
        self.automation_tests_service = (
            automation_tests_service or AutomationTestsService()
        )
        self.ai_mock_tests_service = ai_mock_tests_service or AiMockTestsService()
        self.load_testing_service = load_testing_service or LoadTestingService()
        self.recovery_testing_service = (
            recovery_testing_service or RecoveryTestingService()
        )
        self.chaos_testing_service = chaos_testing_service or ChaosTestingService()
        self.contract_testing_service = (
            contract_testing_service or ContractTestingService()
        )
        self.security_testing_service = (
            security_testing_service or SecurityTestingService()
        )
        self.performance_testing_service = (
            performance_testing_service or PerformanceTestingService()
        )
        self.regression_testing_service = (
            regression_testing_service or RegressionTestingService()
        )

    def get_dashboard(self) -> dict:
        validations = [
            self.unit_tests_service.validate_setup()["valid"],
            self.integration_tests_service.validate_setup()["valid"],
            self.api_tests_service.validate_setup()["valid"],
            self.frontend_tests_service.validate_setup()["valid"],
            self.playwright_service.validate_setup()["valid"],
            self.automation_tests_service.validate_setup()["valid"],
            self.ai_mock_tests_service.validate_setup()["valid"],
            self.load_testing_service.validate_setup()["valid"],
            self.recovery_testing_service.validate_setup()["valid"],
            self.chaos_testing_service.validate_setup()["valid"],
            self.contract_testing_service.validate_setup()["valid"],
            self.security_testing_service.validate_setup()["valid"],
            self.performance_testing_service.validate_setup()["valid"],
            self.regression_testing_service.validate_setup()["valid"],
        ]

        return {
            "unit_tests": self.unit_tests_service.get_config(),
            "integration_tests": self.integration_tests_service.get_config(),
            "api_tests": self.api_tests_service.get_config(),
            "frontend_tests": self.frontend_tests_service.get_config(),
            "playwright_e2e": self.playwright_service.get_config(),
            "automation_tests": self.automation_tests_service.get_config(),
            "ai_mock_tests": self.ai_mock_tests_service.get_config(),
            "load_testing": self.load_testing_service.get_config(),
            "recovery_testing": self.recovery_testing_service.get_config(),
            "chaos_testing": self.chaos_testing_service.get_config(),
            "contract_testing": self.contract_testing_service.get_config(),
            "security_testing": self.security_testing_service.get_config(),
            "performance_testing": self.performance_testing_service.get_config(),
            "regression_testing": self.regression_testing_service.get_config(),
            "test_ready": all(validations),
        }

    def get_unit_config(self) -> dict:
        return self.unit_tests_service.get_config()

    def list_unit_suites(self) -> dict:
        return self.unit_tests_service.list_suites()

    def evaluate_unit_coverage(self, *, coverage_percent: float) -> dict:
        return self.unit_tests_service.evaluate_coverage(
            coverage_percent=coverage_percent
        )

    def validate_unit_tests(self) -> dict:
        return self.unit_tests_service.validate_setup()

    def get_integration_config(self) -> dict:
        return self.integration_tests_service.get_config()

    def list_integration_scenarios(self) -> dict:
        return self.integration_tests_service.list_scenarios()

    def validate_integration_tests(self) -> dict:
        return self.integration_tests_service.validate_setup()

    def get_api_config(self) -> dict:
        return self.api_tests_service.get_config()

    def list_api_endpoints(self) -> dict:
        return self.api_tests_service.list_endpoints()

    def simulate_api_request(
        self,
        *,
        method: str,
        path: str,
        status_code: int = 200,
    ) -> dict:
        return self.api_tests_service.simulate_request(
            method=method,
            path=path,
            status_code=status_code,
        )

    def validate_api_tests(self) -> dict:
        return self.api_tests_service.validate_setup()

    def get_frontend_config(self) -> dict:
        return self.frontend_tests_service.get_config()

    def list_frontend_suites(self) -> dict:
        return self.frontend_tests_service.list_suites()

    def validate_frontend_tests(self) -> dict:
        return self.frontend_tests_service.validate_setup()

    def get_playwright_config(self) -> dict:
        return self.playwright_service.get_config()

    def list_playwright_flows(self) -> dict:
        return self.playwright_service.list_flows()

    def evaluate_playwright_flow(self, *, flow_id: str) -> dict:
        return self.playwright_service.evaluate_flow_readiness(flow_id=flow_id)

    def validate_playwright(self) -> dict:
        return self.playwright_service.validate_setup()

    def get_automation_config(self) -> dict:
        return self.automation_tests_service.get_config()

    def list_automation_tests(self) -> dict:
        return self.automation_tests_service.list_workflow_tests()

    def validate_automation_tests(self) -> dict:
        return self.automation_tests_service.validate_setup()

    def get_ai_mock_config(self) -> dict:
        return self.ai_mock_tests_service.get_config()

    def list_ai_mock_fixtures(self) -> dict:
        return self.ai_mock_tests_service.list_fixtures()

    def simulate_ai_mock(
        self,
        *,
        provider: str,
        fixture_id: str,
    ) -> dict:
        return self.ai_mock_tests_service.simulate_call(
            provider=provider,
            fixture_id=fixture_id,
        )

    def validate_ai_mock_tests(self) -> dict:
        return self.ai_mock_tests_service.validate_setup()

    def get_load_config(self) -> dict:
        return self.load_testing_service.get_config()

    def list_load_scenarios(self) -> dict:
        return self.load_testing_service.list_scenarios()

    def evaluate_load_results(
        self,
        *,
        p95_ms: float,
        error_rate_percent: float,
    ) -> dict:
        return self.load_testing_service.evaluate_results(
            p95_ms=p95_ms,
            error_rate_percent=error_rate_percent,
        )

    def validate_load_testing(self) -> dict:
        return self.load_testing_service.validate_setup()

    def get_recovery_config(self) -> dict:
        return self.recovery_testing_service.get_config()

    def list_recovery_scenarios(self) -> dict:
        return self.recovery_testing_service.list_scenarios()

    def simulate_recovery(self, *, scenario_id: str) -> dict:
        return self.recovery_testing_service.simulate_recovery(
            scenario_id=scenario_id
        )

    def validate_recovery_testing(self) -> dict:
        return self.recovery_testing_service.validate_setup()

    def get_chaos_config(self) -> dict:
        return self.chaos_testing_service.get_config()

    def list_chaos_experiments(self) -> dict:
        return self.chaos_testing_service.list_experiments()

    def evaluate_chaos_safety(self, *, experiment_id: str) -> dict:
        return self.chaos_testing_service.evaluate_experiment_safety(
            experiment_id=experiment_id
        )

    def validate_chaos_testing(self) -> dict:
        return self.chaos_testing_service.validate_setup()

    def get_contract_config(self) -> dict:
        return self.contract_testing_service.get_config()

    def list_contracts(self) -> dict:
        return self.contract_testing_service.list_contracts()

    def validate_contract_change(self, *, change_type: str) -> dict:
        return self.contract_testing_service.validate_schema_change(
            change_type=change_type
        )

    def validate_contract_testing(self) -> dict:
        return self.contract_testing_service.validate_setup()

    def get_security_test_config(self) -> dict:
        return self.security_testing_service.get_config()

    def list_security_test_cases(self) -> dict:
        return self.security_testing_service.list_test_cases()

    def run_security_test_case(self, *, case_id: str) -> dict:
        return self.security_testing_service.run_case(case_id=case_id)

    def validate_security_testing(self) -> dict:
        return self.security_testing_service.validate_setup()

    def get_performance_test_config(self) -> dict:
        return self.performance_testing_service.get_config()

    def list_performance_benchmarks(self) -> dict:
        return self.performance_testing_service.list_benchmarks()

    def evaluate_performance_benchmark(
        self,
        *,
        benchmark_id: str,
        p95_ms: float,
    ) -> dict:
        return self.performance_testing_service.evaluate_benchmark(
            benchmark_id=benchmark_id,
            p95_ms=p95_ms,
        )

    def validate_performance_testing(self) -> dict:
        return self.performance_testing_service.validate_setup()

    def get_regression_config(self) -> dict:
        return self.regression_testing_service.get_config()

    def list_regression_suites(self) -> dict:
        return self.regression_testing_service.list_suites()

    def compare_regression_baseline(
        self,
        *,
        suite_id: str,
        changed_snapshots: int = 0,
    ) -> dict:
        return self.regression_testing_service.compare_baseline(
            suite_id=suite_id,
            changed_snapshots=changed_snapshots,
        )

    def validate_regression_testing(self) -> dict:
        return self.regression_testing_service.validate_setup()
