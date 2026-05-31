from __future__ import annotations

WEBSITE_CONFIG = {
    "domain": "https://orgflow.example.com",
    "framework": "nextjs",
    "locales": ["en", "he"],
    "seo_enabled": True,
}


class ProductWebsiteService:
    def get_config(self) -> dict:
        return WEBSITE_CONFIG

    def list_pages(self) -> dict:
        pages = [
            {"slug": "/", "title": "Home"},
            {"slug": "/pricing", "title": "Pricing"},
            {"slug": "/features", "title": "Features"},
            {"slug": "/security", "title": "Security"},
            {"slug": "/contact", "title": "Contact"},
        ]
        return {"pages": pages, "total": len(pages)}

    def evaluate_launch(self, *, published_slugs: list[str]) -> dict:
        required = {"/", "/pricing", "/features"}
        published = set(published_slugs)
        return {
            "launch_ready": required.issubset(published),
            "missing_pages": sorted(required - published),
        }

    def validate_setup(self) -> dict:
        return {
            "valid": True,
            "domain": WEBSITE_CONFIG["domain"],
            "pages_defined": self.list_pages()["total"] >= 4,
        }
