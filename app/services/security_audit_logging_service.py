from __future__ import annotations

from app.services.audit_table_service import AuditTableService

SECURITY_AUDIT_EVENTS = [
    "LOGIN_SUCCESS",
    "LOGIN_FAILURE",
    "PERMISSION_DENIED",
    "IMPERSONATION_START",
    "IMPERSONATION_END",
    "SECRET_ROTATION",
    "RATE_LIMIT_EXCEEDED",
    "MALWARE_DETECTED",
    "FILE_UPLOAD_REJECTED",
]


class SecurityAuditLoggingService:
    def __init__(
        self,
        audit_table_service: AuditTableService | None = None,
    ):
        self.audit_table_service = audit_table_service or AuditTableService()

    def get_event_catalog(self) -> dict:
        return {
            "events": SECURITY_AUDIT_EVENTS,
            "total": len(SECURITY_AUDIT_EVENTS),
        }

    def record_security_event(
        self,
        *,
        event_type: str,
        actor_id: str | None = None,
        organization_id: str | None = None,
        metadata: dict | None = None,
    ) -> dict:
        if event_type not in SECURITY_AUDIT_EVENTS:
            return {
                "recorded": False,
                "reason": "UNKNOWN_EVENT_TYPE",
                "event_type": event_type,
            }

        entry = self.audit_table_service.record_change(
            table_name="security_events",
            record_id=event_type,
            action=event_type,
            organization_id=organization_id,
            actor_id=actor_id,
            after=metadata or {},
        )
        return {
            "recorded": entry.get("recorded", False),
            "event_type": event_type,
            "entry": entry.get("entry"),
        }

    def get_audit_coverage(self) -> dict:
        tables = self.audit_table_service.get_audited_tables()
        return {
            "audited_tables": tables,
            "security_events": self.get_event_catalog(),
        }

    def validate_setup(self) -> dict:
        coverage = self.get_audit_coverage()
        return {
            "valid": coverage["audited_tables"]["count"] > 0,
            "audited_table_count": coverage["audited_tables"]["count"],
            "security_event_count": coverage["security_events"]["total"],
        }
