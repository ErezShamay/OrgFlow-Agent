"""
QC migrations metadata - column and index expectations for QC registry tables.

See db/migrations/2026060912_quality_issues.sql (1.1.1)
and db/migrations/2026060913_quality_issue_events.sql (1.1.2).
"""

from __future__ import annotations

from pathlib import Path

QUALITY_ISSUES_MIGRATION_VERSION = "2026060912"
QUALITY_ISSUES_MIGRATION_FILENAME = (
    f"{QUALITY_ISSUES_MIGRATION_VERSION}_quality_issues.sql"
)

QUALITY_ISSUES_REQUIRED_COLUMNS: tuple[str, ...] = (
    "id",
    "organization_id",
    "project_id",
    "title",
    "description",
    "location",
    "trade",
    "group_key",
    "group_label_he",
    "standard_ref",
    "severity",
    "status",
    "catalog_issue_id",
    "first_seen_report_id",
    "first_seen_line_id",
    "first_seen_at",
    "last_seen_report_id",
    "last_seen_line_id",
    "last_seen_at",
    "closed_at",
    "closed_by",
    "recurrence_count",
    "photo_ids",
    "materialization_key",
    "created_at",
    "updated_at",
)

QUALITY_ISSUES_REQUIRED_INDEXES: tuple[str, ...] = (
    "quality_issues_org_project_status_idx",
    "quality_issues_org_project_open_severity_idx",
    "quality_issues_org_materialization_key_uniq",
    "quality_issues_project_matching_idx",
)

QUALITY_ISSUES_REQUIRED_CONSTRAINTS: tuple[str, ...] = (
    "quality_issues_severity_check",
    "quality_issues_status_check",
    "quality_issues_recurrence_count_check",
    "quality_issues_organization_id_fkey",
    "quality_issues_project_id_fkey",
)


def quality_issues_migration_path() -> Path:
    return (
        Path(__file__).resolve().parents[2]
        / "db"
        / "migrations"
        / QUALITY_ISSUES_MIGRATION_FILENAME
    )


def read_quality_issues_migration_sql() -> str:
    return quality_issues_migration_path().read_text(encoding="utf-8")


QUALITY_ISSUE_EVENTS_MIGRATION_VERSION = "2026060913"
QUALITY_ISSUE_EVENTS_MIGRATION_FILENAME = (
    f"{QUALITY_ISSUE_EVENTS_MIGRATION_VERSION}_quality_issue_events.sql"
)

QUALITY_ISSUE_EVENTS_REQUIRED_COLUMNS: tuple[str, ...] = (
    "id",
    "issue_id",
    "event_type",
    "report_id",
    "line_id",
    "actor_id",
    "payload",
    "created_at",
)

QUALITY_ISSUE_EVENT_TYPES: tuple[str, ...] = (
    "DETECTED",
    "LINKED",
    "REMEDIATION_SUBMITTED",
    "VERIFIED_CLOSED",
    "REOPENED",
    "STATUS_CHANGED",
)

QUALITY_ISSUE_EVENTS_REQUIRED_INDEXES: tuple[str, ...] = (
    "quality_issue_events_issue_created_at_idx",
    "quality_issue_events_report_id_idx",
    "quality_issue_events_event_type_created_at_idx",
)

QUALITY_ISSUE_EVENTS_REQUIRED_CONSTRAINTS: tuple[str, ...] = (
    "quality_issue_events_event_type_check",
    "quality_issue_events_issue_id_fkey",
    "quality_issue_events_report_id_fkey",
    "quality_issue_events_line_id_fkey",
    "quality_issue_events_actor_id_fkey",
)


def quality_issue_events_migration_path() -> Path:
    return (
        Path(__file__).resolve().parents[2]
        / "db"
        / "migrations"
        / QUALITY_ISSUE_EVENTS_MIGRATION_FILENAME
    )


def read_quality_issue_events_migration_sql() -> str:
    return quality_issue_events_migration_path().read_text(encoding="utf-8")


QUALITY_ISSUE_PHOTOS_MIGRATION_VERSION = "2026060915"
QUALITY_ISSUE_PHOTOS_MIGRATION_FILENAME = (
    f"{QUALITY_ISSUE_PHOTOS_MIGRATION_VERSION}_quality_issue_photos.sql"
)

QUALITY_ISSUE_PHOTOS_REQUIRED_COLUMNS: tuple[str, ...] = (
    "id",
    "organization_id",
    "project_id",
    "issue_id",
    "storage_path",
    "kind",
    "sort_order",
    "created_at",
    "updated_at",
)

QUALITY_ISSUE_PHOTOS_REQUIRED_INDEXES: tuple[str, ...] = (
    "quality_issue_photos_issue_sort_idx",
    "quality_issue_photos_org_idx",
)

QUALITY_ISSUE_PHOTOS_REQUIRED_CONSTRAINTS: tuple[str, ...] = (
    "quality_issue_photos_kind_check",
    "quality_issue_photos_organization_id_fkey",
    "quality_issue_photos_project_id_fkey",
    "quality_issue_photos_issue_id_fkey",
)


def quality_issue_photos_migration_path() -> Path:
    return (
        Path(__file__).resolve().parents[2]
        / "db"
        / "migrations"
        / QUALITY_ISSUE_PHOTOS_MIGRATION_FILENAME
    )


def read_quality_issue_photos_migration_sql() -> str:
    return quality_issue_photos_migration_path().read_text(encoding="utf-8")
