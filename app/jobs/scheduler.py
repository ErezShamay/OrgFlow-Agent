"""QC notification job registration.

The scheduler instance is shared with app/automation/scheduler.py via
app/scheduling/core.py - see that module's docstring for why this used to
be two independent BackgroundScheduler instances (a bug: QC notification
jobs registered here were on a scheduler that never got started).
"""
from zoneinfo import ZoneInfo

from app.jobs.qc_notification_jobs import (
    run_qc_notification_cycle,
)
from app.scheduling.core import scheduler

ISRAEL_TZ = ZoneInfo("Asia/Jerusalem")


def register_qc_notification_jobs() -> None:
    scheduler.add_job(
        run_qc_notification_cycle,
        "cron",
        hour=8,
        minute=0,
        timezone=ISRAEL_TZ,
        id="qc_notification_cycle",
        replace_existing=True,
        max_instances=1,
    )
