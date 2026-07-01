"""Product readiness routes.

Extracted from app/main.py during the 2026-07 architecture-modularization
refactor. Shared service singletons live in app/dependencies.py; shared
request models live in app/schemas/api_requests.py.
"""
from __future__ import annotations


from fastapi import APIRouter
import app.dependencies as deps


router = APIRouter()


@router.get("/product-readiness/dashboard")
def get_product_readiness_dashboard():
    return deps.product_readiness_dashboard_service.get_dashboard()


@router.get("/product-readiness/onboarding/config")
def get_product_onboarding_config():
    return deps.product_readiness_dashboard_service.get_onboarding_config()


@router.get("/product-readiness/onboarding/steps")
def list_product_onboarding_steps():
    return deps.product_readiness_dashboard_service.list_onboarding_steps()


@router.get("/product-readiness/onboarding/progress")
def evaluate_product_onboarding_progress(completed_steps: str = ""):
    return deps.product_readiness_dashboard_service.evaluate_onboarding_progress(
        completed_steps=completed_steps,
    )


@router.get("/product-readiness/onboarding/validate")
def validate_product_onboarding_flow():
    return deps.product_readiness_dashboard_service.validate_onboarding_flow()


@router.get("/product-readiness/demo-data/config")
def get_product_demo_data_config():
    return deps.product_readiness_dashboard_service.get_demo_data_config()


@router.get("/product-readiness/demo-data/presets")
def list_product_demo_data_presets():
    return deps.product_readiness_dashboard_service.list_demo_data_presets()


@router.get("/product-readiness/demo-data/simulate")
def simulate_product_demo_data(preset_id: str = "startup"):
    return deps.product_readiness_dashboard_service.simulate_demo_data(preset_id=preset_id)


@router.get("/product-readiness/demo-data/validate")
def validate_product_demo_data_generator():
    return deps.product_readiness_dashboard_service.validate_demo_data_generator()


@router.get("/product-readiness/multi-tenant/config")
def get_product_multi_tenant_config():
    return deps.product_readiness_dashboard_service.get_multi_tenant_config()


@router.get("/product-readiness/multi-tenant/checklist")
def list_product_multi_tenant_checklist():
    return deps.product_readiness_dashboard_service.list_multi_tenant_checklist()


@router.get("/product-readiness/multi-tenant/evaluate")
def evaluate_product_multi_tenant_readiness(passed_items: str = ""):
    return deps.product_readiness_dashboard_service.evaluate_multi_tenant_readiness(
        passed_items=passed_items,
    )


@router.get("/product-readiness/multi-tenant/validate")
def validate_product_multi_tenant_readiness():
    return deps.product_readiness_dashboard_service.validate_multi_tenant_readiness()


@router.get("/product-readiness/pricing/config")
def get_product_pricing_config():
    return deps.product_readiness_dashboard_service.get_pricing_config()


@router.get("/product-readiness/pricing/tiers")
def list_product_pricing_tiers():
    return deps.product_readiness_dashboard_service.list_pricing_tiers()


@router.get("/product-readiness/pricing/estimate")
def calculate_product_pricing_estimate(
    tier_id: str = "starter",
    seats: int = 5,
    billing_period: str = "monthly",
):
    return deps.product_readiness_dashboard_service.calculate_pricing_estimate(
        tier_id=tier_id,
        seats=seats,
        billing_period=billing_period,
    )


@router.get("/product-readiness/pricing/validate")
def validate_product_pricing_model():
    return deps.product_readiness_dashboard_service.validate_pricing_model()


@router.get("/product-readiness/admin/config")
def get_product_admin_panel_config():
    return deps.product_readiness_dashboard_service.get_admin_panel_config()


@router.get("/product-readiness/admin/modules")
def list_product_admin_modules():
    return deps.product_readiness_dashboard_service.list_admin_modules()


@router.get("/product-readiness/admin/access")
def check_product_admin_access(role: str = "VIEWER"):
    return deps.product_readiness_dashboard_service.check_admin_access(role=role)


@router.get("/product-readiness/admin/validate")
def validate_product_admin_panel():
    return deps.product_readiness_dashboard_service.validate_admin_panel()


@router.get("/product-readiness/analytics/config")
def get_product_analytics_config():
    return deps.product_readiness_dashboard_service.get_product_analytics_config()


@router.get("/product-readiness/analytics/events")
def list_product_analytics_events():
    return deps.product_readiness_dashboard_service.list_product_analytics_events()


@router.get("/product-readiness/analytics/evaluate")
def evaluate_product_analytics(events_implemented: str = ""):
    return deps.product_readiness_dashboard_service.evaluate_product_analytics(
        events_implemented=events_implemented,
    )


@router.get("/product-readiness/analytics/validate")
def validate_product_analytics():
    return deps.product_readiness_dashboard_service.validate_product_analytics()


@router.get("/product-readiness/quotas/config")
def get_product_usage_quotas_config():
    return deps.product_readiness_dashboard_service.get_usage_quotas_config()


@router.get("/product-readiness/quotas/list")
def list_product_usage_quotas():
    return deps.product_readiness_dashboard_service.list_usage_quotas()


@router.get("/product-readiness/quotas/check")
def check_product_usage_quota(
    metric: str = "ai_tokens",
    plan: str = "starter",
    current_usage: int = 0,
):
    return deps.product_readiness_dashboard_service.check_usage_quota(
        metric=metric,
        plan=plan,
        current_usage=current_usage,
    )


@router.get("/product-readiness/quotas/validate")
def validate_product_usage_quotas():
    return deps.product_readiness_dashboard_service.validate_usage_quotas()


@router.get("/product-readiness/billing/config")
def get_product_billing_config():
    return deps.product_readiness_dashboard_service.get_billing_config()


@router.get("/product-readiness/billing/products")
def list_product_billing_products():
    return deps.product_readiness_dashboard_service.list_billing_products()


@router.get("/product-readiness/billing/webhook")
def simulate_product_billing_webhook(event_type: str = "invoice.paid"):
    return deps.product_readiness_dashboard_service.simulate_billing_webhook(
        event_type=event_type,
    )


@router.get("/product-readiness/billing/validate")
def validate_product_billing_integration():
    return deps.product_readiness_dashboard_service.validate_billing_integration()


@router.get("/product-readiness/subscriptions/config")
def get_product_subscription_config():
    return deps.product_readiness_dashboard_service.get_subscription_config()


@router.get("/product-readiness/subscriptions/plans")
def list_product_subscription_plans():
    return deps.product_readiness_dashboard_service.list_subscription_plans()


@router.get("/product-readiness/subscriptions/upgrade")
def evaluate_product_subscription_upgrade(
    from_plan: str = "starter",
    to_plan: str = "growth",
):
    return deps.product_readiness_dashboard_service.evaluate_subscription_upgrade(
        from_plan=from_plan,
        to_plan=to_plan,
    )


@router.get("/product-readiness/subscriptions/validate")
def validate_product_subscription_plans():
    return deps.product_readiness_dashboard_service.validate_subscription_plans()


@router.get("/product-readiness/support/config")
def get_product_support_config():
    return deps.product_readiness_dashboard_service.get_support_config()


@router.get("/product-readiness/support/channels")
def list_product_support_channels():
    return deps.product_readiness_dashboard_service.list_support_channels()


@router.get("/product-readiness/support/sla")
def evaluate_product_support_sla(
    plan: str = "starter",
    hours_open: float = 0.0,
):
    return deps.product_readiness_dashboard_service.evaluate_support_sla(
        plan=plan,
        hours_open=hours_open,
    )


@router.get("/product-readiness/support/validate")
def validate_product_support_tooling():
    return deps.product_readiness_dashboard_service.validate_support_tooling()


@router.get("/product-readiness/documentation/config")
def get_product_documentation_config():
    return deps.product_readiness_dashboard_service.get_documentation_config()


@router.get("/product-readiness/documentation/sections")
def list_product_documentation_sections():
    return deps.product_readiness_dashboard_service.list_documentation_sections()


@router.get("/product-readiness/documentation/coverage")
def evaluate_product_documentation_coverage(published_sections: str = ""):
    return deps.product_readiness_dashboard_service.evaluate_documentation_coverage(
        published_sections=published_sections,
    )


@router.get("/product-readiness/documentation/validate")
def validate_product_documentation():
    return deps.product_readiness_dashboard_service.validate_documentation()


@router.get("/product-readiness/api-docs/config")
def get_product_api_docs_config():
    return deps.product_readiness_dashboard_service.get_api_docs_config()


@router.get("/product-readiness/api-docs/groups")
def list_product_api_doc_groups():
    return deps.product_readiness_dashboard_service.list_api_doc_groups()


@router.get("/product-readiness/api-docs/completeness")
def evaluate_product_api_docs_completeness(documented_tags: str = ""):
    return deps.product_readiness_dashboard_service.evaluate_api_docs_completeness(
        documented_tags=documented_tags,
    )


@router.get("/product-readiness/api-docs/validate")
def validate_product_api_documentation():
    return deps.product_readiness_dashboard_service.validate_api_documentation()


@router.get("/product-readiness/dev-docs/config")
def get_product_internal_docs_config():
    return deps.product_readiness_dashboard_service.get_internal_docs_config()


@router.get("/product-readiness/dev-docs/guides")
def list_product_internal_docs_guides():
    return deps.product_readiness_dashboard_service.list_internal_docs_guides()


@router.get("/product-readiness/dev-docs/onboarding")
def evaluate_product_internal_docs_onboarding(available_guides: str = ""):
    return deps.product_readiness_dashboard_service.evaluate_internal_docs_onboarding(
        available_guides=available_guides,
    )


@router.get("/product-readiness/dev-docs/validate")
def validate_product_internal_developer_docs():
    return deps.product_readiness_dashboard_service.validate_internal_developer_docs()


@router.get("/product-readiness/website/config")
def get_product_website_config():
    return deps.product_readiness_dashboard_service.get_product_website_config()


@router.get("/product-readiness/website/pages")
def list_product_website_pages():
    return deps.product_readiness_dashboard_service.list_product_website_pages()


@router.get("/product-readiness/website/launch")
def evaluate_product_website_launch(published_slugs: str = ""):
    return deps.product_readiness_dashboard_service.evaluate_product_website_launch(
        published_slugs=published_slugs,
    )


@router.get("/product-readiness/website/validate")
def validate_product_website():
    return deps.product_readiness_dashboard_service.validate_product_website()


@router.get("/product-readiness/marketing/config")
def get_product_marketing_assets_config():
    return deps.product_readiness_dashboard_service.get_marketing_assets_config()


@router.get("/product-readiness/marketing/assets")
def list_product_marketing_assets():
    return deps.product_readiness_dashboard_service.list_marketing_assets()


@router.get("/product-readiness/marketing/check")
def check_product_marketing_asset(asset_id: str = "logo_primary"):
    return deps.product_readiness_dashboard_service.check_marketing_asset(asset_id=asset_id)


@router.get("/product-readiness/marketing/validate")
def validate_product_marketing_assets():
    return deps.product_readiness_dashboard_service.validate_marketing_assets()


@router.get("/product-readiness/investor-deck/config")
def get_product_investor_deck_config():
    return deps.product_readiness_dashboard_service.get_investor_deck_config()


@router.get("/product-readiness/investor-deck/slides")
def list_product_investor_deck_slides():
    return deps.product_readiness_dashboard_service.list_investor_deck_slides()


@router.get("/product-readiness/investor-deck/evaluate")
def evaluate_product_investor_deck(completed_slides: str = ""):
    return deps.product_readiness_dashboard_service.evaluate_investor_deck(
        completed_slides=completed_slides,
    )


@router.get("/product-readiness/investor-deck/validate")
def validate_product_investor_demo_deck():
    return deps.product_readiness_dashboard_service.validate_investor_demo_deck()


@router.get("/product-readiness/demo-env/config")
def get_product_demo_environment_config():
    return deps.product_readiness_dashboard_service.get_demo_environment_config()


@router.get("/product-readiness/demo-env/features")
def list_product_demo_environment_features():
    return deps.product_readiness_dashboard_service.list_demo_environment_features()


@router.get("/product-readiness/demo-env/health")
def evaluate_product_demo_environment_health(
    api_up: bool = True,
    ui_up: bool = True,
    data_seeded: bool = True,
):
    return deps.product_readiness_dashboard_service.evaluate_demo_environment_health(
        api_up=api_up,
        ui_up=ui_up,
        data_seeded=data_seeded,
    )


@router.get("/product-readiness/demo-env/validate")
def validate_product_demo_environment():
    return deps.product_readiness_dashboard_service.validate_demo_environment()


@router.get("/product-readiness/beta/config")
def get_product_beta_testing_config():
    return deps.product_readiness_dashboard_service.get_beta_testing_config()


@router.get("/product-readiness/beta/stages")
def list_product_beta_testing_stages():
    return deps.product_readiness_dashboard_service.list_beta_testing_stages()


@router.get("/product-readiness/beta/enrollment")
def evaluate_product_beta_enrollment(
    current_participants: int = 0,
    approved: bool = True,
):
    return deps.product_readiness_dashboard_service.evaluate_beta_enrollment(
        current_participants=current_participants,
        approved=approved,
    )


@router.get("/product-readiness/beta/validate")
def validate_product_beta_testing_flow():
    return deps.product_readiness_dashboard_service.validate_beta_testing_flow()


@router.get("/product-readiness/customer-onboarding/config")
def get_product_customer_onboarding_config():
    return deps.product_readiness_dashboard_service.get_customer_onboarding_config()


@router.get("/product-readiness/customer-onboarding/milestones")
def list_product_customer_onboarding_milestones():
    return deps.product_readiness_dashboard_service.list_customer_onboarding_milestones()


@router.get("/product-readiness/customer-onboarding/progress")
def evaluate_product_customer_onboarding(completed_milestones: str = ""):
    return deps.product_readiness_dashboard_service.evaluate_customer_onboarding(
        completed_milestones=completed_milestones,
    )


@router.get("/product-readiness/customer-onboarding/validate")
def validate_product_customer_onboarding_flow():
    return deps.product_readiness_dashboard_service.validate_customer_onboarding_flow()


@router.get("/product-readiness/saas/config")
def get_product_saas_readiness_config():
    return deps.product_readiness_dashboard_service.get_saas_readiness_config()


@router.get("/product-readiness/saas/categories")
def list_product_saas_readiness_categories():
    return deps.product_readiness_dashboard_service.list_saas_readiness_categories()


@router.get("/product-readiness/saas/assessment")
def run_product_saas_readiness_assessment(passed_checks: str | None = None):
    return deps.product_readiness_dashboard_service.run_saas_readiness_assessment(
        passed_checks=passed_checks,
    )


@router.get("/product-readiness/saas/validate")
def validate_product_saas_readiness():
    return deps.product_readiness_dashboard_service.validate_saas_readiness()


@router.get("/product-readiness/usage-tracking/config")
def get_product_usage_tracking_config():
    return deps.product_readiness_dashboard_service.get_usage_tracking_config()


@router.get("/product-readiness/usage-tracking/metrics")
def list_product_usage_tracking_metrics():
    return deps.product_readiness_dashboard_service.list_usage_tracking_metrics()


@router.get("/product-readiness/usage-tracking/record")
def record_product_usage(
    organization_id: str = "org-1",
    metric: str = "ai_tokens",
    amount: int = 0,
):
    return deps.product_readiness_dashboard_service.track_usage(
        organization_id=organization_id,
        metric=metric,
        amount=amount,
    )


@router.get("/product-readiness/usage-tracking/summary")
def summarize_product_usage(
    organization_id: str = "org-1",
    ai_tokens: int = 0,
    reports: int = 0,
    api_requests: int = 0,
    storage_gb: int = 0,
    active_users: int = 0,
):
    return deps.product_readiness_dashboard_service.summarize_usage_tracking(
        organization_id=organization_id,
        ai_tokens=ai_tokens,
        reports=reports,
        api_requests=api_requests,
        storage_gb=storage_gb,
        active_users=active_users,
    )


@router.get("/product-readiness/usage-tracking/validate")
def validate_product_usage_tracking():
    return deps.product_readiness_dashboard_service.validate_usage_tracking()


@router.get("/product-readiness/product-demo/config")
def get_product_demo_config():
    return deps.product_readiness_dashboard_service.get_product_demo_config()


@router.get("/product-readiness/product-demo/scenarios")
def list_product_demo_scenarios():
    return deps.product_readiness_dashboard_service.list_product_demo_scenarios()


@router.get("/product-readiness/product-demo/evaluate")
def evaluate_product_demo(completed_scenarios: str = ""):
    return deps.product_readiness_dashboard_service.evaluate_product_demo(
        completed_scenarios=completed_scenarios,
    )


@router.get("/product-readiness/product-demo/validate")
def validate_product_demo():
    return deps.product_readiness_dashboard_service.validate_product_demo()


