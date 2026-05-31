from fastapi.testclient import TestClient

import app.main as main_module
from app.auth.jwt_service import JWTService
from app.main import app
from app.services.admin_panel_service import AdminPanelService
from app.services.api_documentation_service import ApiDocumentationService
from app.services.beta_testing_flow_service import BetaTestingFlowService
from app.services.billing_integration_service import BillingIntegrationService
from app.services.customer_onboarding_flow_service import CustomerOnboardingFlowService
from app.services.demo_data_generator_service import DemoDataGeneratorService
from app.services.demo_environment_service import DemoEnvironmentService
from app.services.documentation_service import DocumentationService
from app.services.internal_developer_docs_service import InternalDeveloperDocsService
from app.services.investor_demo_deck_service import InvestorDemoDeckService
from app.services.marketing_assets_service import MarketingAssetsService
from app.services.multi_tenant_readiness_service import MultiTenantReadinessService
from app.services.onboarding_flow_service import OnboardingFlowService
from app.services.pricing_model_service import PricingModelService
from app.services.product_analytics_service import ProductAnalyticsService
from app.services.product_demo_service import ProductDemoService
from app.services.product_readiness_dashboard_service import (
    ProductReadinessDashboardService,
)
from app.services.product_website_service import ProductWebsiteService
from app.services.saas_readiness_service import SaasReadinessService
from app.services.subscription_plans_service import SubscriptionPlansService
from app.services.support_tooling_service import SupportToolingService
from app.services.usage_quotas_service import UsageQuotasService
from app.services.usage_tracking_service import UsageTrackingService


def build_dashboard():
    return ProductReadinessDashboardService()


def test_onboarding_flow():
    service = OnboardingFlowService()
    config = service.get_config()
    assert config["flow_id"] == "orgflow_signup_v1"

    progress = service.evaluate_progress(
        completed_steps=["welcome", "organization", "first_project"],
    )
    assert progress["complete"] is True

    steps = service.list_steps()
    assert steps["total"] >= 4
    assert service.validate_setup()["valid"] is True


def test_demo_data_generator():
    service = DemoDataGeneratorService()
    config = service.get_config()
    assert config["idempotent"] is True

    result = service.simulate_generation(preset_id="startup")
    assert result["generated"] is True
    assert result["projects_created"] == 3

    presets = service.list_presets()
    assert presets["total"] >= 3
    assert service.validate_setup()["valid"] is True


def test_multi_tenant_readiness():
    service = MultiTenantReadinessService()
    config = service.get_config()
    assert config["isolation_model"] == "organization_scoped_rls"

    readiness = service.evaluate_readiness(
        passed_item_ids=["rls_policies", "tenant_header", "jwt_org_claim", "storage_prefix"],
    )
    assert readiness["ready"] is True

    checklist = service.list_checklist()
    assert checklist["total"] >= 4
    assert service.validate_setup()["valid"] is True


def test_pricing_model():
    service = PricingModelService()
    config = service.get_config()
    assert config["currency"] == "USD"

    estimate = service.calculate_estimate(tier_id="starter", seats=5)
    assert estimate["estimated"] is True
    assert estimate["monthly_total"] == 145

    tiers = service.list_tiers()
    assert tiers["total"] >= 3
    assert service.validate_setup()["valid"] is True


def test_admin_panel():
    service = AdminPanelService()
    config = service.get_config()
    assert config["required_role"] == "ADMIN"

    access = service.check_access(role="ADMIN")
    assert access["allowed"] is True

    denied = service.check_access(role="VIEWER")
    assert denied["allowed"] is False

    modules = service.list_modules()
    assert modules["total"] >= 4
    assert service.validate_setup()["valid"] is True


def test_product_analytics():
    service = ProductAnalyticsService()
    config = service.get_config()
    assert config["provider"] == "posthog"

    tracking = service.evaluate_tracking(
        events_implemented=[
            "project_created",
            "report_uploaded",
            "ai_review_completed",
            "action_completed",
            "subscription_upgraded",
        ],
    )
    assert tracking["ready"] is True

    events = service.list_events()
    assert events["total"] >= 4
    assert service.validate_setup()["valid"] is True


def test_usage_quotas():
    service = UsageQuotasService()
    config = service.get_config()
    assert config["enforcement"] == "soft_then_hard"

    allowed = service.check_usage(metric="ai_tokens", plan="starter", current_usage=1000)
    assert allowed["allowed"] is True

    blocked = service.check_usage(metric="ai_tokens", plan="starter", current_usage=60_000)
    assert blocked["allowed"] is False

    quotas = service.list_quotas()
    assert quotas["total"] >= 3
    assert service.validate_setup()["valid"] is True


def test_billing_integration():
    service = BillingIntegrationService()
    config = service.get_config()
    assert config["provider"] == "stripe"

    webhook = service.simulate_webhook(event_type="invoice.paid")
    assert webhook["processed"] is True

    products = service.list_products()
    assert products["total"] >= 3
    assert service.validate_setup()["valid"] is True


def test_subscription_plans():
    service = SubscriptionPlansService()
    config = service.get_config()
    assert config["trial_days"] == 14

    upgrade = service.evaluate_upgrade(from_plan="starter", to_plan="growth")
    assert upgrade["allowed"] is True

    downgrade = service.evaluate_upgrade(from_plan="growth", to_plan="starter")
    assert downgrade["allowed"] is False

    plans = service.list_plans()
    assert plans["total"] >= 3
    assert service.validate_setup()["valid"] is True


def test_support_tooling():
    service = SupportToolingService()
    config = service.get_config()
    assert config["provider"] == "intercom"

    sla = service.evaluate_sla(plan="enterprise", hours_open=2.0)
    assert sla["within_sla"] is True

    channels = service.list_channels()
    assert channels["total"] >= 2
    assert service.validate_setup()["valid"] is True


def test_documentation():
    service = DocumentationService()
    config = service.get_config()
    assert config["format"] == "mdx"

    coverage = service.evaluate_coverage(
        published_sections=["getting_started", "projects", "reports", "billing"],
    )
    assert coverage["launch_ready"] is True

    sections = service.list_sections()
    assert sections["total"] >= 4
    assert service.validate_setup()["valid"] is True


def test_api_documentation():
    service = ApiDocumentationService()
    config = service.get_config()
    assert config["spec_format"] == "openapi_3.1"

    completeness = service.evaluate_completeness(
        documented_tags=["projects", "reports", "auth", "portfolio", "product-readiness"],
    )
    assert completeness["complete"] is True

    groups = service.list_documented_groups()
    assert groups["total"] >= 4
    assert service.validate_setup()["valid"] is True


def test_internal_developer_docs():
    service = InternalDeveloperDocsService()
    config = service.get_config()
    assert config["includes_runbooks"] is True

    pack = service.evaluate_onboarding_pack(
        available_guides=["local_setup", "database_migrations", "deployment"],
    )
    assert pack["complete"] is True

    guides = service.list_guides()
    assert guides["total"] >= 4
    assert service.validate_setup()["valid"] is True


def test_product_website():
    service = ProductWebsiteService()
    config = service.get_config()
    assert config["framework"] == "nextjs"

    launch = service.evaluate_launch(published_slugs=["/", "/pricing", "/features"])
    assert launch["launch_ready"] is True

    pages = service.list_pages()
    assert pages["total"] >= 4
    assert service.validate_setup()["valid"] is True


def test_marketing_assets():
    service = MarketingAssetsService()
    config = service.get_config()
    assert config["brand_kit_version"] == "2026.1"

    asset = service.check_asset(asset_id="logo_primary")
    assert asset["exists"] is True

    assets = service.list_assets()
    assert assets["total"] >= 4
    assert service.validate_setup()["valid"] is True


def test_investor_demo_deck():
    service = InvestorDemoDeckService()
    config = service.get_config()
    assert config["deck_id"] == "orgflow_investor_v1"

    readiness = service.evaluate_readiness(completed_slides=[1, 2, 3, 4, 6, 8])
    assert readiness["demo_ready"] is True

    slides = service.list_slides()
    assert slides["total"] >= 6
    assert service.validate_setup()["valid"] is True


def test_demo_environment():
    service = DemoEnvironmentService()
    config = service.get_config()
    assert config["environment"] == "demo"

    health = service.evaluate_health(api_up=True, ui_up=True, data_seeded=True)
    assert health["healthy"] is True

    features = service.list_features()
    assert features["total"] >= 3
    assert service.validate_setup()["valid"] is True


def test_beta_testing_flow():
    service = BetaTestingFlowService()
    config = service.get_config()
    assert config["invite_only"] is True

    enrollment = service.evaluate_enrollment(current_participants=50, approved=True)
    assert enrollment["can_enroll"] is True

    full = service.evaluate_enrollment(current_participants=100, approved=True)
    assert full["can_enroll"] is False

    stages = service.list_stages()
    assert stages["total"] >= 4
    assert service.validate_setup()["valid"] is True


def test_customer_onboarding_flow():
    service = CustomerOnboardingFlowService()
    config = service.get_config()
    assert config["sla_days"] == 30

    progress = service.evaluate_progress(
        completed_milestones=["kickoff", "training", "go_live"],
    )
    assert progress["on_track"] is True

    milestones = service.list_milestones()
    assert milestones["total"] >= 4
    assert service.validate_setup()["valid"] is True


def test_saas_readiness():
    service = SaasReadinessService()
    config = service.get_config()
    assert config["threshold_percent"] == 85.0

    assessment = service.run_assessment(
        passed_checks=[
            "RLS enforced",
            "Tenant header validated",
            "Org isolation tested",
            "Stripe integrated",
            "Plans configured",
            "Usage quotas enforced",
            "Signup flow live",
            "Demo data available",
            "Customer onboarding playbook",
            "Support channels live",
            "SLA defined",
            "Status page published",
            "User docs published",
            "API docs complete",
            "Internal runbooks ready",
            "Website live",
            "Pricing published",
            "Marketing assets ready",
        ],
    )
    assert assessment["ready"] is True

    categories = service.list_categories()
    assert categories["total"] >= 5
    assert service.validate_setup()["valid"] is True


def test_usage_tracking():
    service = UsageTrackingService()
    config = service.get_config()
    assert config["aggregation_period"] == "daily"

    recorded = service.track_usage(
        organization_id="org-1",
        metric="ai_tokens",
        amount=1200,
    )
    assert recorded["recorded"] is True
    assert recorded["metric"] == "ai_tokens"

    summary = service.summarize_usage(
        organization_id="org-1",
        usage={"ai_tokens": 1200, "reports": 4, "api_requests": 250},
    )
    assert summary["organization_id"] == "org-1"
    assert summary["tracked_metrics"] >= 4
    assert summary["total_billable_events"] == 1204

    metrics = service.list_metrics()
    assert metrics["total"] >= 4
    assert service.validate_setup()["valid"] is True


def test_product_demo():
    service = ProductDemoService()
    config = service.get_config()
    assert config["demo_id"] == "orgflow_product_demo_v1"

    readiness = service.evaluate_readiness(
        completed_scenarios=[
            "portfolio_overview",
            "ai_report_review",
            "operational_actions",
            "executive_insights",
        ],
    )
    assert readiness["demo_ready"] is True

    scenarios = service.list_scenarios()
    assert scenarios["total"] >= 4
    assert service.validate_setup()["valid"] is True


def test_product_readiness_dashboard_aggregates_all_domains():
    dashboard = build_dashboard()
    result = dashboard.get_dashboard()

    assert result["product_ready"] is True
    assert result["onboarding_flow"]["flow_id"] == "orgflow_signup_v1"
    assert result["billing_integration"]["provider"] == "stripe"
    assert result["saas_readiness"]["threshold_percent"] == 85.0
    assert result["usage_tracking"]["aggregation_period"] == "daily"
    assert result["product_demo"]["demo_id"] == "orgflow_product_demo_v1"


def _auth_headers():
    token = JWTService().issue_access_token(
        user_id="user-1",
        org_id="org-1",
        role="ADMIN",
        token_id="product-readiness-backlog-tests",
    )
    return {"Authorization": f"Bearer {token}", "X-Organization-ID": "org-1"}


def test_product_readiness_api_endpoints(monkeypatch):
    dashboard = build_dashboard()
    monkeypatch.setattr(
        main_module,
        "product_readiness_dashboard_service",
        dashboard,
    )

    client = TestClient(app)
    headers = _auth_headers()

    get_endpoints = [
        "/product-readiness/dashboard",
        "/product-readiness/onboarding/config",
        "/product-readiness/onboarding/steps",
        "/product-readiness/onboarding/progress",
        "/product-readiness/onboarding/validate",
        "/product-readiness/demo-data/config",
        "/product-readiness/demo-data/presets",
        "/product-readiness/demo-data/simulate",
        "/product-readiness/demo-data/validate",
        "/product-readiness/multi-tenant/config",
        "/product-readiness/multi-tenant/checklist",
        "/product-readiness/multi-tenant/evaluate",
        "/product-readiness/multi-tenant/validate",
        "/product-readiness/pricing/config",
        "/product-readiness/pricing/tiers",
        "/product-readiness/pricing/estimate",
        "/product-readiness/pricing/validate",
        "/product-readiness/admin/config",
        "/product-readiness/admin/modules",
        "/product-readiness/admin/access",
        "/product-readiness/admin/validate",
        "/product-readiness/analytics/config",
        "/product-readiness/analytics/events",
        "/product-readiness/analytics/evaluate",
        "/product-readiness/analytics/validate",
        "/product-readiness/quotas/config",
        "/product-readiness/quotas/list",
        "/product-readiness/quotas/check",
        "/product-readiness/quotas/validate",
        "/product-readiness/billing/config",
        "/product-readiness/billing/products",
        "/product-readiness/billing/webhook",
        "/product-readiness/billing/validate",
        "/product-readiness/subscriptions/config",
        "/product-readiness/subscriptions/plans",
        "/product-readiness/subscriptions/upgrade",
        "/product-readiness/subscriptions/validate",
        "/product-readiness/support/config",
        "/product-readiness/support/channels",
        "/product-readiness/support/sla",
        "/product-readiness/support/validate",
        "/product-readiness/documentation/config",
        "/product-readiness/documentation/sections",
        "/product-readiness/documentation/coverage",
        "/product-readiness/documentation/validate",
        "/product-readiness/api-docs/config",
        "/product-readiness/api-docs/groups",
        "/product-readiness/api-docs/completeness",
        "/product-readiness/api-docs/validate",
        "/product-readiness/dev-docs/config",
        "/product-readiness/dev-docs/guides",
        "/product-readiness/dev-docs/onboarding",
        "/product-readiness/dev-docs/validate",
        "/product-readiness/website/config",
        "/product-readiness/website/pages",
        "/product-readiness/website/launch",
        "/product-readiness/website/validate",
        "/product-readiness/marketing/config",
        "/product-readiness/marketing/assets",
        "/product-readiness/marketing/check",
        "/product-readiness/marketing/validate",
        "/product-readiness/investor-deck/config",
        "/product-readiness/investor-deck/slides",
        "/product-readiness/investor-deck/evaluate",
        "/product-readiness/investor-deck/validate",
        "/product-readiness/demo-env/config",
        "/product-readiness/demo-env/features",
        "/product-readiness/demo-env/health",
        "/product-readiness/demo-env/validate",
        "/product-readiness/beta/config",
        "/product-readiness/beta/stages",
        "/product-readiness/beta/enrollment",
        "/product-readiness/beta/validate",
        "/product-readiness/customer-onboarding/config",
        "/product-readiness/customer-onboarding/milestones",
        "/product-readiness/customer-onboarding/progress",
        "/product-readiness/customer-onboarding/validate",
        "/product-readiness/saas/config",
        "/product-readiness/saas/categories",
        "/product-readiness/saas/assessment",
        "/product-readiness/saas/validate",
        "/product-readiness/usage-tracking/config",
        "/product-readiness/usage-tracking/metrics",
        "/product-readiness/usage-tracking/record",
        "/product-readiness/usage-tracking/summary",
        "/product-readiness/usage-tracking/validate",
        "/product-readiness/product-demo/config",
        "/product-readiness/product-demo/scenarios",
        "/product-readiness/product-demo/evaluate",
        "/product-readiness/product-demo/validate",
    ]

    for path in get_endpoints:
        response = client.get(path, headers=headers)
        assert response.status_code == 200, path

    dashboard_response = client.get(
        "/product-readiness/dashboard",
        headers=headers,
    ).json()
    assert dashboard_response["product_ready"] is True
