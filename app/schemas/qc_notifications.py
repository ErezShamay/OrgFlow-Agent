"""QC notification cycle response - roadmap 4.3.3."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.field_reports import OpenReportReminderResponse
from app.schemas.quality_issue import QualityCriticalStaleAlertResponse


class QcNotificationCycleResponse(BaseModel):
    """POST /portfolio/quality-alerts/run - unified QC notification cycle."""

    organization_id: str
    critical_stale: QualityCriticalStaleAlertResponse
    open_reports: OpenReportReminderResponse
    total_emails_sent: int = Field(ge=0)


class QcReportNotificationResponse(BaseModel):
    """Per-report QC alert evaluation triggered from Finalize (N01)."""

    organization_id: str
    report_id: str
    project_id: str
    alerts_evaluated: bool = True
    open_report_resolved: bool = False
    critical_new_issue_count: int = Field(default=0, ge=0)


class DraftIssueNotificationResponse(BaseModel):
    """Instant-loop L3 — internal activity + optional contractor heads-up on draft."""

    organization_id: str
    project_id: str
    report_id: str
    issue_id: str
    line_id: str
    workspace_activity_id: str | None = None
    contractor_email: str | None = None
    email_status: str = "SKIPPED"
