"""QC alerts - roadmap 4.3.1: CRITICAL open > 7 days → email via NotificationTool."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Protocol

from app.repositories.project_repository import ProjectRepository
from app.repositories.quality_issue_repository import (
    OPEN_ISSUE_STATUSES,
    QualityIssueRepository,
)
from app.schemas.quality_issue import (
    QualityCriticalStaleAlertDelivery,
    QualityCriticalStaleAlertResponse,
)
from app.services.quality_issue_portfolio_kpi import (
    days_open_for_issue,
    is_critical_open_over_days,
)
from app.tools.notification_tool import NotificationTool

CRITICAL_ALERT_DAYS_THRESHOLD = 7


class CriticalAlertDedupStore:
    """Skip duplicate alerts for the same issue on the same calendar day."""

    def __init__(self) -> None:
        self._last_alert_date_by_issue: dict[str, str] = {}

    def should_alert(self, issue_id: str, *, alert_date: str) -> bool:
        return self._last_alert_date_by_issue.get(issue_id) != alert_date

    def mark_alerted(self, issue_id: str, *, alert_date: str) -> None:
        self._last_alert_date_by_issue[issue_id] = alert_date


class NotificationSender(Protocol):
    def build_critical_stale_issue_messages(
        self,
        digests: list[dict[str, Any]],
    ) -> list[dict[str, Any]]: ...

    def send_reminders(
        self,
        reminders: list[dict[str, Any]],
    ) -> list[dict[str, Any]]: ...


def select_critical_stale_issues(
    open_issues: list[dict[str, Any]],
    *,
    threshold: int = CRITICAL_ALERT_DAYS_THRESHOLD,
    now: datetime,
) -> list[dict[str, Any]]:
    """Return open CRITICAL issues open longer than threshold days."""
    stale_issues = [
        issue
        for issue in open_issues
        if is_critical_open_over_days(issue, threshold=threshold, now=now)
    ]
    return sorted(
        stale_issues,
        key=lambda issue: (
            -int(days_open_for_issue(issue, now=now) or 0),
            str(issue.get("title") or "").casefold(),
        ),
    )


def build_supervisor_digests(
    stale_issues: list[dict[str, Any]],
    *,
    projects_by_id: dict[str, dict[str, Any]],
    now: datetime,
) -> list[dict[str, Any]]:
    """Group stale issues by supervisor email for one digest email each."""
    digests_by_email: dict[str, dict[str, Any]] = {}

    for issue in stale_issues:
        project_id = str(issue.get("project_id") or "")
        project = projects_by_id.get(project_id, {})
        supervisor_email = (project.get("supervisor_email") or "").strip()
        supervisor_name = (project.get("supervisor_name") or "מפקח").strip()
        project_name = (project.get("project_name") or project_id or "פרויקט").strip()
        days_open = days_open_for_issue(issue, now=now)

        digest_key = supervisor_email or f"missing-email:{project_id}"
        digest = digests_by_email.setdefault(
            digest_key,
            {
                "supervisor_email": supervisor_email or None,
                "supervisor_name": supervisor_name,
                "issues": [],
            },
        )
        digest["issues"].append(
            {
                "issue_id": str(issue.get("id") or ""),
                "project_id": project_id,
                "project_name": project_name,
                "title": str(issue.get("title") or "ליקוי"),
                "location": str(issue.get("location") or "").strip() or None,
                "trade": str(issue.get("trade") or "").strip() or None,
                "days_open": days_open,
            }
        )

    return list(digests_by_email.values())


class QualityIssueCriticalAlertService:
    def __init__(
        self,
        *,
        issue_repository: QualityIssueRepository | None = None,
        project_repository: ProjectRepository | None = None,
        notification_tool: NotificationSender | None = None,
        dedup_store: CriticalAlertDedupStore | None = None,
    ) -> None:
        self.issue_repository = issue_repository or QualityIssueRepository()
        self.project_repository = project_repository or ProjectRepository()
        self.notification_tool = notification_tool or NotificationTool()
        self.dedup_store = dedup_store or CriticalAlertDedupStore()

    def run_for_organization(
        self,
        *,
        organization_id: str,
        now: datetime | None = None,
        threshold: int = CRITICAL_ALERT_DAYS_THRESHOLD,
        send_email: bool = True,
    ) -> QualityCriticalStaleAlertResponse:
        current_time = now or datetime.now(UTC)
        alert_date = current_time.date().isoformat()

        issues = self.issue_repository.list_by_organization(
            organization_id=organization_id,
        )
        open_issues = [
            issue
            for issue in issues
            if issue.get("status") in OPEN_ISSUE_STATUSES
        ]
        stale_issues = select_critical_stale_issues(
            open_issues,
            threshold=threshold,
            now=current_time,
        )

        projects = self.project_repository.get_projects_by_organization(
            organization_id
        )
        projects_by_id = {
            str(project.get("id") or ""): project
            for project in projects
            if project.get("id")
        }

        issues_to_notify: list[dict[str, Any]] = []
        skipped_issue_ids: list[str] = []
        for issue in stale_issues:
            issue_id = str(issue.get("id") or "")
            if not issue_id:
                continue
            if self.dedup_store.should_alert(issue_id, alert_date=alert_date):
                issues_to_notify.append(issue)
            else:
                skipped_issue_ids.append(issue_id)

        digests = build_supervisor_digests(
            issues_to_notify,
            projects_by_id=projects_by_id,
            now=current_time,
        )
        reminders = self.notification_tool.build_critical_stale_issue_messages(
            digests
        )

        deliveries: list[QualityCriticalStaleAlertDelivery] = []
        if send_email and reminders:
            sent_results = self.notification_tool.send_reminders(reminders)
            for reminder, result in zip(reminders, sent_results, strict=False):
                issue_ids = [
                    str(item.get("issue_id") or "")
                    for item in reminder.get("issues", [])
                    if item.get("issue_id")
                ]
                for issue_id in issue_ids:
                    self.dedup_store.mark_alerted(
                        issue_id,
                        alert_date=alert_date,
                    )
                deliveries.append(
                    QualityCriticalStaleAlertDelivery(
                        to=result.get("to"),
                        status=str(result.get("status") or "UNKNOWN"),
                        issue_ids=issue_ids,
                        error=result.get("error"),
                    )
                )
        elif reminders:
            for reminder in reminders:
                issue_ids = [
                    str(item.get("issue_id") or "")
                    for item in reminder.get("issues", [])
                    if item.get("issue_id")
                ]
                deliveries.append(
                    QualityCriticalStaleAlertDelivery(
                        to=reminder.get("to"),
                        status="DRY_RUN",
                        issue_ids=issue_ids,
                    )
                )

        return QualityCriticalStaleAlertResponse(
            organization_id=organization_id,
            threshold_days=threshold,
            stale_issue_count=len(stale_issues),
            digest_count=len(digests),
            skipped_issue_ids=skipped_issue_ids,
            deliveries=deliveries,
        )
