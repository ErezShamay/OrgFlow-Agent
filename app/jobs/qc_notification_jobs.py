"""QC notification jobs - roadmap 4.3 (uses NotificationTool, not automation engine)."""

from __future__ import annotations

from app.config.settings import settings
from app.repositories.organization_repository import OrganizationRepository
from app.services.qc_notification_service import QcNotificationService


def run_qc_notification_cycle() -> dict:
    """Daily job: run all QC email alerts for every organization."""
    if not settings.FEATURE_FLAGS.enable_email_delivery:
        return {
            "status": "SKIPPED",
            "reason": "email_delivery_disabled",
            "organizations_processed": 0,
        }

    service = QcNotificationService()
    organization_repository = OrganizationRepository()
    organizations = organization_repository.get_all_organizations()

    results = []
    for organization in organizations:
        organization_id = str(organization.get("id") or "")
        if not organization_id:
            continue
        result = service.run_for_organization(
            organization_id=organization_id,
            send_email=True,
        )
        results.append(result.model_dump(mode="json"))

    sent_count = sum(result.get("total_emails_sent", 0) for result in results)

    return {
        "status": "COMPLETED",
        "organizations_processed": len(results),
        "emails_sent": sent_count,
        "results": results,
    }


def run_critical_stale_alert_job() -> dict:
    """Backward-compatible wrapper - prefer run_qc_notification_cycle."""
    if not settings.FEATURE_FLAGS.enable_email_delivery:
        return {
            "status": "SKIPPED",
            "reason": "email_delivery_disabled",
            "organizations_processed": 0,
        }

    service = QcNotificationService()
    organization_repository = OrganizationRepository()
    organizations = organization_repository.get_all_organizations()

    results = []
    for organization in organizations:
        organization_id = str(organization.get("id") or "")
        if not organization_id:
            continue
        result = service.run_critical_stale_for_organization(
            organization_id=organization_id,
            send_email=True,
        )
        results.append(result.model_dump(mode="json"))

    sent_count = sum(
        1
        for result in results
        for delivery in result.get("deliveries", [])
        if delivery.get("status") == "SENT"
    )

    return {
        "status": "COMPLETED",
        "organizations_processed": len(results),
        "emails_sent": sent_count,
        "results": results,
    }


def run_open_report_reminder_job() -> dict:
    """Backward-compatible wrapper - prefer run_qc_notification_cycle."""
    if not settings.FEATURE_FLAGS.enable_email_delivery:
        return {
            "status": "SKIPPED",
            "reason": "email_delivery_disabled",
            "organizations_processed": 0,
        }

    service = QcNotificationService()
    organization_repository = OrganizationRepository()
    organizations = organization_repository.get_all_organizations()

    results = []
    for organization in organizations:
        organization_id = str(organization.get("id") or "")
        if not organization_id:
            continue
        result = service.run_open_reports_for_organization(
            organization_id=organization_id,
            send_email=True,
        )
        results.append(result.model_dump(mode="json"))

    sent_count = sum(
        1
        for result in results
        for delivery in result.get("deliveries", [])
        if delivery.get("status") == "SENT"
    )

    return {
        "status": "COMPLETED",
        "organizations_processed": len(results),
        "emails_sent": sent_count,
        "results": results,
    }
