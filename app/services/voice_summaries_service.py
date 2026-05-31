from __future__ import annotations

VOICE_SUMMARIES_CONFIG = {
    "provider": "elevenlabs",
    "default_voice": "executive_neutral",
    "max_duration_seconds": 180,
    "formats": ["mp3", "ogg"],
}


class VoiceSummariesService:
    def get_config(self) -> dict:
        return VOICE_SUMMARIES_CONFIG

    def synthesize(self, *, text_length: int = 500) -> dict:
        duration = min(text_length // 3, VOICE_SUMMARIES_CONFIG["max_duration_seconds"])
        return {
            "synthesized": text_length > 0,
            "duration_seconds": duration,
            "format": "mp3",
        }

    def list_voices(self) -> dict:
        voices = ["executive_neutral", "warm_briefing", "urgent_alert"]
        return {"voices": voices, "total": len(voices)}

    def validate_setup(self) -> dict:
        return {
            "valid": True,
            "voices_defined": self.list_voices()["total"] >= 3,
        }
