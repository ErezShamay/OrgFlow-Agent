from app.services.audit_table_service import AuditTableService
from app.services.connection_pool_service import ConnectionPoolService
from app.services.data_retention_service import DataRetentionService
from app.services.database_backup_service import DatabaseBackupService
from app.services.database_fixture_service import DatabaseFixtureService
from app.services.database_monitoring_service import DatabaseMonitoringService
from app.services.database_seed_service import DatabaseSeedService
from app.services.foreign_key_integrity_service import ForeignKeyIntegrityService
from app.services.index_optimization_service import IndexOptimizationService
from app.services.migration_management_service import MigrationManagementService
from app.services.query_optimization_service import QueryOptimizationService
from app.services.rls_policy_service import RlsPolicyService
from app.services.soft_delete_service import SoftDeleteService
from app.services.tenant_data_isolation_service import TenantDataIsolationService


class DatabaseHardeningDashboardService:
    def __init__(
        self,
        migration_service: MigrationManagementService | None = None,
        rls_service: RlsPolicyService | None = None,
        fk_service: ForeignKeyIntegrityService | None = None,
        index_service: IndexOptimizationService | None = None,
        soft_delete_service: SoftDeleteService | None = None,
        audit_service: AuditTableService | None = None,
        backup_service: DatabaseBackupService | None = None,
        monitoring_service: DatabaseMonitoringService | None = None,
        seed_service: DatabaseSeedService | None = None,
        fixture_service: DatabaseFixtureService | None = None,
        query_service: QueryOptimizationService | None = None,
        pool_service: ConnectionPoolService | None = None,
        tenant_service: TenantDataIsolationService | None = None,
        retention_service: DataRetentionService | None = None,
    ):
        self.migration_service = (
            migration_service or MigrationManagementService()
        )
        self.rls_service = rls_service or RlsPolicyService()
        self.fk_service = fk_service or ForeignKeyIntegrityService()
        self.index_service = index_service or IndexOptimizationService()
        self.soft_delete_service = soft_delete_service or SoftDeleteService()
        self.audit_service = audit_service or AuditTableService()
        self.backup_service = backup_service or DatabaseBackupService()
        self.monitoring_service = (
            monitoring_service or DatabaseMonitoringService()
        )
        self.seed_service = seed_service or DatabaseSeedService()
        self.fixture_service = fixture_service or DatabaseFixtureService()
        self.query_service = query_service or QueryOptimizationService()
        self.pool_service = pool_service or ConnectionPoolService()
        self.tenant_service = tenant_service or TenantDataIsolationService()
        self.retention_service = retention_service or DataRetentionService()

    def get_dashboard(self) -> dict:
        migration_status = self.migration_service.get_status()
        rls_validation = self.rls_service.validate_coverage()
        fk_validation = self.fk_service.validate_schema()
        index_recommendations = self.index_service.get_recommendations()
        backup_status = self.backup_service.get_backup_status()
        monitoring = self.monitoring_service.get_health()
        retention = self.retention_service.list_policies()
        tenant_report = self.tenant_service.get_isolation_report()

        return {
            "migrations": migration_status,
            "rls": {
                "validation": rls_validation,
                "policy_count": self.rls_service.list_policies()["policy_count"],
            },
            "foreign_keys": fk_validation,
            "indexes": index_recommendations,
            "soft_delete": self.soft_delete_service.get_supported_tables(),
            "audit": self.audit_service.get_audited_tables(),
            "backup": backup_status,
            "monitoring": monitoring,
            "connection_pool": self.pool_service.get_stats(),
            "tenant_isolation": tenant_report,
            "retention": retention,
            "healthy": (
                migration_status["up_to_date"]
                and rls_validation["valid"]
                and fk_validation["valid"]
                and backup_status["healthy"]
                and monitoring["status"] == "HEALTHY"
            ),
        }

    def get_migrations(self) -> dict:
        return self.migration_service.list_migrations()

    def get_migration_status(self) -> dict:
        return self.migration_service.get_status()

    def apply_migrations(self) -> dict:
        return self.migration_service.apply_pending()

    def get_rls_policies(self) -> dict:
        return self.rls_service.list_policies()

    def validate_rls(self) -> dict:
        return self.rls_service.validate_coverage()

    def get_foreign_keys(self) -> dict:
        return self.fk_service.get_constraints()

    def validate_foreign_keys(self) -> dict:
        return self.fk_service.validate_schema()

    def get_indexes(self) -> dict:
        return self.index_service.list_indexes()

    def get_index_recommendations(self) -> dict:
        return self.index_service.get_recommendations()

    def get_soft_delete_tables(self) -> dict:
        return self.soft_delete_service.get_supported_tables()

    def get_audit_tables(self) -> dict:
        return self.audit_service.get_audited_tables()

    def get_audit_log(
        self,
        *,
        table_name: str | None = None,
        organization_id: str | None = None,
        limit: int = 100,
    ) -> dict:
        return self.audit_service.get_audit_log(
            table_name=table_name,
            organization_id=organization_id,
            limit=limit,
        )

    def get_backup_strategy(self) -> dict:
        return self.backup_service.get_strategy()

    def get_backup_status(self) -> dict:
        return self.backup_service.get_backup_status()

    def run_backup_restore_test(self, backup_id: str = "latest") -> dict:
        return self.backup_service.run_restore_test(backup_id=backup_id)

    def get_monitoring_health(self) -> dict:
        return self.monitoring_service.get_health()

    def get_monitoring_metrics(self) -> dict:
        return self.monitoring_service.get_metrics()

    def get_monitoring_alerts(self) -> dict:
        return self.monitoring_service.get_alerts()

    def get_seed_scripts(self) -> dict:
        return self.seed_service.list_seed_scripts()

    def generate_demo_seed(self) -> dict:
        return self.seed_service.generate_full_demo()

    def get_fixture_types(self) -> dict:
        return self.fixture_service.list_fixture_types()

    def build_test_fixtures(self, organization_id: str = "org-fixture-1") -> dict:
        return self.fixture_service.build_test_suite(
            organization_id=organization_id,
        )

    def get_query_optimization_report(self) -> dict:
        return self.query_service.get_optimization_report()

    def batch_load_related(
        self,
        *,
        parent_records: list[dict],
        child_records: list[dict],
        parent_key: str = "id",
        foreign_key: str = "project_id",
    ) -> dict:
        return self.query_service.batch_load(
            parent_records=parent_records,
            child_records=child_records,
            parent_key=parent_key,
            foreign_key=foreign_key,
        )

    def get_connection_pool_config(self) -> dict:
        return self.pool_service.get_configuration()

    def get_connection_pool_stats(self) -> dict:
        return self.pool_service.get_stats()

    def get_tenant_isolation_report(self) -> dict:
        return self.tenant_service.get_isolation_report()

    def get_retention_policies(self) -> dict:
        return self.retention_service.list_policies()
