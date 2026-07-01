"""Gate L3 — draft issue notifications (COMPETITIVE-LAYER-TASKS.md)."""

from __future__ import annotations

from pathlib import Path

from app.schemas.quality_issue import IssueVisibility
from app.services.field_visit_report_service import FieldVisitReportService
from app.services.qc_notification_service import QcNotificationService
from app.services.quality_issue_materialization_service import (
    QualityIssueMaterializationService,
)
from app.services.workspace_activity_service import WorkspaceActivityService
from app.tools.notification_tool import NotificationTool
from tests.quality_issues_test_support import (
    FakeProjectRepository,
    InMemoryQualityIssueEventRepository,
    InMemoryQualityIssueRepository,
    qc_create_request,
)
from tests.test_field_visit_reports import (
    FakeVisitReportLinePhotoRepository,
    FakeVisitReportLineRepository,
    FakeVisitReportRepository,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


def _read_app_source() -> str:
    """Concatenates app/main.py with every app/routers/*.py and
    app/dependencies.py. Since the 2026-07 architecture-modularization
    refactor, main.py is a thin entrypoint (imports + middleware +
    include_router() calls) - route bodies and singleton wiring live in
    app/routers/*.py and app/dependencies.py. Gate tests that assert a
    given route path/snippet is "wired into the app" need to search the
    whole assembled surface, not main.py alone."""
    parts = [(REPO_ROOT / "app" / "main.py").read_text(encoding="utf-8")]
    parts.append((REPO_ROOT / "app" / "dependencies.py").read_text(encoding="utf-8"))
    for router_file in sorted((REPO_ROOT / "app" / "routers").glob("*.py")):
        if router_file.name == "__init__.py":
            continue
        parts.append(router_file.read_text(encoding="utf-8"))
    return "\n".join(parts)


class RecordingDraftNotificationTool(NotificationTool):
    def __init__(self) -> None:
        self.sent: list[dict] = []

    def build_draft_contractor_issue_messages(self, digests):
        return super().build_draft_contractor_issue_messages(digests)

    def send_reminders(self, reminders):
        self.sent.extend(reminders)
        return [{"to": item.get("to"), "status": "SENT"} for item in reminders]


def _create_line(
    lines: FakeVisitReportLineRepository,
    report_id: str,
    payload: dict,
) -> dict:
    return lines.create(
        {
            **payload,
            "sort_order": lines.next_sort_order(report_id),
        }
    )


def _draft_stack(
    *,
    contractor_email: str | None = "contractor@example.com",
) -> tuple[
    FieldVisitReportService,
    FakeVisitReportRepository,
    str,
    str,
    WorkspaceActivityService,
    RecordingDraftNotificationTool,
]:
    reports = FakeVisitReportRepository()
    lines = FakeVisitReportLineRepository()
    issues = InMemoryQualityIssueRepository()
    events = InMemoryQualityIssueEventRepository()
    projects = FakeProjectRepository(
        projects={
            "project-1": {
                "id": "project-1",
                "organization_id": "org-1",
                "project_name": "מגדלי הצפון",
                "contractor_name": "קבלן אלפא",
                "contractor_email": contractor_email,
            }
        }
    )
    workspace = WorkspaceActivityService()
    tool = RecordingDraftNotificationTool()
    materialization = QualityIssueMaterializationService(
        report_repository=reports,
        line_repository=lines,
        line_photo_repository=FakeVisitReportLinePhotoRepository(),
        issue_repository=issues,
        event_repository=events,
    )
    qc_service = QcNotificationService(
        notification_tool=tool,
        project_repository=projects,
        workspace_activity_service=workspace,
    )
    qc_service.critical_alert_service.issue_repository = issues

    visit_service = FieldVisitReportService(
        report_repository=reports,
        line_repository=lines,
        line_photo_repository=FakeVisitReportLinePhotoRepository(),
        project_repository=projects,
        materialization_service=materialization,
        qc_notification_service=qc_service,
    )

    report = reports.create(
        organization_id="org-1",
        project_id="project-1",
        status="IN_PROGRESS",
        visit_date="2026-06-18",
        header_fields={},
    )
    report_id = str(report["id"])
    line = _create_line(
        lines,
        report_id,
        {
            "organization_id": "org-1",
            "report_id": report_id,
            "issue_id": "SUP-FIN-004",
            "description": "פוגות",
            "trade": "ריצוף",
            "location": "דירה 5",
            "status": "NEEDS_ACTION",
        },
    )

    return (
        visit_service,
        reports,
        report_id,
        str(line["id"]),
        workspace,
        tool,
    )


def test_l3_service_and_api_wired() -> None:
    service = (
        REPO_ROOT / "app" / "services" / "qc_notification_service.py"
    ).read_text(encoding="utf-8")
    visit_service = (
        REPO_ROOT / "app" / "services" / "field_visit_report_service.py"
    ).read_text(encoding="utf-8")
    tool = (REPO_ROOT / "app" / "tools" / "notification_tool.py").read_text(
        encoding="utf-8"
    )
    main = _read_app_source()

    assert "notify_contractor_on_draft_issue" in service
    assert "build_draft_contractor_issue_messages" in tool
    assert "draft_notification" in visit_service
    assert "qc_notification_service" in main


def test_notify_contractor_on_draft_issue_creates_workspace_activity() -> None:
    visit_service, _, report_id, line_id, workspace, tool = _draft_stack()

    result = visit_service.materialize_draft_issue_from_line(
        organization_id="org-1",
        report_id=report_id,
        line_id=line_id,
        actor_id="user-1",
        checklist_item_id="checklist-1",
    )

    notification = result["draft_notification"]
    assert notification["workspace_activity_id"] is not None
    assert notification["email_status"] == "SENT"
    assert notification["contractor_email"] == "contractor@example.com"
    assert len(tool.sent) == 1
    assert tool.sent[0]["to"] == "contractor@example.com"

    feed = workspace.list_activities("project-1")
    assert feed["total"] == 1
    activity = feed["activities"][0]
    assert activity["activity_type"] == "DRAFT_DEFECT_RECORDED"
    assert activity["metadata"]["visibility"] == "DRAFT"
    assert activity["metadata"]["issue_id"] == result["issue"].id


def test_draft_notification_skips_email_without_contractor_email() -> None:
    visit_service, _, report_id, line_id, workspace, tool = _draft_stack(
        contractor_email=None,
    )

    result = visit_service.materialize_draft_issue_from_line(
        organization_id="org-1",
        report_id=report_id,
        line_id=line_id,
        actor_id="user-1",
    )

    notification = result["draft_notification"]
    assert notification["email_status"] == "SKIPPED"
    assert notification["contractor_email"] is None
    assert tool.sent == []
    assert workspace.list_activities("project-1")["total"] == 1


def test_draft_notification_not_sent_on_idempotent_replay() -> None:
    visit_service, _, report_id, line_id, workspace, tool = _draft_stack()

    first = visit_service.materialize_draft_issue_from_line(
        organization_id="org-1",
        report_id=report_id,
        line_id=line_id,
        actor_id="user-1",
    )
    second = visit_service.materialize_draft_issue_from_line(
        organization_id="org-1",
        report_id=report_id,
        line_id=line_id,
        actor_id="user-1",
    )

    assert "draft_notification" in first
    assert "draft_notification" not in second
    assert workspace.list_activities("project-1")["total"] == 1
    assert len(tool.sent) == 1


def test_notify_contractor_on_draft_issue_direct() -> None:
    issues = InMemoryQualityIssueRepository()
    projects = FakeProjectRepository()
    workspace = WorkspaceActivityService()
    tool = RecordingDraftNotificationTool()
    service = QcNotificationService(
        notification_tool=tool,
        project_repository=projects,
        workspace_activity_service=workspace,
    )
    service.critical_alert_service.issue_repository = issues
    created = issues.create(
        organization_id="org-1",
        project_id="proj-1",
        request=qc_create_request(
            title="נזילה",
            trade="אינסטלציה",
            location="דירה 2",
            visibility=IssueVisibility.DRAFT,
            first_seen_report_id="report-1",
            first_seen_line_id="line-1",
            materialization_key="report-1:line-1",
        ),
    )

    result = service.notify_contractor_on_draft_issue(
        organization_id="org-1",
        project_id="proj-1",
        report_id="report-1",
        issue_id=str(created["id"]),
        line_id="line-1",
        actor_id="user-1",
        send_email=False,
    )

    assert result.workspace_activity_id is not None
    assert result.email_status == "SKIPPED"
    assert workspace.list_activities("proj-1")["total"] == 1
