from __future__ import annotations

from app.db.schema_registry import MIGRATION_SCRIPTS, SCHEMA_VERSION
from app.repositories.migration_repository import MigrationRepository


class MigrationManagementService:
    def __init__(
        self,
        migration_repository: MigrationRepository | None = None,
    ):
        self.migration_repository = (
            migration_repository or MigrationRepository()
        )

    def get_status(self) -> dict:
        applied = self.migration_repository.list_applied()
        applied_versions = {item["version"] for item in applied}
        pending = [
            script
            for script in MIGRATION_SCRIPTS
            if script["version"] not in applied_versions
        ]
        return {
            "schema_version": SCHEMA_VERSION,
            "applied_count": len(applied),
            "pending_count": len(pending),
            "applied": applied,
            "pending": pending,
            "up_to_date": len(pending) == 0,
        }

    def list_migrations(self) -> dict:
        applied_versions = {
            item["version"]
            for item in self.migration_repository.list_applied()
        }
        migrations = []
        for script in MIGRATION_SCRIPTS:
            migrations.append({
                **script,
                "status": (
                    "APPLIED"
                    if script["version"] in applied_versions
                    else "PENDING"
                ),
            })
        return {
            "migrations": migrations,
            "total": len(migrations),
        }

    def apply_pending(self) -> dict:
        applied_versions = {
            item["version"]
            for item in self.migration_repository.list_applied()
        }
        newly_applied = []
        for script in MIGRATION_SCRIPTS:
            if script["version"] in applied_versions:
                continue
            record = self.migration_repository.record_applied(
                version=script["version"],
                name=script["name"],
                description=script["description"],
            )
            newly_applied.append(record)
        return {
            "applied": newly_applied,
            "count": len(newly_applied),
            "status": self.get_status(),
        }
