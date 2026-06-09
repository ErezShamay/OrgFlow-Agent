#!/usr/bin/env python3
"""Apply field-report offline sync SQL migrations to Supabase Postgres.

Runs, in order:
  - deploy/sql/2026060301_field_visit_report_line_grouping.sql
  - deploy/sql/2026060304_field_visit_report_client_uuids.sql

Requires DATABASE_URL or SUPABASE_DB_PASSWORD in .env (see apply_project_columns_migration.py).
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[1]
MIGRATIONS = (
    "2026060301_field_visit_report_line_grouping.sql",
    "2026060304_field_visit_report_client_uuids.sql",
)
REQUIRED_COLUMNS = {
    "field_visit_reports": ("client_report_uuid",),
    "field_visit_report_lines": (
        "client_line_uuid",
        "group_key",
        "group_label_he",
        "block_id",
    ),
}


def _python_executable() -> str:
    venv_python = REPO_ROOT / ".venv" / "bin" / "python3"
    if venv_python.is_file():
        return str(venv_python)
    return sys.executable


def verify_columns() -> bool:
    load_dotenv(REPO_ROOT / ".env")
    sys.path.insert(0, str(REPO_ROOT))

    from app.db.supabase_client import supabase

    ok = True
    for table, columns in REQUIRED_COLUMNS.items():
        for column in columns:
            try:
                supabase.table(table).select(column).limit(0).execute()
                print(f"  OK  {table}.{column}")
            except Exception:
                print(f"  MISSING  {table}.{column}")
                ok = False

    return ok


def main() -> int:
    load_dotenv(REPO_ROOT / ".env")
    apply_script = REPO_ROOT / "scripts" / "apply_project_columns_migration.py"
    python_executable = _python_executable()
    exit_code = 0

    print("Verifying columns before migration...")
    if verify_columns():
        print("All required columns already exist — nothing to apply.")
        return 0

    for migration in MIGRATIONS:
        print(f"Applying {migration}...")
        result = subprocess.run(
            [python_executable, str(apply_script), migration],
            cwd=REPO_ROOT,
        )
        if result.returncode != 0:
            exit_code = result.returncode
            break

    print("Verifying columns after migration...")
    if not verify_columns():
        exit_code = 1

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
