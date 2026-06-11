from __future__ import annotations

from pathlib import Path

import pytest

from app.schemas.qc_migration import (
    QUALITY_ISSUE_PHOTOS_MIGRATION_FILENAME,
    QUALITY_ISSUE_PHOTOS_MIGRATION_VERSION,
    QUALITY_ISSUE_PHOTOS_REQUIRED_COLUMNS,
    QUALITY_ISSUE_PHOTOS_REQUIRED_CONSTRAINTS,
    QUALITY_ISSUE_PHOTOS_REQUIRED_INDEXES,
    read_quality_issue_photos_migration_sql,
)


@pytest.fixture
def migration_sql() -> str:
    return read_quality_issue_photos_migration_sql()


def test_migration_file_exists() -> None:
    path = (
        Path(__file__).resolve().parents[1]
        / "db"
        / "migrations"
        / QUALITY_ISSUE_PHOTOS_MIGRATION_FILENAME
    )
    assert path.is_file()


def test_deploy_sql_matches_db_migration() -> None:
    root = Path(__file__).resolve().parents[1]
    db_sql = (
        root / "db" / "migrations" / QUALITY_ISSUE_PHOTOS_MIGRATION_FILENAME
    ).read_text(encoding="utf-8")
    deploy_sql = (
        root / "deploy" / "sql" / QUALITY_ISSUE_PHOTOS_MIGRATION_FILENAME
    ).read_text(encoding="utf-8")
    assert db_sql == deploy_sql


def test_migration_creates_quality_issue_photos_table(
    migration_sql: str,
) -> None:
    assert (
        "CREATE TABLE IF NOT EXISTS public.quality_issue_photos"
        in migration_sql
    )
    assert QUALITY_ISSUE_PHOTOS_MIGRATION_VERSION == "2026060915"


@pytest.mark.parametrize("column", QUALITY_ISSUE_PHOTOS_REQUIRED_COLUMNS)
def test_migration_includes_required_columns(
    migration_sql: str,
    column: str,
) -> None:
    assert column in migration_sql


@pytest.mark.parametrize("index_name", QUALITY_ISSUE_PHOTOS_REQUIRED_INDEXES)
def test_migration_includes_spec_indexes(
    migration_sql: str,
    index_name: str,
) -> None:
    assert index_name in migration_sql


@pytest.mark.parametrize("constraint", QUALITY_ISSUE_PHOTOS_REQUIRED_CONSTRAINTS)
def test_migration_includes_constraints(
    migration_sql: str,
    constraint: str,
) -> None:
    assert constraint in migration_sql
