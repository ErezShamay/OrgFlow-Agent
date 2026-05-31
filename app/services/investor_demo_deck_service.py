from __future__ import annotations

DECK_CONFIG = {
    "deck_id": "orgflow_investor_v1",
    "format": "google_slides",
    "target_duration_minutes": 12,
    "languages": ["en"],
}


class InvestorDemoDeckService:
    def get_config(self) -> dict:
        return DECK_CONFIG

    def list_slides(self) -> dict:
        slides = [
            {"number": 1, "title": "Problem", "speaker_notes": True},
            {"number": 2, "title": "Solution", "speaker_notes": True},
            {"number": 3, "title": "Product demo", "speaker_notes": True},
            {"number": 4, "title": "Traction", "speaker_notes": True},
            {"number": 5, "title": "Market", "speaker_notes": False},
            {"number": 6, "title": "Business model", "speaker_notes": True},
            {"number": 7, "title": "Team", "speaker_notes": False},
            {"number": 8, "title": "Ask", "speaker_notes": True},
        ]
        return {"slides": slides, "total": len(slides)}

    def evaluate_readiness(self, *, completed_slides: list[int]) -> dict:
        required = {1, 2, 3, 4, 6, 8}
        done = set(completed_slides)
        return {
            "demo_ready": required.issubset(done),
            "completed": len(done),
            "total": self.list_slides()["total"],
            "missing_required": sorted(required - done),
        }

    def validate_setup(self) -> dict:
        return {
            "valid": True,
            "deck_id": DECK_CONFIG["deck_id"],
            "slides_defined": self.list_slides()["total"] >= 6,
        }
