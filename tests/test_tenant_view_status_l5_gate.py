"""Gate L5 — tenant_view_status_he for resident portal (COMPETITIVE-LAYER-TASKS.md)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

from app.db.schema_registry import MIGRATION_SCRIPTS, SCHEMA_VERSION
from app.repositories.quality_issue_repository import (
    QUALITY_ISSUE_TENANT_VIEW_MIGRATION,
)
from app.schemas.quality_issue import (
    IssueVisibility,
    QualityIssueStatus,
    QualityIssueUpdateRequest,
    resolve_tenant_view_status_he,
)
from app.services.quality_issue_service import QualityIssueService
from app.services.resident_portal_service import ResidentPortalService
from tests.quality_issues_test_support import (
    FakeProjectRepository,
    InMemoryQualityIssueEventRepository,
    InMemoryQualityIssueRepository,
    qc_create_request,
)

REPO_ROOT = Path(__file__).resolve().parents[1]

TENANT_OPEN = "הקבלן זומן לתיקון הליקוי"
TENANT_PENDING = "הליקוי בבדיקה על ידי המפקח"
TENANT_CLOSED = "הליקוי טופל"


def test_migration_sql_adds_tenant_view_status_he_column() -> None:
    migration_path = REPO_ROOT / QUALITY_ISSUE_TENANT_VIEW_MIGRATION
    sql = migration_path.read_text(encoding="utf-8")

    assert "ALTER TABLE" in sql
    assert "quality_issues" in sql
    assert "tenant_view_status_he" in sql
    assert TENANT_OPEN in sql
    assert TENANT_PENDING in sql
    assert TENANT_CLOSED in sql


def test_migration_registered_in_schema_registry() -> None:
    assert SCHEMA_VERSION == "2026061803"

    entry = next(
        script
        for script in MIGRATION_SCRIPTS
        if script["version"] == "2026061803"
    )
    assert entry["name"] == "quality_issues_tenant_view_status_he"
    assert entry["tables"] == ["quality_issues"]


def test_resolve_tenant_view_status_he_default_mapping() -> None:
    assert (
        resolve_tenant_view_status_he(QualityIssueStatus.OPEN)
        == TENANT_OPEN
    )
    assert (
        resolve_tenant_view_status_he(QualityIssueStatus.IN_REMEDIATION)
        == TENANT_OPEN
    )
    assert (
        resolve_tenant_view_status_he(QualityIssueStatus.REOPENED)
        == TENANT_OPEN
    )
    assert (
        resolve_tenant_view_status_he(
            QualityIssueStatus.PENDING_VERIFICATION
        )
        == TENANT_PENDING
    )
    assert (
        resolve_tenant_view_status_he(QualityIssueStatus.CLOSED)
        == TENANT_CLOSED
    )


def test_repository_create_sets_tenant_view_status_he() -> None:
    issues = InMemoryQualityIssueRepository()
    issue = issues.create(
        organization_id="org-1",
        project_id="proj-1",
        request=qc_create_request(),
        status=QualityIssueStatus.PENDING_VERIFICATION.value,
    )
    assert issue["tenant_view_status_he"] == TENANT_PENDING


def test_status_update_sets_tenant_view_status_he() -> None:
    service = QualityIssueService(
        issue_repository=InMemoryQualityIssueRepository(),
        event_repository=InMemoryQualityIssueEventRepository(),
        project_repository=FakeProjectRepository(),
    )

    created = service.create_issue(
        organization_id="org-1",
        project_id="proj-1",
        request=qc_create_request(),
        actor_role="ADMIN",
    )
    assert created["tenant_view_status_he"] == TENANT_OPEN

    updated = service.update_issue(
        organization_id="org-1",
        issue_id=created["id"],
        request=QualityIssueUpdateRequest(
            status=QualityIssueStatus.CLOSED,
            last_seen_report_id="report-1",
        ),
        actor_role="ADMIN",
        actor_id="admin-1",
    )
    assert updated["tenant_view_status_he"] == TENANT_CLOSED


def test_resident_portal_returns_tenant_view_status_he() -> None:
    service = ResidentPortalService(
        issue_repository=MagicMock(
            is_storage_available=MagicMock(return_value=True),
            list_by_project=MagicMock(
                return_value=[
                    {
                        "id": "issue-open",
                        "organization_id": "org-1",
                        "project_id": "proj-1",
                        "group_key": "apartment:12",
                        "title": "נזילה",
                        "status": "OPEN",
                        "visibility": IssueVisibility.PUBLISHED.value,
                    },
                    {
                        "id": "issue-closed",
                        "organization_id": "org-1",
                        "project_id": "proj-1",
                        "group_key": "apartment:12",
                        "title": "איטום",
                        "status": "CLOSED",
                        "tenant_view_status_he": TENANT_CLOSED,
                        "visibility": IssueVisibility.PUBLISHED.value,
                    },
                ]
            ),
        )
    )

    issues, _records = service._collect_issues(
        organization_id="org-1",
        project_id="proj-1",
        group_key="apartment:12",
    )

    assert issues[0].tenant_view_status_he == TENANT_OPEN
    assert issues[1].tenant_view_status_he == TENANT_CLOSED


def test_schema_and_portal_ui_wired() -> None:
    schema = (REPO_ROOT / "app" / "schemas" / "quality_issue.py").read_text(
        encoding="utf-8"
    )
    portal_service = (
        REPO_ROOT / "app" / "services" / "resident_portal_service.py"
    ).read_text(encoding="utf-8")
    portal_view = (
        REPO_ROOT
        / "orgflow-ui"
        / "components"
        / "apartments"
        / "ResidentPortalView.tsx"
    ).read_text(encoding="utf-8")

    assert "tenant_view_status_he" in schema
    assert "resolve_tenant_view_status_he" in schema
    assert "tenant_view_status_he" in portal_service
    assert "tenant_view_status_he" in portal_view
