from __future__ import annotations

from pathlib import Path

import pytest

from app.schemas.qc_migration import (
    QUALITY_ISSUES_MIGRATION_FILENAME,
    QUALITY_ISSUES_MIGRATION_VERSION,
    QUALITY_ISSUES_REQUIRED_COLUMNS,
    QUALITY_ISSUES_REQUIRED_CONSTRAINTS,
    QUALITY_ISSUES_REQUIRED_INDEXES,
    read_quality_issues_migration_sql,
)


@pytest.fixture
def migration_sql() -> str:
    return read_quality_issues_migration_sql()


def test_migration_file_exists() -> None:
    path = (
        Path(__file__).resolve().parents[1]
        / "db"
        / "migrations"
        / QUALITY_ISSUES_MIGRATION_FILENAME
    )
    assert path.is_file()


def test_deploy_sql_matches_db_migration() -> None:
    root = Path(__file__).resolve().parents[1]
    db_sql = (
        root / "db" / "migrations" / QUALITY_ISSUES_MIGRATION_FILENAME
    ).read_text(encoding="utf-8")
    deploy_sql = (
        root / "deploy" / "sql" / QUALITY_ISSUES_MIGRATION_FILENAME
    ).read_text(encoding="utf-8")
    assert db_sql == deploy_sql


def test_migration_creates_quality_issues_table(migration_sql: str) -> None:
    assert "CREATE TABLE IF NOT EXISTS public.quality_issues" in migration_sql
    assert QUALITY_ISSUES_MIGRATION_VERSION == "2026060912"


@pytest.mark.parametrize("column", QUALITY_ISSUES_REQUIRED_COLUMNS)
def test_migration_includes_required_columns(
    migration_sql: str,
    column: str,
) -> None:
    assert column in migration_sql


@pytest.mark.parametrize("index_name", QUALITY_ISSUES_REQUIRED_INDEXES)
def test_migration_includes_spec_indexes(
    migration_sql: str,
    index_name: str,
) -> None:
    assert index_name in migration_sql


@pytest.mark.parametrize("constraint", QUALITY_ISSUES_REQUIRED_CONSTRAINTS)
def test_migration_includes_constraints(
    migration_sql: str,
    constraint: str,
) -> None:
    assert constraint in migration_sql


def test_migration_enforces_status_and_severity_enums(migration_sql: str) -> None:
    assert "'IN_REMEDIATION'" in migration_sql
    assert "'PENDING_VERIFICATION'" in migration_sql
    assert "'REOPENED'" in migration_sql
    assert "'CRITICAL'" in migration_sql


def test_migration_idempotency_unique_materialization_key(
    migration_sql: str,
) -> None:
    assert "quality_issues_org_materialization_key_uniq" in migration_sql
    assert "organization_id, materialization_key" in migration_sql
