"""Database hardening / migration admin routes.

Extracted from app/main.py during the 2026-07 architecture-modularization
refactor. Shared service singletons live in app/dependencies.py; shared
request models live in app/schemas/api_requests.py.
"""
from __future__ import annotations


from fastapi import APIRouter
import app.dependencies as deps


router = APIRouter()


@router.get("/database/dashboard")
def get_database_hardening_dashboard():
    return deps.database_hardening_dashboard_service.get_dashboard()


@router.get("/database/migrations")
def list_database_migrations():
    return deps.database_hardening_dashboard_service.get_migrations()


@router.get("/database/migrations/status")
def get_database_migration_status():
    return deps.database_hardening_dashboard_service.get_migration_status()


@router.post("/database/migrations/apply")
def apply_database_migrations():
    return deps.database_hardening_dashboard_service.apply_migrations()


@router.get("/database/rls/policies")
def list_database_rls_policies():
    return deps.database_hardening_dashboard_service.get_rls_policies()


@router.get("/database/rls/validate")
def validate_database_rls():
    return deps.database_hardening_dashboard_service.validate_rls()


@router.get("/database/foreign-keys")
def list_database_foreign_keys():
    return deps.database_hardening_dashboard_service.get_foreign_keys()


@router.get("/database/foreign-keys/validate")
def validate_database_foreign_keys():
    return deps.database_hardening_dashboard_service.validate_foreign_keys()


@router.get("/database/indexes")
def list_database_indexes():
    return deps.database_hardening_dashboard_service.get_indexes()


@router.get("/database/indexes/recommendations")
def get_database_index_recommendations():
    return deps.database_hardening_dashboard_service.get_index_recommendations()


@router.get("/database/soft-delete/tables")
def list_soft_delete_tables():
    return deps.database_hardening_dashboard_service.get_soft_delete_tables()


@router.get("/database/audit/tables")
def list_audit_tables():
    return deps.database_hardening_dashboard_service.get_audit_tables()


@router.get("/database/audit/log")
def get_database_audit_log(
    table_name: str | None = None,
    organization_id: str | None = None,
    limit: int = 100,
):
    return deps.database_hardening_dashboard_service.get_audit_log(
        table_name=table_name,
        organization_id=organization_id,
        limit=limit,
    )


@router.get("/database/backup/strategy")
def get_database_backup_strategy():
    return deps.database_hardening_dashboard_service.get_backup_strategy()


@router.get("/database/backup/status")
def get_database_backup_status():
    return deps.database_hardening_dashboard_service.get_backup_status()


@router.post("/database/backup/restore-test")
def run_database_backup_restore_test(backup_id: str = "latest"):
    return deps.database_hardening_dashboard_service.run_backup_restore_test(
        backup_id=backup_id,
    )


@router.get("/database/monitoring/health")
def get_database_monitoring_health():
    return deps.database_hardening_dashboard_service.get_monitoring_health()


@router.get("/database/monitoring/metrics")
def get_database_monitoring_metrics():
    return deps.database_hardening_dashboard_service.get_monitoring_metrics()


@router.get("/database/monitoring/alerts")
def get_database_monitoring_alerts():
    return deps.database_hardening_dashboard_service.get_monitoring_alerts()


@router.get("/database/seeds")
def list_database_seed_scripts():
    return deps.database_hardening_dashboard_service.get_seed_scripts()


@router.post("/database/seeds/demo")
def generate_database_demo_seed():
    return deps.database_hardening_dashboard_service.generate_demo_seed()


@router.get("/database/fixtures/types")
def list_database_fixture_types():
    return deps.database_hardening_dashboard_service.get_fixture_types()


@router.post("/database/fixtures/test-suite")
def build_database_test_fixtures(organization_id: str = "org-fixture-1"):
    return deps.database_hardening_dashboard_service.build_test_fixtures(
        organization_id=organization_id,
    )


@router.get("/database/query-optimization")
def get_database_query_optimization_report():
    return deps.database_hardening_dashboard_service.get_query_optimization_report()


@router.get("/database/connection-pool/config")
def get_database_connection_pool_config():
    return deps.database_hardening_dashboard_service.get_connection_pool_config()


@router.get("/database/connection-pool/stats")
def get_database_connection_pool_stats():
    return deps.database_hardening_dashboard_service.get_connection_pool_stats()


@router.get("/database/tenant-isolation")
def get_database_tenant_isolation_report():
    return deps.database_hardening_dashboard_service.get_tenant_isolation_report()


@router.get("/database/retention/policies")
def list_database_retention_policies():
    return deps.database_hardening_dashboard_service.get_retention_policies()


