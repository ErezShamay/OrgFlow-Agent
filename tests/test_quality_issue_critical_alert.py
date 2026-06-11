"""Roadmap 4.3.1 - CRITICAL open > 7 days email alerts."""

from __future__ import annotations

from datetime import timedelta
from unittest.mock import MagicMock

import pytest

from app.services.quality_issue_critical_alert_service import (
    CRITICAL_ALERT_DAYS_THRESHOLD,
    CriticalAlertDedupStore,
    QualityIssueCriticalAlertService,
    build_supervisor_digests,
    select_critical_stale_issues,
)
from app.tools.notification_tool import NotificationTool
from tests.quality_issues_test_support import (
    FakeProjectRepository,
    InMemoryQualityIssueRepository,
    qc_create_request,
    qc_now,
)


NOW = qc_now()


def test_select_critical_stale_issues_uses_seven_day_threshold() -> None:
    open_issues = [
        {
            "id": "issue-1",
            "severity": "CRITICAL",
            "first_seen_at": NOW - timedelta(days=8),
        },
        {
            "id": "issue-2",
            "severity": "CRITICAL",
            "first_seen_at": NOW - timedelta(days=7),
        },
        {
            "id": "issue-3",
            "severity": "HIGH",
            "first_seen_at": NOW - timedelta(days=20),
        },
    ]

    stale = select_critical_stale_issues(
        open_issues,
        threshold=CRITICAL_ALERT_DAYS_THRESHOLD,
        now=NOW,
    )

    assert [issue["id"] for issue in stale] == ["issue-1"]


def test_build_supervisor_digests_groups_by_email() -> None:
    stale_issues = [
        {
            "id": "issue-1",
            "project_id": "proj-1",
            "title": "נזילה",
            "location": "קומה 3",
            "trade": "אינסטלציה",
            "first_seen_at": NOW - timedelta(days=10),
        },
        {
            "id": "issue-2",
            "project_id": "proj-2",
            "title": "סדק",
            "location": None,
            "trade": None,
            "first_seen_at": NOW - timedelta(days=12),
        },
    ]
    projects_by_id = {
        "proj-1": {
            "id": "proj-1",
            "project_name": "האורנים 7",
            "supervisor_name": "יוסי",
            "supervisor_email": "yossi@example.com",
        },
        "proj-2": {
            "id": "proj-2",
            "project_name": "פרויקט ב",
            "supervisor_name": "יוסי",
            "supervisor_email": "yossi@example.com",
        },
    }

    digests = build_supervisor_digests(
        stale_issues,
        projects_by_id=projects_by_id,
        now=NOW,
    )

    assert len(digests) == 1
    assert digests[0]["supervisor_email"] == "yossi@example.com"
    assert len(digests[0]["issues"]) == 2


def test_notification_tool_builds_critical_stale_messages() -> None:
    tool = NotificationTool()
    reminders = tool.build_critical_stale_issue_messages(
        [
            {
                "supervisor_email": "yossi@example.com",
                "supervisor_name": "יוסי",
                "issues": [
                    {
                        "issue_id": "issue-1",
                        "project_name": "האורנים 7",
                        "title": "נזילה",
                        "location": "קומה 3",
                        "trade": "אינסטלציה",
                        "days_open": 10,
                    }
                ],
            }
        ]
    )

    assert len(reminders) == 1
    assert reminders[0]["to"] == "yossi@example.com"
    assert "ליקוי קריטי" in reminders[0]["subject"]
    assert "נזילה" in reminders[0]["body"]
    assert "OrgFlow QC" in reminders[0]["body"]


def test_service_sends_email_for_stale_critical_issue() -> None:
    issue_repo = InMemoryQualityIssueRepository()
    issue_repo.create(
        organization_id="org-1",
        project_id="proj-1",
        request=qc_create_request(
            title="נזילה קריטית",
            severity="CRITICAL",
            first_seen_at=NOW - timedelta(days=10),
            materialization_key="report-1:line-1",
        ),
    )
    projects = FakeProjectRepository(
        projects={
            "proj-1": {
                "id": "proj-1",
                "organization_id": "org-1",
                "project_name": "האורנים 7",
                "supervisor_name": "יוסי",
                "supervisor_email": "yossi@example.com",
            }
        }
    )
    notification_tool = MagicMock()
    notification_tool.build_critical_stale_issue_messages.return_value = [
        {
            "to": "yossi@example.com",
            "subject": "התראת ליקוי קריטי",
            "body": "test",
            "issues": [{"issue_id": "issue-1"}],
        }
    ]
    notification_tool.send_reminders.return_value = [
        {"to": "yossi@example.com", "status": "SENT"}
    ]

    service = QualityIssueCriticalAlertService(
        issue_repository=issue_repo,
        project_repository=projects,
        notification_tool=notification_tool,
    )
    result = service.run_for_organization(
        organization_id="org-1",
        now=NOW,
    )

    assert result.stale_issue_count == 1
    assert result.digest_count == 1
    assert result.deliveries[0].status == "SENT"
    notification_tool.send_reminders.assert_called_once()


def test_service_dedups_same_issue_on_same_day() -> None:
    issue_repo = InMemoryQualityIssueRepository()
    issue_repo.create(
        organization_id="org-1",
        project_id="proj-1",
        request=qc_create_request(
            title="נזילה קריטית",
            severity="CRITICAL",
            first_seen_at=NOW - timedelta(days=10),
            materialization_key="report-1:line-1",
        ),
    )
    projects = FakeProjectRepository(
        projects={
            "proj-1": {
                "id": "proj-1",
                "organization_id": "org-1",
                "project_name": "האורנים 7",
                "supervisor_name": "יוסי",
                "supervisor_email": "yossi@example.com",
            }
        }
    )
    notification_tool = MagicMock()
    notification_tool.build_critical_stale_issue_messages.return_value = []
    dedup_store = CriticalAlertDedupStore()
    dedup_store.mark_alerted("issue-1", alert_date=NOW.date().isoformat())

    service = QualityIssueCriticalAlertService(
        issue_repository=issue_repo,
        project_repository=projects,
        notification_tool=notification_tool,
        dedup_store=dedup_store,
    )
    result = service.run_for_organization(
        organization_id="org-1",
        now=NOW,
    )

    assert result.stale_issue_count == 1
    assert result.digest_count == 0
    assert result.skipped_issue_ids == ["issue-1"]
    notification_tool.send_reminders.assert_not_called()


def test_service_skips_when_no_supervisor_email() -> None:
    issue_repo = InMemoryQualityIssueRepository()
    issue_repo.create(
        organization_id="org-1",
        project_id="proj-1",
        request=qc_create_request(
            title="נזילה קריטית",
            severity="CRITICAL",
            first_seen_at=NOW - timedelta(days=10),
            materialization_key="report-1:line-1",
        ),
    )
    projects = FakeProjectRepository(
        projects={
            "proj-1": {
                "id": "proj-1",
                "organization_id": "org-1",
                "project_name": "האורנים 7",
                "supervisor_name": "יוסי",
            }
        }
    )
    notification_tool = MagicMock()
    notification_tool.build_critical_stale_issue_messages.return_value = [
        {
            "to": None,
            "subject": "התראת ליקוי קריטי",
            "body": "test",
            "issues": [{"issue_id": "issue-1"}],
        }
    ]
    notification_tool.send_reminders.return_value = [
        {"to": None, "status": "SKIPPED"}
    ]

    service = QualityIssueCriticalAlertService(
        issue_repository=issue_repo,
        project_repository=projects,
        notification_tool=notification_tool,
    )
    result = service.run_for_organization(
        organization_id="org-1",
        now=NOW,
    )

    assert result.deliveries[0].status == "SKIPPED"
