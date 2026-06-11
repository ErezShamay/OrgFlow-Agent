#!/usr/bin/env python3
"""Verify project metadata columns exist and all projects/orgs still load."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

EXPECTED_COLUMNS = (
    "owner_id",
    "tags",
    "lifecycle_phase",
    "scheme",
    "developer_pm_name",
    "accompanying_lawyer",
    "architect_name",
    "site_manager_name",
    "city",
    "housing_units_count",
    "project_start_date",
    "project_end_date",
    "project_grace_end_date",
    "structure_documentation_date",
    "illustration_url",
    "illustration_source_he",
)


def _check_columns_via_supabase() -> tuple[bool, list[str]]:
    from app.db.supabase_client import supabase

    messages: list[str] = []
    ok = True

    try:
        response = (
            supabase.table("projects")
            .select(",".join(["id", "project_name", "organization_id", *EXPECTED_COLUMNS]))
            .limit(1)
            .execute()
        )
        messages.append("Supabase select with new columns: OK")
        if response.data:
            row = response.data[0]
            for col in EXPECTED_COLUMNS:
                if col not in row:
                    ok = False
                    messages.append(f"Missing column in API response: {col}")
    except Exception as error:
        ok = False
        messages.append(f"Supabase select failed: {error}")

    return ok, messages


def _check_all_projects_load() -> tuple[bool, list[str]]:
    from app.repositories.project_repository import ProjectRepository

    messages: list[str] = []
    ok = True
    repo = ProjectRepository()

    try:
        projects = repo.get_all_projects()
    except Exception as error:
        return False, [f"get_all_projects failed: {error}"]

    messages.append(f"Loaded {len(projects)} project(s) via repository")

    org_ids: dict[str, list[str]] = {}
    for project in projects:
        org_id = project.get("organization_id") or "UNSCOPED"
        org_ids.setdefault(org_id, []).append(project.get("project_name", "?"))

        for col in EXPECTED_COLUMNS:
            if col not in project:
                ok = False
                messages.append(
                    f"Project {project.get('id')} missing column '{col}' in row"
                )

    try:
        org_response = (
            repo.client.table("organizations")
            .select("id,organization_name")
            .execute()
        )
        org_names = {
            row["id"]: row.get("organization_name", "?")
            for row in (org_response.data or [])
        }
    except Exception as error:
        org_names = {}
        messages.append(f"Could not load organizations: {error}")

    messages.append("Projects by organization:")
    for org_id, names in sorted(org_ids.items(), key=lambda item: item[0]):
        label = org_names.get(org_id, org_id)
        messages.append(f"  - {label}: {len(names)} project(s)")

    return ok, messages


def _check_postgres_columns() -> tuple[bool, list[str]]:
    from scripts.apply_project_columns_migration import _connection_candidates

    messages: list[str] = []
    supabase_url = os.getenv("SUPABASE_URL", "").strip()
    password = os.getenv("SUPABASE_DB_PASSWORD", "").strip()
    database_url = os.getenv("DATABASE_URL", "").strip()

    if not database_url and not password:
        messages.append(
            "Skipped direct Postgres check (no DATABASE_URL / SUPABASE_DB_PASSWORD)"
        )
        return True, messages

    import psycopg

    sql = """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'projects'
          AND column_name = ANY(%s)
        ORDER BY column_name
    """

    candidates = _connection_candidates(
        supabase_url=supabase_url,
        password=password or "unused",
    )
    if database_url:
        candidates.insert(0, database_url)

    last_error: Exception | None = None
    for conninfo in candidates:
        try:
            with psycopg.connect(conninfo, connect_timeout=8) as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, (list(EXPECTED_COLUMNS),))
                    found = {row[0] for row in cursor.fetchall()}
            missing = [col for col in EXPECTED_COLUMNS if col not in found]
            if missing:
                return False, [
                    f"Postgres missing columns on projects: {', '.join(missing)}"
                ]
            messages.append(
                f"Postgres schema: all {len(EXPECTED_COLUMNS)} columns present"
            )
            return True, messages
        except Exception as error:
            last_error = error
            continue

    messages.append(f"Postgres check failed: {last_error}")
    return False, messages


def main() -> int:
    load_dotenv(REPO_ROOT / ".env")

    checks: list[tuple[str, tuple[bool, list[str]]]] = [
        ("postgres_schema", _check_postgres_columns()),
        ("supabase_api", _check_columns_via_supabase()),
        ("all_projects", _check_all_projects_load()),
    ]

    all_ok = True
    for name, (ok, messages) in checks:
        status = "PASS" if ok else "FAIL"
        print(f"[{status}] {name}")
        for message in messages:
            print(f"  {message}")
        if not ok:
            all_ok = False

    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
