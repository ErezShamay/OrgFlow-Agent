from __future__ import annotations

from pathlib import Path


def test_linked_issue_migration_files_exist_and_match() -> None:
    root = Path(__file__).resolve().parents[1]
    filename = "2026060914_field_visit_report_line_linked_issue.sql"
    db_sql = (root / "db" / "migrations" / filename).read_text(encoding="utf-8")
    deploy_sql = (root / "deploy" / "sql" / filename).read_text(encoding="utf-8")

    assert db_sql == deploy_sql
    assert "linked_issue_id" in db_sql
    assert "quality_issues" in db_sql
