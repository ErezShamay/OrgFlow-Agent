from app.services.api_abuse_protection_service import ApiAbuseProtectionService
from app.services.api_rate_limiting_service import ApiRateLimitingService
from app.services.auth_hardening_service import AuthHardeningService
from app.services.cors_hardening_service import CorsHardeningService
from app.services.dependency_vulnerability_scanning_service import (
    DependencyVulnerabilityScanningService,
)
from app.services.file_upload_validation_service import FileUploadValidationService
from app.services.owasp_review_service import OwaspReviewService
from app.services.permissions_validation_service import PermissionsValidationService
from app.services.secrets_management_service import SecretsManagementService
from app.services.security_audit_logging_service import SecurityAuditLoggingService
from app.services.security_malware_scanning_service import SecurityMalwareScanningService
from app.services.security_penetration_testing_service import (
    SecurityPenetrationTestingService,
)
from app.services.sql_injection_review_service import SqlInjectionReviewService
from app.services.supply_chain_security_service import SupplyChainSecurityService
from app.services.tenant_security_isolation_service import TenantSecurityIsolationService


class SecurityDashboardService:
    def __init__(
        self,
        rate_limiting_service: ApiRateLimitingService | None = None,
        cors_service: CorsHardeningService | None = None,
        secrets_service: SecretsManagementService | None = None,
        sql_review_service: SqlInjectionReviewService | None = None,
        upload_validation_service: FileUploadValidationService | None = None,
        malware_service: SecurityMalwareScanningService | None = None,
        auth_hardening_service: AuthHardeningService | None = None,
        audit_logging_service: SecurityAuditLoggingService | None = None,
        permissions_service: PermissionsValidationService | None = None,
        owasp_service: OwaspReviewService | None = None,
        dependency_scan_service: DependencyVulnerabilityScanningService | None = None,
        supply_chain_service: SupplyChainSecurityService | None = None,
        pentest_service: SecurityPenetrationTestingService | None = None,
        tenant_isolation_service: TenantSecurityIsolationService | None = None,
        abuse_protection_service: ApiAbuseProtectionService | None = None,
    ):
        self.rate_limiting_service = (
            rate_limiting_service or ApiRateLimitingService()
        )
        self.cors_service = cors_service or CorsHardeningService()
        self.secrets_service = secrets_service or SecretsManagementService()
        self.sql_review_service = sql_review_service or SqlInjectionReviewService()
        self.upload_validation_service = (
            upload_validation_service or FileUploadValidationService()
        )
        self.malware_service = malware_service or SecurityMalwareScanningService()
        self.auth_hardening_service = (
            auth_hardening_service or AuthHardeningService()
        )
        self.audit_logging_service = (
            audit_logging_service or SecurityAuditLoggingService()
        )
        self.permissions_service = (
            permissions_service or PermissionsValidationService()
        )
        self.owasp_service = owasp_service or OwaspReviewService()
        self.dependency_scan_service = (
            dependency_scan_service or DependencyVulnerabilityScanningService()
        )
        self.supply_chain_service = (
            supply_chain_service or SupplyChainSecurityService()
        )
        self.pentest_service = pentest_service or SecurityPenetrationTestingService()
        self.tenant_isolation_service = (
            tenant_isolation_service or TenantSecurityIsolationService()
        )
        self.abuse_protection_service = (
            abuse_protection_service or ApiAbuseProtectionService()
        )

    def get_dashboard(self) -> dict:
        rate_validation = self.rate_limiting_service.validate_setup()
        cors_validation = self.cors_service.validate_production_readiness()
        secrets_validation = self.secrets_service.validate_repository_hygiene()
        sql_validation = self.sql_review_service.validate_codebase_posture()
        auth_validation = self.auth_hardening_service.validate_setup()
        audit_validation = self.audit_logging_service.validate_setup()
        permissions_validation = self.permissions_service.validate_matrix_integrity()
        owasp_validation = self.owasp_service.validate_review_completeness()
        dependency_validation = self.dependency_scan_service.validate_setup()
        supply_chain_validation = self.supply_chain_service.validate_controls()
        pentest_validation = self.pentest_service.validate_catalog()
        tenant_validation = self.tenant_isolation_service.validate_setup()
        abuse_validation = self.abuse_protection_service.validate_setup()
        malware_validation = self.malware_service.validate_setup()

        checks = [
            rate_validation["valid"],
            cors_validation["valid"],
            secrets_validation["valid"],
            sql_validation["valid"],
            auth_validation["valid"],
            audit_validation["valid"],
            permissions_validation["valid"],
            owasp_validation["valid"],
            dependency_validation["valid"],
            supply_chain_validation["valid"],
            pentest_validation["valid"],
            tenant_validation["valid"],
            abuse_validation["valid"],
            malware_validation["valid"],
        ]

        return {
            "rate_limiting": self.rate_limiting_service.get_config(),
            "cors": cors_validation,
            "secrets": secrets_validation,
            "sql_injection_review": sql_validation,
            "file_upload": self.upload_validation_service.get_policy(),
            "malware_scanning": self.malware_service.get_scanner_config(),
            "auth_hardening": self.auth_hardening_service.get_controls(),
            "audit_logging": audit_validation,
            "permissions": permissions_validation,
            "owasp": self.owasp_service.get_top_10_assessment(),
            "dependency_scanning": dependency_validation,
            "supply_chain": supply_chain_validation,
            "penetration_testing": pentest_validation,
            "tenant_isolation": self.tenant_isolation_service.get_isolation_report(),
            "api_abuse_protection": self.abuse_protection_service.get_protection_config(),
            "secure": all(checks),
        }

    def get_rate_limiting_config(self) -> dict:
        return self.rate_limiting_service.get_config()

    def check_rate_limit(
        self,
        *,
        client_id: str,
        tier: str = "authenticated",
        current_count: int = 0,
    ) -> dict:
        return self.rate_limiting_service.check_rate_limit(
            client_id=client_id,
            tier=tier,
            current_count=current_count,
        )

    def validate_rate_limiting(self) -> dict:
        return self.rate_limiting_service.validate_setup()

    def get_cors_recommendations(self) -> dict:
        return self.cors_service.get_recommended_config()

    def evaluate_cors(
        self,
        *,
        allow_origins: list[str] | None = None,
    ) -> dict:
        origins = allow_origins or ["https://app.orgflow.example.com"]
        return self.cors_service.evaluate_config(
            allow_origins=origins,
            allow_methods=self.cors_service.get_recommended_config()["allow_methods"],
            allow_headers=self.cors_service.get_recommended_config()["allow_headers"],
        )

    def validate_cors(self) -> dict:
        return self.cors_service.validate_production_readiness()

    def list_managed_secrets(self) -> dict:
        return self.secrets_service.list_managed_secrets()

    def validate_secrets_hygiene(self) -> dict:
        return self.secrets_service.validate_repository_hygiene()

    def get_secrets_rotation_policy(self) -> dict:
        return self.secrets_service.get_rotation_policy()

    def get_sql_injection_checklist(self) -> dict:
        return self.sql_review_service.get_review_checklist()

    def scan_sql_input(self, value: str) -> dict:
        return self.sql_review_service.scan_input(value)

    def validate_sql_posture(self) -> dict:
        return self.sql_review_service.validate_codebase_posture()

    def get_file_upload_policy(self) -> dict:
        return self.upload_validation_service.get_policy()

    def validate_file_upload(
        self,
        *,
        filename: str,
        size_bytes: int | None = None,
    ) -> dict:
        return self.upload_validation_service.validate_upload(
            filename=filename,
            size_bytes=size_bytes,
        )

    def get_malware_scanner_config(self) -> dict:
        return self.malware_service.get_scanner_config()

    def scan_file_for_malware(self, *, file_path: str, filename: str) -> dict:
        return self.malware_service.scan_file(
            file_path=file_path,
            filename=filename,
        )

    def validate_malware_scanner(self) -> dict:
        return self.malware_service.validate_setup()

    def get_auth_hardening_controls(self) -> dict:
        return self.auth_hardening_service.get_controls()

    def evaluate_token_policy(
        self,
        *,
        access_token_ttl_minutes: int = 15,
        refresh_token_ttl_days: int = 7,
    ) -> dict:
        return self.auth_hardening_service.evaluate_token_policy(
            access_token_ttl_minutes=access_token_ttl_minutes,
            refresh_token_ttl_days=refresh_token_ttl_days,
        )

    def validate_auth_hardening(self) -> dict:
        return self.auth_hardening_service.validate_setup()

    def get_security_audit_events(self) -> dict:
        return self.audit_logging_service.get_event_catalog()

    def get_audit_coverage(self) -> dict:
        return self.audit_logging_service.get_audit_coverage()

    def validate_security_audit_logging(self) -> dict:
        return self.audit_logging_service.validate_setup()

    def get_permissions_matrix(self) -> dict:
        return self.permissions_service.get_matrix()

    def validate_role_permission(
        self,
        *,
        role: str,
        required_permission: str,
    ) -> dict:
        return self.permissions_service.validate_role_access(
            role=role,
            required_permission=required_permission,
        )

    def validate_permissions_matrix(self) -> dict:
        return self.permissions_service.validate_matrix_integrity()

    def get_owasp_assessment(self) -> dict:
        return self.owasp_service.get_top_10_assessment()

    def evaluate_owasp_control(self, control_id: str) -> dict:
        return self.owasp_service.evaluate_control(control_id)

    def validate_owasp_review(self) -> dict:
        return self.owasp_service.validate_review_completeness()

    def list_dependency_lock_files(self) -> dict:
        return self.dependency_scan_service.list_lock_files()

    def simulate_dependency_scan(
        self,
        *,
        critical: int = 0,
        high: int = 0,
    ) -> dict:
        return self.dependency_scan_service.simulate_scan_result(
            critical=critical,
            high=high,
        )

    def validate_dependency_scanning(self) -> dict:
        return self.dependency_scan_service.validate_setup()

    def get_supply_chain_controls(self) -> dict:
        return self.supply_chain_service.get_controls()

    def validate_supply_chain(self) -> dict:
        return self.supply_chain_service.validate_controls()

    def get_sbom_status(self) -> dict:
        return self.supply_chain_service.get_sbom_status()

    def list_pentest_scenarios(self) -> dict:
        return self.pentest_service.list_scenarios()

    def run_pentest_scenario(self, scenario_id: str) -> dict:
        return self.pentest_service.run_scenario(scenario_id)

    def run_pentest_smoke_suite(self) -> dict:
        return self.pentest_service.run_smoke_suite()

    def get_tenant_isolation_report(self) -> dict:
        return self.tenant_isolation_service.get_isolation_report()

    def validate_tenant_access(
        self,
        *,
        table_name: str,
        record: dict,
        requesting_org_id: str,
    ) -> dict:
        return self.tenant_isolation_service.validate_cross_tenant_access(
            table_name=table_name,
            record=record,
            requesting_org_id=requesting_org_id,
        )

    def validate_tenant_isolation(self) -> dict:
        return self.tenant_isolation_service.validate_setup()

    def get_api_abuse_config(self) -> dict:
        return self.abuse_protection_service.get_protection_config()

    def evaluate_api_abuse(
        self,
        *,
        client_id: str,
        requests_per_minute: int = 0,
        failed_auth_count: int = 0,
    ) -> dict:
        return self.abuse_protection_service.evaluate_client(
            client_id=client_id,
            requests_per_minute=requests_per_minute,
            failed_auth_count=failed_auth_count,
        )

    def validate_api_abuse_protection(self) -> dict:
        return self.abuse_protection_service.validate_setup()
