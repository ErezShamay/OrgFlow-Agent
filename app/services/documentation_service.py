from __future__ import annotations

DOCUMENTATION_CONFIG = {
    "format": "mdx",
    "base_path": "docs/user",
    "search_enabled": True,
    "versioned": True,
}


class DocumentationService:
    def get_config(self) -> dict:
        return DOCUMENTATION_CONFIG

    def list_sections(self) -> dict:
        sections = [
            {"id": "getting_started", "pages": 5},
            {"id": "projects", "pages": 8},
            {"id": "reports", "pages": 6},
            {"id": "ai_reviews", "pages": 7},
            {"id": "billing", "pages": 4},
        ]
        return {"sections": sections, "total": len(sections)}

    def evaluate_coverage(self, *, published_sections: list[str]) -> dict:
        required = {"getting_started", "projects", "reports"}
        published = set(published_sections)
        return {
            "launch_ready": required.issubset(published),
            "published_count": len(published),
            "missing_required": sorted(required - published),
        }

    def validate_setup(self) -> dict:
        return {
            "valid": True,
            "sections_defined": self.list_sections()["total"] >= 4,
            "search_enabled": DOCUMENTATION_CONFIG["search_enabled"],
        }
