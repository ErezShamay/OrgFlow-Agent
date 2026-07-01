from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

import app.main as main_module
from app.auth.jwt_service import JWTService
from app.main import app
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.migration_repository import MigrationRepository
from app.services.audit_table_service import AuditTableService
from app.services.connection_pool_service import ConnectionPoolService
from app.services.data_retention_service import DataRetentionService
from app.services.database_backup_service import DatabaseBackupService
from app.services.database_fixture_service import DatabaseFixtureService
from app.services.database_hardening_dashboard_service import (
    DatabaseHardeningDashboardService,
)
from app.services.database_monitoring_service import DatabaseMonitoringService
from app.services.database_seed_service import DatabaseSeedService
from app.services.foreign_key_integrity_service import ForeignKeyIntegrityService
from app.services.index_optimization_service import IndexOptimizationService
from app.services.migration_management_service import MigrationManagementService
from app.services.query_optimization_service import QueryOptimizationService
from app.services.rls_policy_service import RlsPolicyService
from app.services.soft_delete_service import SoftDeleteService
from app.services.tenant_data_isolation_service import TenantDataIsolationService
import app.dependencies as deps


def build_dashboard():
    migration_repo = MigrationRepository()
    audit_repo = AuditLogRepository()
    return DatabaseHardeningDashboardService(
        migration_service=MigrationManagementService(migration_repo),
        audit_service=AuditTableService(audit_repo),
    )


def test_migration_management_tracks_pending_and_applied():
    service = MigrationManagementService(MigrationRepository())

    status = service.get_status()
    assert status["pending_count"] >= 1
    assert status["up_to_date"] is False

    applied = service.apply_pending()
    assert applied["count"] >= 1
    assert service.get_status()["up_to_date"] is True


def test_rls_policy_service_lists_and_validates_coverage():
    service = RlsPolicyService()
    policies = service.list_policies()
    validation = service.validate_coverage()

    assert policies["policy_count"] >= 1
    assert validation["valid"] is True
    assert validation["covered_tables"] >= 1


def test_foreign_key_integrity_validates_schema_and_records():
    service = ForeignKeyIntegrityService()
    schema = service.validate_schema()
    assert schema["valid"] is True

    result = service.validate_references(
        table_name="projects",
        records=[{"id": "p1", "organization_id": "org-1"}],
        reference_data={"organizations": {"org-1"}},
    )
    assert result["valid"] is True

    orphan = service.validate_references(
        table_name="projects",
        records=[{"id": "p2", "organization_id": "missing"}],
        reference_data={"organizations": {"org-1"}},
    )
    assert orphan["valid"] is False
    assert orphan["violations"][0]["issue"] == "ORPHAN_REFERENCE"


def test_index_optimization_lists_and_recommends():
    service = IndexOptimizationService()
    indexes = service.list_indexes()
    recommendations = service.get_recommendations()

    assert indexes["index_count"] >= 1
    assert "recommendations" in recommendations


def test_soft_delete_marks_and_filters_records():
    service = SoftDeleteService()
    record = {"id": "p1", "organization_id": "org-1"}

    deleted = service.apply_soft_delete(
        table_name="projects",
        record=record,
        actor_id="user-1",
    )
    assert deleted["already_deleted"] is False
    assert deleted["record"]["deleted_at"]

    filtered = service.filter_active(
        [record, deleted["record"]],
        table_name="projects",
    )
    assert filtered["active_count"] == 1
    assert filtered["deleted_count"] == 1


def test_audit_table_records_changes():
    audit_repo = AuditLogRepository()
    service = AuditTableService(audit_repo)

    result = service.record_change(
        table_name="projects",
        record_id="p1",
        action="UPDATE",
        organization_id="org-1",
        actor_id="user-1",
        before={"status": "ACTIVE"},
        after={"status": "ARCHIVED"},
    )
    assert result["recorded"] is True

    log = service.get_audit_log(organization_id="org-1")
    assert log["count"] == 1
    assert log["entries"][0]["action"] == "UPDATE"


def test_database_backup_strategy_and_restore_test():
    service = DatabaseBackupService()
    strategy = service.get_strategy()
    restore = service.run_restore_test()

    assert strategy["point_in_time_recovery"] is True
    assert restore["passed"] is True
    assert len(restore["steps"]) >= 4


def test_database_monitoring_reports_health_and_metrics():
    service = DatabaseMonitoringService()
    health = service.get_health()
    metrics = service.get_metrics()

    assert "status" in health
    assert metrics["connection_pool"]["max_connections"] == 20


def test_database_seed_and_fixture_generators():
    seed_service = DatabaseSeedService()
    fixture_service = DatabaseFixtureService()

    demo = seed_service.generate_full_demo()
    assert demo["entity_count"] >= 3

    suite = fixture_service.build_test_suite()
    assert suite["fixture_count"] == 2
    assert suite["project"]["organization_id"] == suite["organization_id"]


def test_query_optimization_detects_slow_queries_and_batch_loads():
    service = QueryOptimizationService()

    slow = service.analyze_query(
        table="operational_actions",
        filters=[],
        estimated_rows=5000,
    )
    assert slow["slow_risk"] is True

    parents = [{"id": "p1"}, {"id": "p2"}]
    children = [
        {"id": "a1", "project_id": "p1"},
        {"id": "a2", "project_id": "p1"},
        {"id": "a3", "project_id": "p2"},
    ]
    batched = service.batch_load(
        parent_records=parents,
        child_records=children,
        parent_key="id",
        foreign_key="project_id",
    )
    assert batched["n_plus_one_resolved"] is True
    assert batched["query_count_after"] == 2


def test_connection_pool_configuration_and_capacity():
    service = ConnectionPoolService()
    config = service.get_configuration()
    stats = service.get_stats()
    capacity = service.check_capacity(requested=5)

    assert config["pool_size"] == 20
    assert stats["healthy"] is True
    assert capacity["can_acquire"] is True


def test_tenant_data_isolation_validates_and_filters():
    service = TenantDataIsolationService()
    record = {"id": "p1", "organization_id": "org-1"}
    other = {"id": "p2", "organization_id": "org-2"}

    valid = service.validate_record(
        table_name="projects",
        record=record,
        organization_id="org-1",
    )
    assert valid["valid"] is True

    filtered = service.filter_by_tenant(
        table_name="projects",
        records=[record, other],
        organization_id="org-1",
    )
    assert filtered["output_count"] == 1
    assert filtered["leaked_count"] == 1


def test_data_retention_evaluates_and_simulates_purge():
    service = DataRetentionService()
    old_date = (datetime.now(UTC) - timedelta(days=400)).isoformat()
    recent_date = datetime.now(UTC).isoformat()

    old = service.evaluate_record(
        table_name="audit_log",
        created_at=old_date,
    )
    recent = service.evaluate_record(
        table_name="audit_log",
        created_at=recent_date,
    )
    assert old["eligible_for_purge"] is True
    assert recent["eligible_for_purge"] is False

    ai_old = service.evaluate_record(
        table_name="ai_execution_logs",
        created_at=old_date,
    )
    assert ai_old["eligible_for_purge"] is True

    purge = service.simulate_purge(
        table_name="ai_execution_logs",
        records=[
            {"id": "1", "created_at": old_date},
            {"id": "2", "created_at": recent_date},
        ],
    )
    assert purge["purge_count"] == 1
    assert purge["retain_count"] == 1


def test_database_hardening_dashboard_aggregates_all_domains():
    dashboard = build_dashboard()
    dashboard.apply_migrations()
    result = dashboard.get_dashboard()

    assert "migrations" in result
    assert result["rls"]["validation"]["valid"] is True
    assert result["foreign_keys"]["valid"] is True
    assert result["healthy"] is True


def _auth_headers():
    token = JWTService().issue_access_token(
        user_id="user-1",
        org_id="org-1",
        role="ADMIN",
        token_id="database-hardening-tests",
    )
    return {"Authorization": f"Bearer {token}", "X-Organization-ID": "org-1"}


def test_database_hardening_api_endpoints(monkeypatch):
    dashboard = build_dashboard()
    dashboard.apply_migrations()
    monkeypatch.setattr(
        deps,
        "database_hardening_dashboard_service",
        dashboard,
    )

    client = TestClient(app)
    headers = _auth_headers()

    get_endpoints = [
        "/database/dashboard",
        "/database/migrations",
        "/database/migrations/status",
        "/database/rls/policies",
        "/database/rls/validate",
        "/database/foreign-keys",
        "/database/foreign-keys/validate",
        "/database/indexes",
        "/database/indexes/recommendations",
        "/database/soft-delete/tables",
        "/database/audit/tables",
        "/database/audit/log",
        "/database/backup/strategy",
        "/database/backup/status",
        "/database/monitoring/health",
        "/database/monitoring/metrics",
        "/database/monitoring/alerts",
        "/database/seeds",
        "/database/fixtures/types",
        "/database/query-optimization",
        "/database/connection-pool/config",
        "/database/connection-pool/stats",
        "/database/tenant-isolation",
        "/database/retention/policies",
    ]

    for path in get_endpoints:
        response = client.get(path, headers=headers)
        assert response.status_code == 200, path

    post_endpoints = [
        "/database/migrations/apply",
        "/database/backup/restore-test",
        "/database/seeds/demo",
        "/database/fixtures/test-suite",
    ]

    for path in post_endpoints:
        response = client.post(path, headers=headers)
        assert response.status_code == 200, path

    dashboard_response = client.get(
        "/database/dashboard",
        headers=headers,
    ).json()
    assert dashboard_response["healthy"] is True
