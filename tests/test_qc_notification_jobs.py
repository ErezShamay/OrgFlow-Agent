"""QC notification jobs - scheduler wiring tests."""

from __future__ import annotations

from unittest.mock import patch

from app.jobs.qc_notification_jobs import (
    run_critical_stale_alert_job,
    run_open_report_reminder_job,
    run_qc_notification_cycle,
)


def test_run_qc_notification_cycle_skips_when_email_disabled() -> None:
    with patch(
        "app.jobs.qc_notification_jobs.settings"
    ) as mock_settings:
        mock_settings.FEATURE_FLAGS.enable_email_delivery = False
        result = run_qc_notification_cycle()

    assert result["status"] == "SKIPPED"
    assert result["organizations_processed"] == 0


def test_run_critical_stale_alert_job_skips_when_email_disabled() -> None:
    with patch(
        "app.jobs.qc_notification_jobs.settings"
    ) as mock_settings:
        mock_settings.FEATURE_FLAGS.enable_email_delivery = False
        result = run_critical_stale_alert_job()

    assert result["status"] == "SKIPPED"
    assert result["organizations_processed"] == 0


def test_run_open_report_reminder_job_skips_when_email_disabled() -> None:
    with patch(
        "app.jobs.qc_notification_jobs.settings"
    ) as mock_settings:
        mock_settings.FEATURE_FLAGS.enable_email_delivery = False
        result = run_open_report_reminder_job()

    assert result["status"] == "SKIPPED"
    assert result["organizations_processed"] == 0
