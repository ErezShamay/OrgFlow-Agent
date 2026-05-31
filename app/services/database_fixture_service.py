from __future__ import annotations

from uuid import uuid4


class DatabaseFixtureService:
    def build_project_fixture(
        self,
        *,
        organization_id: str = "org-fixture-1",
        overrides: dict | None = None,
    ) -> dict:
        fixture = {
            "id": str(uuid4()),
            "organization_id": organization_id,
            "project_name": "Fixture Project",
            "status": "ACTIVE",
            "health_score": 75,
        }
        if overrides:
            fixture.update(overrides)
        return fixture

    def build_operational_action_fixture(
        self,
        *,
        project_id: str,
        organization_id: str = "org-fixture-1",
        overrides: dict | None = None,
    ) -> dict:
        fixture = {
            "id": str(uuid4()),
            "project_id": project_id,
            "organization_id": organization_id,
            "title": "Fixture Action",
            "status": "OPEN",
            "priority": "MEDIUM",
        }
        if overrides:
            fixture.update(overrides)
        return fixture

    def build_test_suite(
        self,
        *,
        organization_id: str = "org-fixture-1",
    ) -> dict:
        project = self.build_project_fixture(organization_id=organization_id)
        action = self.build_operational_action_fixture(
            project_id=project["id"],
            organization_id=organization_id,
        )
        return {
            "organization_id": organization_id,
            "project": project,
            "operational_action": action,
            "fixture_count": 2,
        }

    def list_fixture_types(self) -> dict:
        return {
            "types": ["project", "operational_action", "test_suite"],
        }
