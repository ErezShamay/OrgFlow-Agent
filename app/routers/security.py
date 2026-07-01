"""Security routes.

Extracted from app/main.py during the 2026-07 architecture-modularization
refactor. Shared service singletons live in app/dependencies.py; shared
request models live in app/schemas/api_requests.py.
"""
from __future__ import annotations

from app.config import config_manager

from fastapi import APIRouter
import app.dependencies as deps


router = APIRouter()


@router.get("/secrets/rotation-status")
def get_secret_rotation_status():
    return config_manager.get_secret_rotation_status()


@router.get("/security/dashboard")
def get_security_dashboard():
    return deps.security_dashboard_service.get_dashboard()


@router.get("/security/rate-limiting/config")
def get_security_rate_limiting_config():
    return deps.security_dashboard_service.get_rate_limiting_config()


@router.get("/security/rate-limiting/check")
def check_security_rate_limit(
    client_id: str = "default",
    tier: str = "authenticated",
    current_count: int = 0,
):
    return deps.security_dashboard_service.check_rate_limit(
        client_id=client_id,
        tier=tier,
        current_count=current_count,
    )


@router.get("/security/rate-limiting/validate")
def validate_security_rate_limiting():
    return deps.security_dashboard_service.validate_rate_limiting()


@router.get("/security/cors/recommendations")
def get_security_cors_recommendations():
    return deps.security_dashboard_service.get_cors_recommendations()


@router.get("/security/cors/evaluate")
def evaluate_security_cors(allow_origins: str | None = None):
    origins = allow_origins.split(",") if allow_origins else None
    return deps.security_dashboard_service.evaluate_cors(allow_origins=origins)


@router.get("/security/cors/validate")
def validate_security_cors():
    return deps.security_dashboard_service.validate_cors()


@router.get("/security/secrets")
def list_security_managed_secrets():
    return deps.security_dashboard_service.list_managed_secrets()


@router.get("/security/secrets/validate")
def validate_security_secrets_hygiene():
    return deps.security_dashboard_service.validate_secrets_hygiene()


@router.get("/security/secrets/rotation-policy")
def get_security_secrets_rotation_policy():
    return deps.security_dashboard_service.get_secrets_rotation_policy()


@router.get("/security/sql-injection/checklist")
def get_security_sql_injection_checklist():
    return deps.security_dashboard_service.get_sql_injection_checklist()


@router.get("/security/sql-injection/scan")
def scan_security_sql_input(value: str = ""):
    return deps.security_dashboard_service.scan_sql_input(value)


@router.get("/security/sql-injection/validate")
def validate_security_sql_posture():
    return deps.security_dashboard_service.validate_sql_posture()


@router.get("/security/uploads/policy")
def get_security_file_upload_policy():
    return deps.security_dashboard_service.get_file_upload_policy()


@router.get("/security/uploads/validate")
def validate_security_file_upload(
    filename: str = "report.pdf",
    size_bytes: int | None = None,
):
    return deps.security_dashboard_service.validate_file_upload(
        filename=filename,
        size_bytes=size_bytes,
    )


@router.get("/security/malware/config")
def get_security_malware_scanner_config():
    return deps.security_dashboard_service.get_malware_scanner_config()


@router.get("/security/malware/validate")
def validate_security_malware_scanner():
    return deps.security_dashboard_service.validate_malware_scanner()


@router.get("/security/auth/controls")
def get_security_auth_hardening_controls():
    return deps.security_dashboard_service.get_auth_hardening_controls()


@router.get("/security/auth/token-policy")
def evaluate_security_token_policy(
    access_token_ttl_minutes: int = 15,
    refresh_token_ttl_days: int = 7,
):
    return deps.security_dashboard_service.evaluate_token_policy(
        access_token_ttl_minutes=access_token_ttl_minutes,
        refresh_token_ttl_days=refresh_token_ttl_days,
    )


@router.get("/security/auth/validate")
def validate_security_auth_hardening():
    return deps.security_dashboard_service.validate_auth_hardening()


@router.get("/security/audit/events")
def get_security_audit_events():
    return deps.security_dashboard_service.get_security_audit_events()


@router.get("/security/audit/coverage")
def get_security_audit_coverage():
    return deps.security_dashboard_service.get_audit_coverage()


@router.get("/security/audit/validate")
def validate_security_audit_logging():
    return deps.security_dashboard_service.validate_security_audit_logging()


@router.get("/security/permissions/matrix")
def get_security_permissions_matrix():
    return deps.security_dashboard_service.get_permissions_matrix()


@router.get("/security/permissions/validate")
def validate_security_permissions_matrix():
    return deps.security_dashboard_service.validate_permissions_matrix()


@router.get("/security/permissions/check")
def check_security_role_permission(
    role: str = "VIEWER",
    required_permission: str = "projects:read",
):
    return deps.security_dashboard_service.validate_role_permission(
        role=role,
        required_permission=required_permission,
    )


@router.get("/security/owasp/assessment")
def get_security_owasp_assessment():
    return deps.security_dashboard_service.get_owasp_assessment()


@router.get("/security/owasp/controls/{control_id}")
def evaluate_security_owasp_control(control_id: str):
    return deps.security_dashboard_service.evaluate_owasp_control(control_id)


@router.get("/security/owasp/validate")
def validate_security_owasp_review():
    return deps.security_dashboard_service.validate_owasp_review()


@router.get("/security/dependencies/lock-files")
def list_security_dependency_lock_files():
    return deps.security_dashboard_service.list_dependency_lock_files()


@router.get("/security/dependencies/scan")
def simulate_security_dependency_scan(
    critical: int = 0,
    high: int = 0,
):
    return deps.security_dashboard_service.simulate_dependency_scan(
        critical=critical,
        high=high,
    )


@router.get("/security/dependencies/validate")
def validate_security_dependency_scanning():
    return deps.security_dashboard_service.validate_dependency_scanning()


@router.get("/security/supply-chain/controls")
def get_security_supply_chain_controls():
    return deps.security_dashboard_service.get_supply_chain_controls()


@router.get("/security/supply-chain/validate")
def validate_security_supply_chain():
    return deps.security_dashboard_service.validate_supply_chain()


@router.get("/security/supply-chain/sbom")
def get_security_sbom_status():
    return deps.security_dashboard_service.get_sbom_status()


@router.get("/security/pentest/scenarios")
def list_security_pentest_scenarios():
    return deps.security_dashboard_service.list_pentest_scenarios()


@router.post("/security/pentest/run")
def run_security_pentest_scenario(scenario_id: str = "AUTH_BYPASS"):
    return deps.security_dashboard_service.run_pentest_scenario(scenario_id)


@router.post("/security/pentest/smoke")
def run_security_pentest_smoke_suite():
    return deps.security_dashboard_service.run_pentest_smoke_suite()


@router.get("/security/tenant-isolation/report")
def get_security_tenant_isolation_report():
    return deps.security_dashboard_service.get_tenant_isolation_report()


@router.get("/security/tenant-isolation/validate")
def validate_security_tenant_isolation():
    return deps.security_dashboard_service.validate_tenant_isolation()


@router.get("/security/tenant-isolation/check")
def check_security_tenant_access(
    table_name: str = "projects",
    requesting_org_id: str = "org-1",
):
    return deps.security_dashboard_service.validate_tenant_access(
        table_name=table_name,
        record={"organization_id": requesting_org_id},
        requesting_org_id=requesting_org_id,
    )


@router.get("/security/abuse/config")
def get_security_api_abuse_config():
    return deps.security_dashboard_service.get_api_abuse_config()


@router.get("/security/abuse/evaluate")
def evaluate_security_api_abuse(
    client_id: str = "client-1",
    requests_per_minute: int = 0,
    failed_auth_count: int = 0,
):
    return deps.security_dashboard_service.evaluate_api_abuse(
        client_id=client_id,
        requests_per_minute=requests_per_minute,
        failed_auth_count=failed_auth_count,
    )


@router.get("/security/abuse/validate")
def validate_security_api_abuse_protection():
    return deps.security_dashboard_service.validate_api_abuse_protection()


