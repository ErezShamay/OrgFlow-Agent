from __future__ import annotations

CDN_CONFIG = {
    "provider": "cloudflare",
    "enabled": True,
    "static_assets_path": "/_next/static/",
    "cache_ttl_seconds": 86400,
    "gzip_enabled": True,
    "brotli_enabled": True,
    "edge_locations": ["us-east", "eu-west", "ap-southeast"],
}


class CdnSetupService:
    def get_config(self) -> dict:
        return CDN_CONFIG

    def get_cache_rules(self) -> dict:
        rules = [
            {
                "pattern": "/_next/static/*",
                "ttl_seconds": 31536000,
                "cache_control": "public, max-age=31536000, immutable",
            },
            {
                "pattern": "/api/*",
                "ttl_seconds": 0,
                "cache_control": "no-store",
            },
            {
                "pattern": "/*.png",
                "ttl_seconds": 604800,
                "cache_control": "public, max-age=604800",
            },
        ]
        return {"rules": rules, "total": len(rules)}

    def validate_setup(self) -> dict:
        return {
            "valid": CDN_CONFIG["enabled"],
            "provider": CDN_CONFIG["provider"],
            "compression_enabled": (
                CDN_CONFIG["gzip_enabled"] and CDN_CONFIG["brotli_enabled"]
            ),
            "edge_locations": len(CDN_CONFIG["edge_locations"]),
        }
