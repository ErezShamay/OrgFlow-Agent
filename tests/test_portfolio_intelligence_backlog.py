from fastapi.testclient import TestClient

import app.main as main_module
from app.auth.jwt_service import JWTService
from app.main import app
from app.services.ai_executive_recommendations_service import (
    AIExecutiveRecommendationsService,
)
from app.services.cross_organization_insights_service import (
    CrossOrganizationInsightsService,
)
from app.services.executive_kpi_service import ExecutiveKpiService
from app.services.executive_summary_service import ExecutiveSummaryService
from app.services.multi_project_risk_scoring_service import (
    MultiProjectRiskScoringService,
)
from app.services.organization_benchmarking_service import (
    OrganizationBenchmarkingService,
)
from app.services.portfolio_analytics_service import PortfolioAnalyticsService
from app.services.portfolio_forecasting_service import (
    PortfolioForecastingService,
)
from app.services.portfolio_heatmap_service import PortfolioHeatmapService
from app.services.portfolio_insights_service import PortfolioInsightsService
from app.services.portfolio_intelligence_dashboard_service import (
    PortfolioIntelligenceDashboardService,
)
from app.services.portfolio_trend_analysis_service import (
    PortfolioTrendAnalysisService,
)
from app.services.predictive_alerts_service import PredictiveAlertsService
from app.services.predictive_risk_service import PredictiveRiskService
import app.dependencies as deps


def sample_portfolio_summary():
    return {
        "projects": [
            {
                "project_id": "p1",
                "project_name": "Alpha",
                "health": {"score": 35, "status": "CRITICAL"},
                "summary": {
                    "actions_count": 6,
                    "escalations_count": 3,
                    "reviews_count": 1,
                },
                "prediction": {
                    "prediction": "HIGH_RISK",
                    "risk_score": 82,
                    "message": "high risk",
                },
            },
            {
                "project_id": "p2",
                "project_name": "Beta",
                "health": {"score": 88, "status": "HEALTHY"},
                "summary": {
                    "actions_count": 2,
                    "escalations_count": 0,
                    "reviews_count": 0,
                },
                "prediction": {
                    "prediction": "LOW_RISK",
                    "risk_score": 18,
                    "message": "stable",
                },
            },
        ],
        "critical_projects": 1,
        "total_projects": 2,
        "total_actions": 8,
        "total_escalations": 3,
        "average_health_score": 61,
    }


class FakeProjectRepository:
    def get_all_projects(self):
        return [
            {"id": "p1", "project_name": "Alpha", "organization_id": "org-1"},
            {"id": "p2", "project_name": "Beta", "organization_id": "org-1"},
        ]

    def get_projects_by_organization(self, organization_id: str):
        return [
            project
            for project in self.get_all_projects()
            if project.get("organization_id") == organization_id
        ]


class FakeWorkspaceService:
    def get_workspace(self, project_id: str):
        if project_id == "p1":
            return {
                "health": {"score": 35, "status": "CRITICAL"},
                "summary": {
                    "actions_count": 6,
                    "escalations_count": 3,
                    "reviews_count": 1,
                },
            }
        return {
            "health": {"score": 88, "status": "HEALTHY"},
            "summary": {
                "actions_count": 2,
                "escalations_count": 0,
                "reviews_count": 0,
            },
        }


class FakeOrganizationRepository:
    def get_all_organizations(self):
        return [
            {
                "id": "org-1",
                "name": "Org One",
                "projects": [
                    {"id": "p1", "health_score": 40},
                    {"id": "p2", "health_score": 90},
                ],
            },
            {
                "id": "org-2",
                "name": "Org Two",
                "projects": [
                    {"id": "p3", "health_score": 55},
                ],
            },
        ]


def build_dashboard():
    portfolio_service = PortfolioInsightsService(
        project_repository=FakeProjectRepository(),
        workspace_service=FakeWorkspaceService(),
    )
    return PortfolioIntelligenceDashboardService(
        portfolio_insights_service=portfolio_service,
        organization_repository=FakeOrganizationRepository(),
    )


def test_trend_analysis_detects_declining_dominant_trend():
    service = PortfolioTrendAnalysisService()
    result = service.analyze(sample_portfolio_summary())

    assert result["dominant_trend"] == "DECLINING"
    assert result["summary"]["declining"] == 1
    assert result["summary"]["improving"] == 1


def test_predictive_risk_analysis_portfolio_distribution():
    result = PredictiveRiskService.analyze_portfolio(
        sample_portfolio_summary()
    )

    assert result["portfolio_risk_level"] == "MEDIUM"
    assert result["distribution"]["HIGH_RISK"] == 1
    assert len(result["high_risk_projects"]) == 1


def test_executive_kpis_include_exposure_indexes():
    service = ExecutiveKpiService()
    kpis = service.get_kpis(sample_portfolio_summary())

    assert kpis["portfolio_health_index"] == 61
    assert kpis["critical_project_ratio"] == 0.5
    assert kpis["operational_load_index"] == 8


def test_portfolio_forecasting_returns_outlook():
    service = PortfolioForecastingService()
    forecast = service.forecast(sample_portfolio_summary(), horizon_days=30)

    assert forecast["horizon_days"] == 30
    assert forecast["outlook"] in {"STABLE", "WATCH", "AT_RISK"}
    assert "projected" in forecast


def test_portfolio_heatmap_builds_risk_health_grid():
    service = PortfolioHeatmapService()
    heatmap = service.build_heatmap(sample_portfolio_summary())

    assert len(heatmap["cells"]) == 9
    assert heatmap["hottest_cell"]["project_count"] >= 1


def test_organization_benchmarking_compares_to_industry():
    kpis = ExecutiveKpiService().get_kpis(sample_portfolio_summary())
    result = OrganizationBenchmarkingService().benchmark(
        sample_portfolio_summary(),
        kpis,
    )

    assert result["performance_tier"] in {
        "LEADER",
        "COMPETITIVE",
        "DEVELOPING",
        "LAGGING",
    }
    assert len(result["comparisons"]) == 5


def test_ai_executive_recommendations_for_high_risk_portfolio():
    summary = sample_portfolio_summary()
    trends = PortfolioTrendAnalysisService().analyze(summary)
    risk = PredictiveRiskService.analyze_portfolio(summary)
    kpis = ExecutiveKpiService().get_kpis(summary)

    result = AIExecutiveRecommendationsService().generate_recommendations(
        portfolio_summary=summary,
        trend_analysis=trends,
        risk_analysis=risk,
        executive_kpis=kpis,
    )

    assert result["recommendation_count"] >= 2
    assert result["top_priority"] in {"HIGH", "CRITICAL", "MEDIUM", "LOW"}


def test_portfolio_analytics_and_metrics():
    analytics = PortfolioAnalyticsService().get_analytics(
        sample_portfolio_summary()
    )
    metrics = PortfolioAnalyticsService().get_metrics(
        sample_portfolio_summary()
    )

    assert analytics["by_health_status"]["CRITICAL"] == 1
    assert metrics["high_risk_projects"] == 1
    assert metrics["critical_rate"] == 0.5


def test_multi_project_risk_scoring_ranks_projects():
    result = MultiProjectRiskScoringService().score_portfolio(
        sample_portfolio_summary()
    )

    assert result["portfolio_risk_level"] == "MEDIUM"
    assert result["top_risk_projects"][0]["project_id"] == "p1"


def test_predictive_alerts_include_forecast_and_risk_sources():
    summary = sample_portfolio_summary()
    alerts = PredictiveAlertsService().generate(summary)

    assert alerts["total_alerts"] >= 1
    sources = {alert.get("source") for alert in alerts["alerts"]}
    assert None in sources or "PREDICTIVE_RISK" in sources


def test_executive_summary_generates_brief():
    summary = sample_portfolio_summary()
    trends = PortfolioTrendAnalysisService().analyze(summary)
    risk = PredictiveRiskService.analyze_portfolio(summary)
    kpis = ExecutiveKpiService().get_kpis(summary)
    alerts = PredictiveAlertsService().generate(summary)

    result = ExecutiveSummaryService().generate(
        portfolio_summary=summary,
        executive_kpis=kpis,
        trend_analysis=trends,
        risk_analysis=risk,
        predictive_alerts=alerts,
    )

    assert "headline" in result
    assert result["recommended_focus"] in {
        "IMMEDIATE_INTERVENTION",
        "ENHANCED_MONITORING",
        "MAINTAIN_STABILITY",
    }


def test_cross_organization_insights_aggregate_orgs():
    organizations = FakeOrganizationRepository().get_all_organizations()
    result = CrossOrganizationInsightsService().get_insights(organizations)

    assert result["organization_count"] == 2
    assert result["total_projects"] == 3
    assert len(result["top_performers"]) <= 3


def test_portfolio_intelligence_dashboard_aggregates_all_domains():
    dashboard = build_dashboard().get_dashboard(organization_id="org-1")

    assert dashboard["summary"]["total_projects"] == 2
    assert "trends" in dashboard
    assert "executive_kpis" in dashboard
    assert "predictive_risk" in dashboard
    assert "forecast" in dashboard
    assert "heatmap" in dashboard
    assert "benchmarks" in dashboard
    assert "recommendations" in dashboard
    assert "analytics" in dashboard
    assert "risk_scores" in dashboard
    assert "predictive_alerts" in dashboard
    assert "executive_summary" in dashboard
    assert dashboard["cross_organization"]["organization_count"] == 2


def _auth_headers():
    token = JWTService().issue_access_token(
        user_id="user-1",
        org_id="org-1",
        role="ADMIN",
        token_id="portfolio-intelligence-tests",
    )
    return {"Authorization": f"Bearer {token}", "X-Organization-ID": "org-1"}


def test_portfolio_intelligence_api_endpoints(monkeypatch):
    dashboard = build_dashboard()
    monkeypatch.setattr(
        deps,
        "portfolio_intelligence_dashboard_service",
        dashboard,
    )
    monkeypatch.setattr(
        deps,
        "portfolio_insights_service",
        dashboard.portfolio_insights_service,
    )

    client = TestClient(app)
    headers = _auth_headers()

    endpoints = [
        "/portfolio/summary",
        "/portfolio/dashboard",
        "/portfolio/trends",
        "/portfolio/predictive-risk",
        "/portfolio/executive-kpis",
        "/portfolio/forecast",
        "/portfolio/heatmap",
        "/portfolio/benchmarks",
        "/portfolio/recommendations",
        "/portfolio/analytics",
        "/portfolio/metrics",
        "/portfolio/risk-scores",
        "/portfolio/predictive-alerts",
        "/portfolio/executive-summary",
        "/portfolio/cross-organization",
    ]

    for path in endpoints:
        response = client.get(path, headers=headers)
        assert response.status_code == 200, path

    summary = client.get("/portfolio/summary", headers=headers).json()
    assert summary["total_projects"] == 2

    dashboard_response = client.get(
        "/portfolio/dashboard",
        headers=headers,
    ).json()
    assert dashboard_response["executive_summary"]["headline"]
