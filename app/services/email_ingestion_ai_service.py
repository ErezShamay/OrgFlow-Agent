from __future__ import annotations

EMAIL_INGESTION_AI_CONFIG = {
    "pipeline_id": "orgflow_email_ingest_v1",
    "parsers": ["pdf_attachment", "inline_body", "thread_context"],
    "auto_classify": True,
}


class EmailIngestionAiService:
    def get_config(self) -> dict:
        return EMAIL_INGESTION_AI_CONFIG

    def process_message(self, *, has_attachment: bool = True, subject: str = "Q1 report") -> dict:
        return {
            "ingested": True,
            "classification": "report" if has_attachment else "general",
            "subject": subject,
            "routed_to_project": has_attachment,
        }

    def list_parsers(self) -> dict:
        parsers = EMAIL_INGESTION_AI_CONFIG["parsers"]
        return {"parsers": parsers, "total": len(parsers)}

    def validate_setup(self) -> dict:
        return {
            "valid": True,
            "parsers_defined": self.list_parsers()["total"] >= 3,
        }
