from __future__ import annotations

PRICING_CONFIG = {
    "currency": "USD",
    "billing_periods": ["monthly", "annual"],
    "model": "per_seat_with_usage_addons",
    "annual_discount_percent": 20,
}


class PricingModelService:
    def get_config(self) -> dict:
        return PRICING_CONFIG

    def list_tiers(self) -> dict:
        tiers = [
            {"id": "starter", "seat_price_monthly": 29, "included_seats": 5},
            {"id": "growth", "seat_price_monthly": 49, "included_seats": 25},
            {"id": "enterprise", "seat_price_monthly": 0, "custom_quote": True},
        ]
        return {"tiers": tiers, "total": len(tiers)}

    def calculate_estimate(
        self,
        *,
        tier_id: str,
        seats: int,
        billing_period: str = "monthly",
    ) -> dict:
        tiers = {t["id"]: t for t in self.list_tiers()["tiers"]}
        tier = tiers.get(tier_id)
        if tier is None or tier.get("custom_quote"):
            return {"estimated": False, "requires_quote": True}
        monthly = tier["seat_price_monthly"] * seats
        if billing_period == "annual":
            discount = PRICING_CONFIG["annual_discount_percent"] / 100
            annual = monthly * 12 * (1 - discount)
            return {
                "estimated": True,
                "tier_id": tier_id,
                "seats": seats,
                "billing_period": billing_period,
                "annual_total": round(annual, 2),
            }
        return {
            "estimated": True,
            "tier_id": tier_id,
            "seats": seats,
            "billing_period": billing_period,
            "monthly_total": monthly,
        }

    def validate_setup(self) -> dict:
        return {
            "valid": True,
            "currency": PRICING_CONFIG["currency"],
            "tiers_defined": self.list_tiers()["total"] >= 3,
        }
