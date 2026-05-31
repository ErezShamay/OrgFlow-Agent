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
from app.services.product_website_service import ProductWebsiteService
from app.services.saas_readiness_service import SaasReadinessService
from app.services.subscription_plans_service import SubscriptionPlansService
from app.services.support_tooling_service import SupportToolingService
from app.services.usage_quotas_service import UsageQuotasService
from app.services.usage_tracking_service import UsageTrackingService


class ProductReadinessDashboardService:
    def __init__(
        self,
        onboarding_flow_service: OnboardingFlowService | None = None,
        demo_data_generator_service: DemoDataGeneratorService | None = None,
        multi_tenant_readiness_service: MultiTenantReadinessService | None = None,
        pricing_model_service: PricingModelService | None = None,
        admin_panel_service: AdminPanelService | None = None,
        product_analytics_service: ProductAnalyticsService | None = None,
        usage_quotas_service: UsageQuotasService | None = None,
        billing_integration_service: BillingIntegrationService | None = None,
        subscription_plans_service: SubscriptionPlansService | None = None,
        support_tooling_service: SupportToolingService | None = None,
        documentation_service: DocumentationService | None = None,
        api_documentation_service: ApiDocumentationService | None = None,
        internal_developer_docs_service: InternalDeveloperDocsService | None = None,
        product_website_service: ProductWebsiteService | None = None,
        marketing_assets_service: MarketingAssetsService | None = None,
        investor_demo_deck_service: InvestorDemoDeckService | None = None,
        demo_environment_service: DemoEnvironmentService | None = None,
        beta_testing_flow_service: BetaTestingFlowService | None = None,
        customer_onboarding_flow_service: CustomerOnboardingFlowService | None = None,
        saas_readiness_service: SaasReadinessService | None = None,
        usage_tracking_service: UsageTrackingService | None = None,
        product_demo_service: ProductDemoService | None = None,
    ):
        self.onboarding_flow_service = onboarding_flow_service or OnboardingFlowService()
        self.demo_data_generator_service = (
            demo_data_generator_service or DemoDataGeneratorService()
        )
        self.multi_tenant_readiness_service = (
            multi_tenant_readiness_service or MultiTenantReadinessService()
        )
        self.pricing_model_service = pricing_model_service or PricingModelService()
        self.admin_panel_service = admin_panel_service or AdminPanelService()
        self.product_analytics_service = (
            product_analytics_service or ProductAnalyticsService()
        )
        self.usage_quotas_service = usage_quotas_service or UsageQuotasService()
        self.billing_integration_service = (
            billing_integration_service or BillingIntegrationService()
        )
        self.subscription_plans_service = (
            subscription_plans_service or SubscriptionPlansService()
        )
        self.support_tooling_service = support_tooling_service or SupportToolingService()
        self.documentation_service = documentation_service or DocumentationService()
        self.api_documentation_service = (
            api_documentation_service or ApiDocumentationService()
        )
        self.internal_developer_docs_service = (
            internal_developer_docs_service or InternalDeveloperDocsService()
        )
        self.product_website_service = product_website_service or ProductWebsiteService()
        self.marketing_assets_service = (
            marketing_assets_service or MarketingAssetsService()
        )
        self.investor_demo_deck_service = (
            investor_demo_deck_service or InvestorDemoDeckService()
        )
        self.demo_environment_service = demo_environment_service or DemoEnvironmentService()
        self.beta_testing_flow_service = (
            beta_testing_flow_service or BetaTestingFlowService()
        )
        self.customer_onboarding_flow_service = (
            customer_onboarding_flow_service or CustomerOnboardingFlowService()
        )
        self.saas_readiness_service = saas_readiness_service or SaasReadinessService()
        self.usage_tracking_service = usage_tracking_service or UsageTrackingService()
        self.product_demo_service = product_demo_service or ProductDemoService()

    def get_dashboard(self) -> dict:
        validations = [
            self.onboarding_flow_service.validate_setup()["valid"],
            self.demo_data_generator_service.validate_setup()["valid"],
            self.multi_tenant_readiness_service.validate_setup()["valid"],
            self.pricing_model_service.validate_setup()["valid"],
            self.admin_panel_service.validate_setup()["valid"],
            self.product_analytics_service.validate_setup()["valid"],
            self.usage_quotas_service.validate_setup()["valid"],
            self.billing_integration_service.validate_setup()["valid"],
            self.subscription_plans_service.validate_setup()["valid"],
            self.support_tooling_service.validate_setup()["valid"],
            self.documentation_service.validate_setup()["valid"],
            self.api_documentation_service.validate_setup()["valid"],
            self.internal_developer_docs_service.validate_setup()["valid"],
            self.product_website_service.validate_setup()["valid"],
            self.marketing_assets_service.validate_setup()["valid"],
            self.investor_demo_deck_service.validate_setup()["valid"],
            self.demo_environment_service.validate_setup()["valid"],
            self.beta_testing_flow_service.validate_setup()["valid"],
            self.customer_onboarding_flow_service.validate_setup()["valid"],
            self.saas_readiness_service.validate_setup()["valid"],
            self.usage_tracking_service.validate_setup()["valid"],
            self.product_demo_service.validate_setup()["valid"],
        ]

        return {
            "onboarding_flow": self.onboarding_flow_service.get_config(),
            "demo_data_generator": self.demo_data_generator_service.get_config(),
            "multi_tenant_readiness": self.multi_tenant_readiness_service.get_config(),
            "pricing_model": self.pricing_model_service.get_config(),
            "admin_panel": self.admin_panel_service.get_config(),
            "product_analytics": self.product_analytics_service.get_config(),
            "usage_quotas": self.usage_quotas_service.get_config(),
            "billing_integration": self.billing_integration_service.get_config(),
            "subscription_plans": self.subscription_plans_service.get_config(),
            "support_tooling": self.support_tooling_service.get_config(),
            "documentation": self.documentation_service.get_config(),
            "api_documentation": self.api_documentation_service.get_config(),
            "internal_developer_docs": self.internal_developer_docs_service.get_config(),
            "product_website": self.product_website_service.get_config(),
            "marketing_assets": self.marketing_assets_service.get_config(),
            "investor_demo_deck": self.investor_demo_deck_service.get_config(),
            "demo_environment": self.demo_environment_service.get_config(),
            "beta_testing_flow": self.beta_testing_flow_service.get_config(),
            "customer_onboarding_flow": (
                self.customer_onboarding_flow_service.get_config()
            ),
            "saas_readiness": self.saas_readiness_service.get_config(),
            "usage_tracking": self.usage_tracking_service.get_config(),
            "product_demo": self.product_demo_service.get_config(),
            "product_ready": all(validations),
        }

    def get_onboarding_config(self) -> dict:
        return self.onboarding_flow_service.get_config()

    def list_onboarding_steps(self) -> dict:
        return self.onboarding_flow_service.list_steps()

    def evaluate_onboarding_progress(self, *, completed_steps: str = "") -> dict:
        steps = [s for s in completed_steps.split(",") if s]
        return self.onboarding_flow_service.evaluate_progress(completed_steps=steps)

    def validate_onboarding_flow(self) -> dict:
        return self.onboarding_flow_service.validate_setup()

    def get_demo_data_config(self) -> dict:
        return self.demo_data_generator_service.get_config()

    def list_demo_data_presets(self) -> dict:
        return self.demo_data_generator_service.list_presets()

    def simulate_demo_data(self, *, preset_id: str = "startup") -> dict:
        return self.demo_data_generator_service.simulate_generation(preset_id=preset_id)

    def validate_demo_data_generator(self) -> dict:
        return self.demo_data_generator_service.validate_setup()

    def get_multi_tenant_config(self) -> dict:
        return self.multi_tenant_readiness_service.get_config()

    def list_multi_tenant_checklist(self) -> dict:
        return self.multi_tenant_readiness_service.list_checklist()

    def evaluate_multi_tenant_readiness(self, *, passed_items: str = "") -> dict:
        items = [i for i in passed_items.split(",") if i]
        return self.multi_tenant_readiness_service.evaluate_readiness(
            passed_item_ids=items
        )

    def validate_multi_tenant_readiness(self) -> dict:
        return self.multi_tenant_readiness_service.validate_setup()

    def get_pricing_config(self) -> dict:
        return self.pricing_model_service.get_config()

    def list_pricing_tiers(self) -> dict:
        return self.pricing_model_service.list_tiers()

    def calculate_pricing_estimate(
        self,
        *,
        tier_id: str = "starter",
        seats: int = 5,
        billing_period: str = "monthly",
    ) -> dict:
        return self.pricing_model_service.calculate_estimate(
            tier_id=tier_id,
            seats=seats,
            billing_period=billing_period,
        )

    def validate_pricing_model(self) -> dict:
        return self.pricing_model_service.validate_setup()

    def get_admin_panel_config(self) -> dict:
        return self.admin_panel_service.get_config()

    def list_admin_modules(self) -> dict:
        return self.admin_panel_service.list_modules()

    def check_admin_access(self, *, role: str = "VIEWER") -> dict:
        return self.admin_panel_service.check_access(role=role)

    def validate_admin_panel(self) -> dict:
        return self.admin_panel_service.validate_setup()

    def get_product_analytics_config(self) -> dict:
        return self.product_analytics_service.get_config()

    def list_product_analytics_events(self) -> dict:
        return self.product_analytics_service.list_events()

    def evaluate_product_analytics(self, *, events_implemented: str = "") -> dict:
        events = [e for e in events_implemented.split(",") if e]
        return self.product_analytics_service.evaluate_tracking(
            events_implemented=events
        )

    def validate_product_analytics(self) -> dict:
        return self.product_analytics_service.validate_setup()

    def get_usage_quotas_config(self) -> dict:
        return self.usage_quotas_service.get_config()

    def list_usage_quotas(self) -> dict:
        return self.usage_quotas_service.list_quotas()

    def check_usage_quota(
        self,
        *,
        metric: str = "ai_tokens",
        plan: str = "starter",
        current_usage: int = 0,
    ) -> dict:
        return self.usage_quotas_service.check_usage(
            metric=metric,
            plan=plan,
            current_usage=current_usage,
        )

    def validate_usage_quotas(self) -> dict:
        return self.usage_quotas_service.validate_setup()

    def get_billing_config(self) -> dict:
        return self.billing_integration_service.get_config()

    def list_billing_products(self) -> dict:
        return self.billing_integration_service.list_products()

    def simulate_billing_webhook(self, *, event_type: str = "invoice.paid") -> dict:
        return self.billing_integration_service.simulate_webhook(event_type=event_type)

    def validate_billing_integration(self) -> dict:
        return self.billing_integration_service.validate_setup()

    def get_subscription_config(self) -> dict:
        return self.subscription_plans_service.get_config()

    def list_subscription_plans(self) -> dict:
        return self.subscription_plans_service.list_plans()

    def evaluate_subscription_upgrade(
        self,
        *,
        from_plan: str = "starter",
        to_plan: str = "growth",
    ) -> dict:
        return self.subscription_plans_service.evaluate_upgrade(
            from_plan=from_plan,
            to_plan=to_plan,
        )

    def validate_subscription_plans(self) -> dict:
        return self.subscription_plans_service.validate_setup()

    def get_support_config(self) -> dict:
        return self.support_tooling_service.get_config()

    def list_support_channels(self) -> dict:
        return self.support_tooling_service.list_channels()

    def evaluate_support_sla(
        self,
        *,
        plan: str = "starter",
        hours_open: float = 0.0,
    ) -> dict:
        return self.support_tooling_service.evaluate_sla(
            plan=plan,
            hours_open=hours_open,
        )

    def validate_support_tooling(self) -> dict:
        return self.support_tooling_service.validate_setup()

    def get_documentation_config(self) -> dict:
        return self.documentation_service.get_config()

    def list_documentation_sections(self) -> dict:
        return self.documentation_service.list_sections()

    def evaluate_documentation_coverage(self, *, published_sections: str = "") -> dict:
        sections = [s for s in published_sections.split(",") if s]
        return self.documentation_service.evaluate_coverage(
            published_sections=sections
        )

    def validate_documentation(self) -> dict:
        return self.documentation_service.validate_setup()

    def get_api_docs_config(self) -> dict:
        return self.api_documentation_service.get_config()

    def list_api_doc_groups(self) -> dict:
        return self.api_documentation_service.list_documented_groups()

    def evaluate_api_docs_completeness(self, *, documented_tags: str = "") -> dict:
        tags = [t for t in documented_tags.split(",") if t]
        return self.api_documentation_service.evaluate_completeness(
            documented_tags=tags
        )

    def validate_api_documentation(self) -> dict:
        return self.api_documentation_service.validate_setup()

    def get_internal_docs_config(self) -> dict:
        return self.internal_developer_docs_service.get_config()

    def list_internal_docs_guides(self) -> dict:
        return self.internal_developer_docs_service.list_guides()

    def evaluate_internal_docs_onboarding(self, *, available_guides: str = "") -> dict:
        guides = [g for g in available_guides.split(",") if g]
        return self.internal_developer_docs_service.evaluate_onboarding_pack(
            available_guides=guides
        )

    def validate_internal_developer_docs(self) -> dict:
        return self.internal_developer_docs_service.validate_setup()

    def get_product_website_config(self) -> dict:
        return self.product_website_service.get_config()

    def list_product_website_pages(self) -> dict:
        return self.product_website_service.list_pages()

    def evaluate_product_website_launch(self, *, published_slugs: str = "") -> dict:
        slugs = [s for s in published_slugs.split(",") if s]
        return self.product_website_service.evaluate_launch(published_slugs=slugs)

    def validate_product_website(self) -> dict:
        return self.product_website_service.validate_setup()

    def get_marketing_assets_config(self) -> dict:
        return self.marketing_assets_service.get_config()

    def list_marketing_assets(self) -> dict:
        return self.marketing_assets_service.list_assets()

    def check_marketing_asset(self, *, asset_id: str = "logo_primary") -> dict:
        return self.marketing_assets_service.check_asset(asset_id=asset_id)

    def validate_marketing_assets(self) -> dict:
        return self.marketing_assets_service.validate_setup()

    def get_investor_deck_config(self) -> dict:
        return self.investor_demo_deck_service.get_config()

    def list_investor_deck_slides(self) -> dict:
        return self.investor_demo_deck_service.list_slides()

    def evaluate_investor_deck(self, *, completed_slides: str = "") -> dict:
        slides = [int(s) for s in completed_slides.split(",") if s.strip().isdigit()]
        return self.investor_demo_deck_service.evaluate_readiness(
            completed_slides=slides
        )

    def validate_investor_demo_deck(self) -> dict:
        return self.investor_demo_deck_service.validate_setup()

    def get_demo_environment_config(self) -> dict:
        return self.demo_environment_service.get_config()

    def list_demo_environment_features(self) -> dict:
        return self.demo_environment_service.list_features()

    def evaluate_demo_environment_health(
        self,
        *,
        api_up: bool = True,
        ui_up: bool = True,
        data_seeded: bool = True,
    ) -> dict:
        return self.demo_environment_service.evaluate_health(
            api_up=api_up,
            ui_up=ui_up,
            data_seeded=data_seeded,
        )

    def validate_demo_environment(self) -> dict:
        return self.demo_environment_service.validate_setup()

    def get_beta_testing_config(self) -> dict:
        return self.beta_testing_flow_service.get_config()

    def list_beta_testing_stages(self) -> dict:
        return self.beta_testing_flow_service.list_stages()

    def evaluate_beta_enrollment(
        self,
        *,
        current_participants: int = 0,
        approved: bool = True,
    ) -> dict:
        return self.beta_testing_flow_service.evaluate_enrollment(
            current_participants=current_participants,
            approved=approved,
        )

    def validate_beta_testing_flow(self) -> dict:
        return self.beta_testing_flow_service.validate_setup()

    def get_customer_onboarding_config(self) -> dict:
        return self.customer_onboarding_flow_service.get_config()

    def list_customer_onboarding_milestones(self) -> dict:
        return self.customer_onboarding_flow_service.list_milestones()

    def evaluate_customer_onboarding(self, *, completed_milestones: str = "") -> dict:
        milestones = [m for m in completed_milestones.split(",") if m]
        return self.customer_onboarding_flow_service.evaluate_progress(
            completed_milestones=milestones
        )

    def validate_customer_onboarding_flow(self) -> dict:
        return self.customer_onboarding_flow_service.validate_setup()

    def get_saas_readiness_config(self) -> dict:
        return self.saas_readiness_service.get_config()

    def list_saas_readiness_categories(self) -> dict:
        return self.saas_readiness_service.list_categories()

    def run_saas_readiness_assessment(self, *, passed_checks: str | None = None) -> dict:
        checks = passed_checks.split(",") if passed_checks else None
        return self.saas_readiness_service.run_assessment(passed_checks=checks)

    def validate_saas_readiness(self) -> dict:
        return self.saas_readiness_service.validate_setup()

    def get_usage_tracking_config(self) -> dict:
        return self.usage_tracking_service.get_config()

    def list_usage_tracking_metrics(self) -> dict:
        return self.usage_tracking_service.list_metrics()

    def track_usage(
        self,
        *,
        organization_id: str = "org-1",
        metric: str = "ai_tokens",
        amount: int = 0,
    ) -> dict:
        return self.usage_tracking_service.track_usage(
            organization_id=organization_id,
            metric=metric,
            amount=amount,
        )

    def summarize_usage_tracking(
        self,
        *,
        organization_id: str = "org-1",
        ai_tokens: int = 0,
        reports: int = 0,
        api_requests: int = 0,
        storage_gb: int = 0,
        active_users: int = 0,
    ) -> dict:
        usage = {
            "ai_tokens": ai_tokens,
            "reports": reports,
            "api_requests": api_requests,
            "storage_gb": storage_gb,
            "active_users": active_users,
        }
        return self.usage_tracking_service.summarize_usage(
            organization_id=organization_id,
            usage=usage,
        )

    def validate_usage_tracking(self) -> dict:
        return self.usage_tracking_service.validate_setup()

    def get_product_demo_config(self) -> dict:
        return self.product_demo_service.get_config()

    def list_product_demo_scenarios(self) -> dict:
        return self.product_demo_service.list_scenarios()

    def evaluate_product_demo(self, *, completed_scenarios: str = "") -> dict:
        scenarios = [s for s in completed_scenarios.split(",") if s]
        return self.product_demo_service.evaluate_readiness(
            completed_scenarios=scenarios
        )

    def validate_product_demo(self) -> dict:
        return self.product_demo_service.validate_setup()
