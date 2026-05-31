from __future__ import annotations

BILLING_CONFIG = {
    "provider": "stripe",
    "webhook_events": [
        "customer.subscription.created",
        "customer.subscription.updated",
        "invoice.paid",
        "invoice.payment_failed",
    ],
    "test_mode_supported": True,
}


class BillingIntegrationService:
    def get_config(self) -> dict:
        return BILLING_CONFIG

    def list_products(self) -> dict:
        products = [
            {"id": "prod_starter", "plan": "starter", "stripe_price_monthly": "price_starter_m"},
            {"id": "prod_growth", "plan": "growth", "stripe_price_monthly": "price_growth_m"},
            {"id": "prod_enterprise", "plan": "enterprise", "custom": True},
        ]
        return {"products": products, "total": len(products)}

    def simulate_webhook(self, *, event_type: str) -> dict:
        known = set(BILLING_CONFIG["webhook_events"])
        return {
            "processed": event_type in known,
            "event_type": event_type,
            "provider": BILLING_CONFIG["provider"],
        }

    def validate_setup(self) -> dict:
        return {
            "valid": True,
            "provider": BILLING_CONFIG["provider"],
            "webhooks_configured": len(BILLING_CONFIG["webhook_events"]) >= 3,
            "products_mapped": self.list_products()["total"] >= 3,
        }
