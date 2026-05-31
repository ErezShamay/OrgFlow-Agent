from __future__ import annotations

MARKETING_CONFIG = {
    "brand_kit_version": "2026.1",
    "formats": ["svg", "png", "pdf"],
    "cdn_bucket": "orgflow-marketing-assets",
}


class MarketingAssetsService:
    def get_config(self) -> dict:
        return MARKETING_CONFIG

    def list_assets(self) -> dict:
        assets = [
            {"id": "logo_primary", "type": "logo", "formats": ["svg", "png"]},
            {"id": "logo_dark", "type": "logo", "formats": ["svg", "png"]},
            {"id": "hero_illustration", "type": "illustration", "formats": ["svg", "png"]},
            {"id": "social_share", "type": "og_image", "formats": ["png"]},
            {"id": "one_pager", "type": "pdf", "formats": ["pdf"]},
        ]
        return {"assets": assets, "total": len(assets)}

    def check_asset(self, *, asset_id: str) -> dict:
        known = {a["id"] for a in self.list_assets()["assets"]}
        return {
            "exists": asset_id in known,
            "asset_id": asset_id,
            "brand_kit_version": MARKETING_CONFIG["brand_kit_version"],
        }

    def validate_setup(self) -> dict:
        return {
            "valid": True,
            "assets_catalogued": self.list_assets()["total"] >= 4,
            "brand_kit_version": MARKETING_CONFIG["brand_kit_version"],
        }
