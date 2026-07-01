from pathlib import Path

from fastapi.testclient import TestClient

import app.main as main_module
from app.auth.jwt_service import JWTService
from app.main import app
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
from app.services.security_dashboard_service import SecurityDashboardService
from app.services.security_malware_scanning_service import SecurityMalwareScanningService
from app.services.security_penetration_testing_service import (
    SecurityPenetrationTestingService,
)
from app.services.sql_injection_review_service import SqlInjectionReviewService
from app.services.supply_chain_security_service import SupplyChainSecurityService
from app.services.tenant_security_isolation_service import TenantSecurityIsolationService
import app.dependencies as deps


def build_dashboard():
    return SecurityDashboardService()


def test_api_rate_limiting():
    service = ApiRateLimitingService()
    config = service.get_config()
    assert config["enabled"] is True
    assert "authenticated" in config["tiers"]

    allowed = service.check_rate_limit(
        client_id="client-1",
        tier="authenticated",
        current_count=10,
    )
    assert allowed["allowed"] is True

    blocked = service.check_rate_limit(
        client_id="client-1",
        tier="authenticated",
        current_count=400,
    )
    assert blocked["allowed"] is False
    assert service.validate_setup()["valid"] is True


def test_cors_hardening():
    service = CorsHardeningService()
    good = service.evaluate_config(
        allow_origins=["https://app.orgflow.example.com"],
        allow_methods=["GET", "POST"],
        allow_headers=["Authorization", "Content-Type"],
    )
    assert good["valid"] is True

    bad = service.evaluate_config(
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=True,
    )
    assert bad["valid"] is False
    assert "WILDCARD_ORIGIN" in bad["issues"]
    assert service.validate_production_readiness()["valid"] is True


def test_secrets_management():
    service = SecretsManagementService()
    secrets = service.list_managed_secrets()
    assert secrets["total"] >= 5

    hygiene = service.validate_repository_hygiene()
    assert hygiene["valid"] is True
    assert hygiene["gitignore_covers_env"] is True
    assert service.get_rotation_policy()["rotation_interval_days"] == 90


def test_sql_injection_review():
    service = SqlInjectionReviewService()
    assert service.get_review_checklist()["total"] >= 4

    safe = service.scan_input("weekly report summary")
    assert safe["safe"] is True

    unsafe = service.scan_input("' OR '1'='1")
    assert unsafe["safe"] is False
    assert service.validate_codebase_posture()["valid"] is True


def test_file_upload_validation():
    service = FileUploadValidationService()
    policy = service.get_policy()
    assert "pdf" in policy["allowed_extensions"]

    valid = service.validate_upload(filename="report.pdf", size_bytes=1024)
    assert valid["valid"] is True

    invalid = service.validate_upload(filename="payload.exe", size_bytes=1024)
    assert invalid["valid"] is False
    assert "BLOCKED_EXTENSION" in invalid["issues"]


def test_security_malware_scanning(tmp_path: Path):
    service = SecurityMalwareScanningService()
    assert service.validate_setup()["valid"] is True

    clean = tmp_path / "clean.txt"
    clean.write_text("safe content", encoding="utf-8")
    clean_result = service.scan_file(file_path=str(clean), filename="clean.txt")
    assert clean_result["is_clean"] is True

    infected = tmp_path / "eicar.txt"
    infected.write_bytes(b"EICAR-STANDARD-ANTIVIRUS-TEST-FILE")
    infected_result = service.scan_file(
        file_path=str(infected),
        filename="eicar.txt",
    )
    assert infected_result["is_clean"] is False
    assert infected_result["error_code"] == "MALWARE_DETECTED"


def test_auth_hardening():
    service = AuthHardeningService()
    controls = service.get_controls()
    assert controls["all_enabled"] is True

    policy = service.evaluate_token_policy(
        access_token_ttl_minutes=15,
        refresh_token_ttl_days=7,
    )
    assert policy["valid"] is True
    assert service.validate_setup()["valid"] is True


def test_security_audit_logging():
    service = SecurityAuditLoggingService()
    events = service.get_event_catalog()
    assert events["total"] >= 8
    assert service.validate_setup()["valid"] is True


def test_permissions_validation():
    service = PermissionsValidationService()
    matrix = service.get_matrix()
    assert matrix["role_count"] >= 4

    admin = service.validate_role_access(
        role="ADMIN",
        required_permission="projects:write",
    )
    assert admin["granted"] is True

    viewer = service.validate_role_access(
        role="VIEWER",
        required_permission="users:write",
    )
    assert viewer["granted"] is False
    assert service.validate_matrix_integrity()["valid"] is True


def test_owasp_review():
    service = OwaspReviewService()
    assessment = service.get_top_10_assessment()
    assert assessment["total"] == 10

    control = service.evaluate_control("A01")
    assert control["found"] is True
    assert service.validate_review_completeness()["valid"] is True


def test_dependency_vulnerability_scanning():
    service = DependencyVulnerabilityScanningService()
    lock_files = service.list_lock_files()
    assert lock_files["all_present"] is True

    clean_scan = service.simulate_scan_result()
    assert clean_scan["passed"] is True

    dirty_scan = service.simulate_scan_result(critical=1)
    assert dirty_scan["passed"] is False
    assert service.validate_setup()["valid"] is True


def test_supply_chain_security():
    service = SupplyChainSecurityService()
    assert service.validate_controls()["valid"] is True
    assert service.get_sbom_status()["format"] == "CycloneDX"


def test_security_penetration_testing():
    service = SecurityPenetrationTestingService()
    scenarios = service.list_scenarios()
    assert scenarios["total"] >= 5

    result = service.run_scenario("AUTH_BYPASS")
    assert result["passed"] is True

    suite = service.run_smoke_suite()
    assert suite["passed"] is True


def test_tenant_security_isolation():
    service = TenantSecurityIsolationService()
    report = service.get_isolation_report()
    assert report["table_count"] > 0

    valid = service.validate_cross_tenant_access(
        table_name="projects",
        record={"organization_id": "org-1"},
        requesting_org_id="org-1",
    )
    assert valid["valid"] is True

    invalid = service.validate_cross_tenant_access(
        table_name="projects",
        record={"organization_id": "org-2"},
        requesting_org_id="org-1",
    )
    assert invalid["access_denied"] is True
    assert service.validate_setup()["valid"] is True


def test_api_abuse_protection():
    service = ApiAbuseProtectionService()
    benign = service.evaluate_client(
        client_id="client-1",
        requests_per_minute=20,
        failed_auth_count=0,
    )
    assert benign["action"] == "ALLOW"

    abusive = service.evaluate_client(
        client_id="client-2",
        requests_per_minute=800,
        failed_auth_count=20,
        suspicious_user_agent=True,
    )
    assert abusive["blocked"] is True
    assert service.validate_setup()["valid"] is True


def test_security_dashboard_aggregates_all_domains():
    dashboard = build_dashboard()
    result = dashboard.get_dashboard()

    assert result["secure"] is True
    assert result["rate_limiting"]["enabled"] is True
    assert result["permissions"]["valid"] is True
    assert result["tenant_isolation"]["table_count"] > 0


def _auth_headers():
    token = JWTService().issue_access_token(
        user_id="user-1",
        org_id="org-1",
        role="ADMIN",
        token_id="security-backlog-tests",
    )
    return {"Authorization": f"Bearer {token}", "X-Organization-ID": "org-1"}


def test_security_api_endpoints(monkeypatch):
    dashboard = build_dashboard()
    monkeypatch.setattr(
        deps,
        "security_dashboard_service",
        dashboard,
    )

    client = TestClient(app)
    headers = _auth_headers()

    get_endpoints = [
        "/security/dashboard",
        "/security/rate-limiting/config",
        "/security/rate-limiting/check",
        "/security/rate-limiting/validate",
        "/security/cors/recommendations",
        "/security/cors/evaluate",
        "/security/cors/validate",
        "/security/secrets",
        "/security/secrets/validate",
        "/security/secrets/rotation-policy",
        "/security/sql-injection/checklist",
        "/security/sql-injection/scan",
        "/security/sql-injection/validate",
        "/security/uploads/policy",
        "/security/uploads/validate",
        "/security/malware/config",
        "/security/malware/validate",
        "/security/auth/controls",
        "/security/auth/token-policy",
        "/security/auth/validate",
        "/security/audit/events",
        "/security/audit/coverage",
        "/security/audit/validate",
        "/security/permissions/matrix",
        "/security/permissions/validate",
        "/security/permissions/check",
        "/security/owasp/assessment",
        "/security/owasp/controls/A01",
        "/security/owasp/validate",
        "/security/dependencies/lock-files",
        "/security/dependencies/scan",
        "/security/dependencies/validate",
        "/security/supply-chain/controls",
        "/security/supply-chain/validate",
        "/security/supply-chain/sbom",
        "/security/pentest/scenarios",
        "/security/tenant-isolation/report",
        "/security/tenant-isolation/validate",
        "/security/tenant-isolation/check",
        "/security/abuse/config",
        "/security/abuse/evaluate",
        "/security/abuse/validate",
    ]

    for path in get_endpoints:
        response = client.get(path, headers=headers)
        assert response.status_code == 200, path

    post_endpoints = [
        "/security/pentest/run",
        "/security/pentest/smoke",
    ]
    for path in post_endpoints:
        response = client.post(path, headers=headers)
        assert response.status_code == 200, path

    dashboard_response = client.get(
        "/security/dashboard",
        headers=headers,
    ).json()
    assert dashboard_response["secure"] is True
