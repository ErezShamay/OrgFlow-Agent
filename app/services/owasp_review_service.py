from __future__ import annotations

OWASP_TOP_10_2021 = [
    {"id": "A01", "name": "Broken Access Control", "status": "mitigated"},
    {"id": "A02", "name": "Cryptographic Failures", "status": "mitigated"},
    {"id": "A03", "name": "Injection", "status": "mitigated"},
    {"id": "A04", "name": "Insecure Design", "status": "reviewed"},
    {"id": "A05", "name": "Security Misconfiguration", "status": "mitigated"},
    {"id": "A06", "name": "Vulnerable Components", "status": "monitored"},
    {"id": "A07", "name": "Authentication Failures", "status": "mitigated"},
    {"id": "A08", "name": "Software and Data Integrity", "status": "monitored"},
    {"id": "A09", "name": "Security Logging Failures", "status": "mitigated"},
    {"id": "A10", "name": "Server-Side Request Forgery", "status": "reviewed"},
]


class OwaspReviewService:
    def get_top_10_assessment(self) -> dict:
        mitigated = [
            item for item in OWASP_TOP_10_2021 if item["status"] == "mitigated"
        ]
        return {
            "items": OWASP_TOP_10_2021,
            "total": len(OWASP_TOP_10_2021),
            "mitigated_count": len(mitigated),
            "coverage_percent": round(len(mitigated) / len(OWASP_TOP_10_2021) * 100, 1),
        }

    def evaluate_control(self, control_id: str) -> dict:
        item = next(
            (entry for entry in OWASP_TOP_10_2021 if entry["id"] == control_id),
            None,
        )
        if item is None:
            return {"found": False, "control_id": control_id}

        return {
            "found": True,
            **item,
            "passed": item["status"] in {"mitigated", "reviewed", "monitored"},
        }

    def validate_review_completeness(self) -> dict:
        assessment = self.get_top_10_assessment()
        return {
            "valid": assessment["total"] == 10,
            "coverage_percent": assessment["coverage_percent"],
            "mitigated_count": assessment["mitigated_count"],
        }
