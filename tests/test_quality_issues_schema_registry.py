from __future__ import annotations

from app.db.schema_registry import (
    MIGRATION_SCRIPTS,
    ORGFLOW_QUALITY_ISSUE_EVENT_SCOPE,
    ORGFLOW_TENANT_ISOLATION,
    SCHEMA_VERSION,
    TABLES,
    get_tenant_scoped_tables,
)
from app.services.rls_policy_service import RlsPolicyService


def test_schema_version_includes_quality_issue_migrations() -> None:
    assert SCHEMA_VERSION == "2026060915"


def test_quality_issues_registered_in_tables() -> None:
    schema = TABLES["quality_issues"]
    assert schema.tenant_column == "organization_id"
    assert schema.soft_delete_column is None
    assert len(schema.foreign_keys) >= 2
    assert len(schema.indexes) >= 5
    assert len(schema.rls_policies) == 1
    assert (
        schema.rls_policies[0].using_expression
        == ORGFLOW_TENANT_ISOLATION
    )


def test_quality_issue_events_registered_with_issue_scoped_rls() -> None:
    schema = TABLES["quality_issue_events"]
    assert schema.tenant_column is None
    assert len(schema.foreign_keys) >= 1
    assert schema.foreign_keys[0].column == "issue_id"
    assert schema.foreign_keys[0].references_table == "quality_issues"
    assert len(schema.rls_policies) == 1
    assert (
        schema.rls_policies[0].using_expression
        == ORGFLOW_QUALITY_ISSUE_EVENT_SCOPE
    )


def test_quality_issue_photos_registered_in_tables() -> None:
    schema = TABLES["quality_issue_photos"]
    assert schema.tenant_column == "organization_id"
    assert schema.foreign_keys[2].column == "issue_id"
    assert schema.foreign_keys[2].references_table == "quality_issues"


def test_quality_issues_in_tenant_scoped_tables() -> None:
    assert "quality_issues" in get_tenant_scoped_tables()
    assert "quality_issue_photos" in get_tenant_scoped_tables()


def test_migrations_registered_in_schema_registry() -> None:
    versions = {script["version"]: script for script in MIGRATION_SCRIPTS}

    issues_entry = versions["2026060912"]
    assert issues_entry["name"] == "quality_issues"
    assert issues_entry["tables"] == ["quality_issues"]

    events_entry = versions["2026060913"]
    assert events_entry["name"] == "quality_issue_events"
    assert events_entry["tables"] == ["quality_issue_events"]

    photos_entry = versions["2026060915"]
    assert photos_entry["name"] == "quality_issue_photos"
    assert photos_entry["tables"] == ["quality_issue_photos"]


def test_rls_coverage_includes_quality_issues() -> None:
    service = RlsPolicyService()
    coverage = service.validate_coverage()
    assert coverage["valid"] is True

    policies = service.get_table_policies("quality_issues")
    assert policies["found"] is True
    assert policies["policies"][0]["policy_name"] == (
        "quality_issues_tenant_isolation"
    )

    event_policies = service.get_table_policies("quality_issue_events")
    assert event_policies["found"] is True
    assert (
        event_policies["policies"][0]["policy_name"]
        == "quality_issue_events_tenant_isolation"
    )
