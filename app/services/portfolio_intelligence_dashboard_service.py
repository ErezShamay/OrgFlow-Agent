from app.repositories.organization_repository import (
    OrganizationRepository,
)
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
from app.services.portfolio_trend_analysis_service import (
    PortfolioTrendAnalysisService,
)
from app.services.predictive_alerts_service import PredictiveAlertsService
from app.services.predictive_risk_service import PredictiveRiskService


class PortfolioIntelligenceDashboardService:
    def __init__(
        self,
        portfolio_insights_service: PortfolioInsightsService | None = None,
        trend_service: PortfolioTrendAnalysisService | None = None,
        executive_kpi_service: ExecutiveKpiService | None = None,
        forecasting_service: PortfolioForecastingService | None = None,
        heatmap_service: PortfolioHeatmapService | None = None,
        benchmarking_service: OrganizationBenchmarkingService | None = None,
        recommendations_service: AIExecutiveRecommendationsService | None = None,
        analytics_service: PortfolioAnalyticsService | None = None,
        risk_scoring_service: MultiProjectRiskScoringService | None = None,
        predictive_alerts_service: PredictiveAlertsService | None = None,
        executive_summary_service: ExecutiveSummaryService | None = None,
        cross_org_service: CrossOrganizationInsightsService | None = None,
        organization_repository: OrganizationRepository | None = None,
    ):
        self.portfolio_insights_service = (
            portfolio_insights_service or PortfolioInsightsService()
        )
        self.trend_service = trend_service or PortfolioTrendAnalysisService()
        self.executive_kpi_service = executive_kpi_service or ExecutiveKpiService()
        self.forecasting_service = (
            forecasting_service or PortfolioForecastingService()
        )
        self.heatmap_service = heatmap_service or PortfolioHeatmapService()
        self.benchmarking_service = (
            benchmarking_service or OrganizationBenchmarkingService()
        )
        self.recommendations_service = (
            recommendations_service or AIExecutiveRecommendationsService()
        )
        self.analytics_service = analytics_service or PortfolioAnalyticsService()
        self.risk_scoring_service = (
            risk_scoring_service or MultiProjectRiskScoringService()
        )
        self.predictive_alerts_service = (
            predictive_alerts_service or PredictiveAlertsService()
        )
        self.executive_summary_service = (
            executive_summary_service or ExecutiveSummaryService()
        )
        self.cross_org_service = (
            cross_org_service or CrossOrganizationInsightsService()
        )
        self.organization_repository = (
            organization_repository or OrganizationRepository()
        )

    def _build_context(self, organization_id: str | None = None) -> dict:
        portfolio_summary = (
            self.portfolio_insights_service
            .generate_portfolio_summary()
        )
        if organization_id:
            portfolio_summary["organization_id"] = organization_id

        trend_analysis = self.trend_service.analyze(portfolio_summary)
        executive_kpis = self.executive_kpi_service.get_kpis(portfolio_summary)
        risk_analysis = PredictiveRiskService.analyze_portfolio(portfolio_summary)
        risk_scores = self.risk_scoring_service.score_portfolio(portfolio_summary)
        predictive_alerts = self.predictive_alerts_service.generate(
            portfolio_summary
        )
        executive_summary = self.executive_summary_service.generate(
            portfolio_summary=portfolio_summary,
            executive_kpis=executive_kpis,
            trend_analysis=trend_analysis,
            risk_analysis=risk_analysis,
            predictive_alerts=predictive_alerts,
        )
        recommendations = self.recommendations_service.generate_recommendations(
            portfolio_summary=portfolio_summary,
            trend_analysis=trend_analysis,
            risk_analysis=risk_analysis,
            executive_kpis=executive_kpis,
        )

        return {
            "portfolio_summary": portfolio_summary,
            "trend_analysis": trend_analysis,
            "executive_kpis": executive_kpis,
            "risk_analysis": risk_analysis,
            "risk_scores": risk_scores,
            "predictive_alerts": predictive_alerts,
            "executive_summary": executive_summary,
            "recommendations": recommendations,
            "forecast": self.forecasting_service.forecast(portfolio_summary),
            "heatmap": self.heatmap_service.build_heatmap(portfolio_summary),
            "benchmarks": self.benchmarking_service.benchmark(
                portfolio_summary,
                executive_kpis,
            ),
            "analytics": self.analytics_service.get_analytics(portfolio_summary),
            "metrics": self.analytics_service.get_metrics(portfolio_summary),
        }

    def get_dashboard(self, organization_id: str | None = None) -> dict:
        context = self._build_context(organization_id=organization_id)
        organizations = self.organization_repository.get_all_organizations()
        cross_org = self.cross_org_service.get_insights(organizations)

        return {
            "summary": context["portfolio_summary"],
            "trends": context["trend_analysis"],
            "executive_kpis": context["executive_kpis"],
            "predictive_risk": context["risk_analysis"],
            "forecast": context["forecast"],
            "heatmap": context["heatmap"],
            "benchmarks": context["benchmarks"],
            "recommendations": context["recommendations"],
            "analytics": context["analytics"],
            "metrics": context["metrics"],
            "risk_scores": context["risk_scores"],
            "predictive_alerts": context["predictive_alerts"],
            "executive_summary": context["executive_summary"],
            "cross_organization": cross_org,
        }

    def get_summary(self) -> dict:
        return self.portfolio_insights_service.generate_portfolio_summary()

    def get_trends(self) -> dict:
        summary = self.get_summary()
        return self.trend_service.analyze(summary)

    def get_predictive_risk(self) -> dict:
        summary = self.get_summary()
        return PredictiveRiskService.analyze_portfolio(summary)

    def get_executive_kpis(self) -> dict:
        summary = self.get_summary()
        return self.executive_kpi_service.get_kpis(summary)

    def get_forecast(self, horizon_days: int = 30) -> dict:
        summary = self.get_summary()
        return self.forecasting_service.forecast(summary, horizon_days=horizon_days)

    def get_heatmap(self) -> dict:
        summary = self.get_summary()
        return self.heatmap_service.build_heatmap(summary)

    def get_benchmarks(self, organization_id: str | None = None) -> dict:
        summary = self.get_summary()
        if organization_id:
            summary["organization_id"] = organization_id
        kpis = self.executive_kpi_service.get_kpis(summary)
        return self.benchmarking_service.benchmark(summary, kpis)

    def get_recommendations(self) -> dict:
        context = self._build_context()
        return context["recommendations"]

    def get_analytics(self) -> dict:
        summary = self.get_summary()
        return self.analytics_service.get_analytics(summary)

    def get_metrics(self) -> dict:
        summary = self.get_summary()
        return self.analytics_service.get_metrics(summary)

    def get_risk_scores(self) -> dict:
        summary = self.get_summary()
        return self.risk_scoring_service.score_portfolio(summary)

    def get_predictive_alerts(self) -> dict:
        summary = self.get_summary()
        return self.predictive_alerts_service.generate(summary)

    def get_executive_summary(self) -> dict:
        context = self._build_context()
        return context["executive_summary"]

    def get_cross_organization_insights(self) -> dict:
        organizations = self.organization_repository.get_all_organizations()
        return self.cross_org_service.get_insights(organizations)
