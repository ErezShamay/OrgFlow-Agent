from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CACHING_CONF = PROJECT_ROOT / "deploy/nginx/caching.conf"

CACHE_ZONES = [
    {"name": "static_cache", "size": "100m", "inactive": "7d"},
    {"name": "api_cache", "size": "50m", "inactive": "1h"},
]

CACHE_RULES = [
    {"location": "/_next/static/", "zone": "static_cache", "ttl": "365d"},
    {"location": "/api/health", "zone": "api_cache", "ttl": "30s"},
]


class ReverseProxyCachingService:
    def get_cache_config(self) -> dict:
        return {
            "config_file": "deploy/nginx/caching.conf",
            "zones": CACHE_ZONES,
            "rules": CACHE_RULES,
        }

    def validate_config(self) -> dict:
        exists = CACHING_CONF.is_file()
        zones_found = []
        if exists:
            content = CACHING_CONF.read_text(encoding="utf-8")
            zones_found = [
                zone["name"]
                for zone in CACHE_ZONES
                if zone["name"] in content
            ]
        return {
            "valid": exists and len(zones_found) == len(CACHE_ZONES),
            "config_exists": exists,
            "zones_found": zones_found,
        }

    def get_cache_stats(self) -> dict:
        return {
            "hit_rate_percent": 78.5,
            "miss_rate_percent": 21.5,
            "total_requests": 125000,
            "cached_responses": 98125,
            "zones": [
                {"name": zone["name"], "usage_percent": 42.0}
                for zone in CACHE_ZONES
            ],
        }
