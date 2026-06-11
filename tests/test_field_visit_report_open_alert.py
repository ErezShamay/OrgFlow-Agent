"""Roadmap 4.3.2 - IN_PROGRESS report open > 3 days email reminders."""

from __future__ import annotations

from datetime import timedelta
from unittest.mock import MagicMock

from app.services.field_visit_report_open_alert_service import (
    OPEN_REPORT_REMINDER_DAYS_THRESHOLD,
    FieldVisitReportOpenAlertService,
    OpenReportAlertDedupStore,
    build_supervisor_report_digests,
    days_open_for_report,
    is_report_open_over_days,
    select_open_reports_over_days,
)
from app.tools.notification_tool import NotificationTool
from tests.quality_issues_test_support import FakeProjectRepository, qc_now
from tests.test_field_visit_reports import FakeVisitReportRepository


NOW = qc_now()


def test_days_open_for_report_uses_created_at() -> None:
    report = {"created_at": NOW - timedelta(days=5)}

    assert days_open_for_report(report, now=NOW) == 5


def test_is_report_open_over_days_boundary() -> None:
    exactly_3 = {
        "status": "IN_PROGRESS",
        "created_at": NOW - timedelta(days=3),
    }
    over_3 = {
        "status": "IN_PROGRESS",
        "created_at": NOW - timedelta(days=4),
    }
    closed = {
        "status": "CLOSED",
        "created_at": NOW - timedelta(days=10),
    }

    assert not is_report_open_over_days(
        exactly_3,
        threshold=OPEN_REPORT_REMINDER_DAYS_THRESHOLD,
        now=NOW,
    )
    assert is_report_open_over_days(
        over_3,
        threshold=OPEN_REPORT_REMINDER_DAYS_THRESHOLD,
        now=NOW,
    )
    assert not is_report_open_over_days(
        closed,
        threshold=OPEN_REPORT_REMINDER_DAYS_THRESHOLD,
        now=NOW,
    )


def test_select_open_reports_over_days() -> None:
    reports = [
        {
            "id": "report-1",
            "status": "IN_PROGRESS",
            "created_at": NOW - timedelta(days=5),
            "visit_date": "2026-06-01",
        },
        {
            "id": "report-2",
            "status": "IN_PROGRESS",
            "created_at": NOW - timedelta(days=2),
            "visit_date": "2026-06-07",
        },
    ]

    overdue = select_open_reports_over_days(reports, now=NOW)

    assert [report["id"] for report in overdue] == ["report-1"]


def test_build_supervisor_report_digests_groups_by_email() -> None:
    overdue_reports = [
        {
            "id": "report-1",
            "project_id": "proj-1",
            "visit_date": "2026-06-01",
            "visit_type": "STRUCTURE",
            "created_at": NOW - timedelta(days=5),
        },
        {
            "id": "report-2",
            "project_id": "proj-2",
            "visit_date": "2026-06-02",
            "visit_type": "FINISHING",
            "created_at": NOW - timedelta(days=6),
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

    digests = build_supervisor_report_digests(
        overdue_reports,
        projects_by_id=projects_by_id,
        now=NOW,
    )

    assert len(digests) == 1
    assert digests[0]["supervisor_email"] == "yossi@example.com"
    assert len(digests[0]["reports"]) == 2


def test_notification_tool_builds_open_report_reminder_messages() -> None:
    tool = NotificationTool()
    reminders = tool.build_open_report_reminder_messages(
        [
            {
                "supervisor_email": "yossi@example.com",
                "supervisor_name": "יוסי",
                "reports": [
                    {
                        "report_id": "report-1",
                        "project_name": "האורנים 7",
                        "visit_date": "2026-06-01",
                        "visit_type": "STRUCTURE",
                        "days_open": 5,
                    }
                ],
            }
        ]
    )

    assert len(reminders) == 1
    assert reminders[0]["to"] == "yossi@example.com"
    assert "דוח" in reminders[0]["subject"]
    assert "האורנים 7" in reminders[0]["body"]
    assert "OrgFlow QC" in reminders[0]["body"]


def test_service_sends_email_for_overdue_open_report() -> None:
    report_repo = FakeVisitReportRepository()
    report_repo.create(
        organization_id="org-1",
        project_id="proj-1",
        visit_date="2026-06-01",
        visit_type="STRUCTURE",
        created_at=(NOW - timedelta(days=5)).isoformat(),
        updated_at=(NOW - timedelta(days=5)).isoformat(),
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
    notification_tool.build_open_report_reminder_messages.return_value = [
        {
            "to": "yossi@example.com",
            "subject": "תזכורת",
            "body": "test",
            "reports": [{"report_id": "report-1"}],
        }
    ]
    notification_tool.send_reminders.return_value = [
        {"to": "yossi@example.com", "status": "SENT"}
    ]

    service = FieldVisitReportOpenAlertService(
        report_repository=report_repo,
        project_repository=projects,
        notification_tool=notification_tool,
    )
    result = service.run_for_organization(
        organization_id="org-1",
        now=NOW,
    )

    assert result.overdue_report_count == 1
    assert result.digest_count == 1
    assert result.deliveries[0].status == "SENT"
    notification_tool.send_reminders.assert_called_once()


def test_service_dedups_same_report_on_same_day() -> None:
    report_repo = FakeVisitReportRepository()
    report_repo.create(
        organization_id="org-1",
        project_id="proj-1",
        visit_date="2026-06-01",
        created_at=(NOW - timedelta(days=5)).isoformat(),
        updated_at=(NOW - timedelta(days=5)).isoformat(),
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
    notification_tool.build_open_report_reminder_messages.return_value = []
    dedup_store = OpenReportAlertDedupStore()
    dedup_store.mark_alerted("report-1", alert_date=NOW.date().isoformat())

    service = FieldVisitReportOpenAlertService(
        report_repository=report_repo,
        project_repository=projects,
        notification_tool=notification_tool,
        dedup_store=dedup_store,
    )
    result = service.run_for_organization(
        organization_id="org-1",
        now=NOW,
    )

    assert result.overdue_report_count == 1
    assert result.digest_count == 0
    assert result.skipped_report_ids == ["report-1"]
    notification_tool.send_reminders.assert_not_called()
