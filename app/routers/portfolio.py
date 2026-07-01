"""Portfolio intelligence routes.

Extracted from app/main.py during the 2026-07 architecture-modularization
refactor. Shared service singletons live in app/dependencies.py; shared
request models live in app/schemas/api_requests.py.
"""
from __future__ import annotations

from app.auth import (
    get_auth_context,
    require_permission,
)
from app.config.settings import settings
from app.schemas.deliverable_reports import DeliverableReportsDashboardResponse
from app.schemas.field_reports import OpenReportReminderResponse
from app.schemas.qc_notifications import QcNotificationCycleResponse
from app.schemas.quality_issue import (
    QualityCriticalStaleAlertResponse,
    QualityPeriodicReportResponse,
    QualityPortfolioLiveSnapshot,
    QualityPortfolioSummaryResponse,
    QualityRecurringRankingsResponse,
    QualityTradeHeatmapResponse,
)
from datetime import (
    date,
    timedelta,
)
from fastapi import (
    Depends,
    HTTPException,
)
from fastapi.responses import (
    Response,
    StreamingResponse,
)

from fastapi import APIRouter
import app.dependencies as deps


router = APIRouter()


@router.get("/portfolio/summary")
def get_portfolio_summary(
    auth=Depends(require_permission("projects:read")),
):
    return deps.portfolio_intelligence_dashboard_service.get_summary(
        organization_id=auth.org_id,
    )


@router.get(
    "/portfolio/quality-summary",
    response_model=QualityPortfolioSummaryResponse,
)
def get_portfolio_quality_summary(
    auth=Depends(get_auth_context),
):
    return deps.quality_issue_service.get_portfolio_quality_summary(
        organization_id=auth.org_id,
        actor_role=auth.role,
        actor_user_id=auth.actor_user_id,
    )


@router.get(
    "/portfolio/live-snapshot",
    response_model=QualityPortfolioLiveSnapshot,
)
def get_portfolio_live_snapshot(
    auth=Depends(get_auth_context),
):
    """R1 — lightweight open-issue counters for 30s polling."""
    return deps.quality_issue_service.get_portfolio_live_snapshot(
        organization_id=auth.org_id,
        actor_role=auth.role,
        actor_user_id=auth.actor_user_id,
    )


@router.get("/portfolio/events")
async def stream_portfolio_events(
    auth=Depends(get_auth_context),
):
    """R1 — SSE stream of portfolio open-issue counters (30s interval)."""

    async def event_generator():
        async for chunk in deps.portfolio_live_service.stream_events(
            organization_id=auth.org_id,
            actor_role=auth.role,
            actor_user_id=auth.actor_user_id,
        ):
            yield chunk

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get(
    "/portfolio/quality-trade-heatmap",
    response_model=QualityTradeHeatmapResponse,
)
def get_portfolio_quality_trade_heatmap(
    auth=Depends(get_auth_context),
    project_id: str | None = None,
):
    """Roadmap 6.1 - open issues heatmap grouped by trade."""
    return deps.quality_issue_service.get_portfolio_trade_heatmap(
        organization_id=auth.org_id,
        actor_role=auth.role,
        project_id=project_id,
        actor_user_id=auth.actor_user_id,
    )


@router.get(
    "/portfolio/quality-recurring-rankings",
    response_model=QualityRecurringRankingsResponse,
)
def get_portfolio_quality_recurring_rankings(
    auth=Depends(get_auth_context),
    project_id: str | None = None,
):
    """Roadmap 6.2 - recurring issues and subcontractor pressure rankings."""
    return deps.quality_issue_service.get_portfolio_recurring_rankings(
        organization_id=auth.org_id,
        actor_role=auth.role,
        project_id=project_id,
        actor_user_id=auth.actor_user_id,
    )


@router.get(
    "/portfolio/quality-periodic-report",
    response_model=QualityPeriodicReportResponse,
)
def get_portfolio_quality_periodic_report(
    auth=Depends(get_auth_context),
    period_days: int = 30,
    project_id: str | None = None,
):
    """Roadmap 6.3 - periodic QC report for developers."""
    return deps.quality_issue_service.get_portfolio_periodic_report(
        organization_id=auth.org_id,
        actor_role=auth.role,
        period_days=period_days,
        project_id=project_id,
        actor_user_id=auth.actor_user_id,
    )


@router.get(
    "/portfolio/deliverable-reports",
    response_model=DeliverableReportsDashboardResponse,
)
def get_portfolio_deliverable_reports(
    auth=Depends(get_auth_context),
    start_date: date | None = None,
    end_date: date | None = None,
    project_id: str | None = None,
):
    """Deliverable reports sent in a date range with weekly compliance."""
    today = date.today()
    resolved_end = end_date or today
    resolved_start = start_date or (resolved_end - timedelta(days=89))

    return deps.deliverable_reports_service.get_dashboard(
        organization_id=auth.org_id,
        actor_role=auth.role,
        period_start=resolved_start,
        period_end=resolved_end,
        project_id=project_id,
        actor_user_id=auth.actor_user_id,
    )


@router.get("/portfolio/quality-periodic-report/export")
def export_portfolio_quality_periodic_report(
    auth=Depends(get_auth_context),
    period_days: int = 30,
    project_id: str | None = None,
    format: str = "csv",
):
    """Roadmap 6.3 - CSV export for periodic QC report."""
    if format.lower() != "csv":
        raise HTTPException(
            status_code=400,
            detail={"message": "Only csv export is supported"},
        )

    csv_content = deps.quality_issue_service.export_portfolio_periodic_report_csv(
        organization_id=auth.org_id,
        actor_role=auth.role,
        period_days=period_days,
        project_id=project_id,
        actor_user_id=auth.actor_user_id,
    )
    return Response(
        content=csv_content.encode("utf-8"),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": (
                'attachment; filename="qc-periodic-report.csv"'
            ),
        },
    )


@router.post(
    "/portfolio/quality-alerts/critical-stale",
    response_model=QualityCriticalStaleAlertResponse,
)
def send_critical_stale_quality_alerts(
    auth=Depends(require_permission("quality_issues:write")),
):
    """Roadmap 4.3.1 - email supervisors for CRITICAL issues open > 7 days."""
    send_email = settings.FEATURE_FLAGS.enable_email_delivery
    return deps.qc_notification_service.run_critical_stale_for_organization(
        organization_id=auth.org_id,
        send_email=send_email,
    )


@router.post(
    "/portfolio/quality-alerts/open-reports",
    response_model=OpenReportReminderResponse,
)
def send_open_report_reminders(
    auth=Depends(require_permission("quality_issues:write")),
):
    """Roadmap 4.3.2 - email supervisors for IN_PROGRESS reports open > 3 days."""
    send_email = settings.FEATURE_FLAGS.enable_email_delivery
    return deps.qc_notification_service.run_open_reports_for_organization(
        organization_id=auth.org_id,
        send_email=send_email,
    )


@router.post(
    "/portfolio/quality-alerts/run",
    response_model=QcNotificationCycleResponse,
)
def run_qc_notification_alerts(
    auth=Depends(require_permission("quality_issues:write")),
):
    """Roadmap 4.3.3 - run all QC alerts via NotificationTool (not automation)."""
    send_email = settings.FEATURE_FLAGS.enable_email_delivery
    return deps.qc_notification_service.run_for_organization(
        organization_id=auth.org_id,
        send_email=send_email,
    )


@router.get("/portfolio/dashboard")
def get_portfolio_intelligence_dashboard(
    organization_id: str | None = None,
):
    return deps.portfolio_intelligence_dashboard_service.get_dashboard(
        organization_id=organization_id,
    )


@router.get("/portfolio/trends")
def get_portfolio_trends():
    return deps.portfolio_intelligence_dashboard_service.get_trends()


@router.get("/portfolio/predictive-risk")
def get_portfolio_predictive_risk():
    return deps.portfolio_intelligence_dashboard_service.get_predictive_risk()


@router.get("/portfolio/executive-kpis")
def get_portfolio_executive_kpis():
    return deps.portfolio_intelligence_dashboard_service.get_executive_kpis()


@router.get("/portfolio/forecast")
def get_portfolio_forecast(horizon_days: int = 30):
    return deps.portfolio_intelligence_dashboard_service.get_forecast(
        horizon_days=horizon_days,
    )


@router.get("/portfolio/heatmap")
def get_portfolio_heatmap():
    return deps.portfolio_intelligence_dashboard_service.get_heatmap()


@router.get("/portfolio/benchmarks")
def get_portfolio_benchmarks(organization_id: str | None = None):
    return deps.portfolio_intelligence_dashboard_service.get_benchmarks(
        organization_id=organization_id,
    )


@router.get("/portfolio/recommendations")
def get_portfolio_recommendations():
    return deps.portfolio_intelligence_dashboard_service.get_recommendations()


@router.get("/portfolio/analytics")
def get_portfolio_analytics():
    return deps.portfolio_intelligence_dashboard_service.get_analytics()


@router.get("/portfolio/metrics")
def get_portfolio_metrics():
    return deps.portfolio_intelligence_dashboard_service.get_metrics()


@router.get("/portfolio/risk-scores")
def get_portfolio_risk_scores():
    return deps.portfolio_intelligence_dashboard_service.get_risk_scores()


@router.get("/portfolio/predictive-alerts")
def get_portfolio_predictive_alerts():
    return deps.portfolio_intelligence_dashboard_service.get_predictive_alerts()


@router.get("/portfolio/executive-summary")
def get_portfolio_executive_summary():
    return deps.portfolio_intelligence_dashboard_service.get_executive_summary()


@router.get("/portfolio/cross-organization")
def get_portfolio_cross_organization_insights():
    return (
        deps.portfolio_intelligence_dashboard_service
        .get_cross_organization_insights()
    )


