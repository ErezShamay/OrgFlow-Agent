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
