from apscheduler.schedulers.background import (
    BackgroundScheduler
)

from app.services.action_escalation_service import (
    ActionEscalationService
)

from app.jobs.qc_notification_jobs import (
    run_qc_notification_cycle,
)


scheduler = (
    BackgroundScheduler()
)


def run_escalations_job():

    print(
        "\nRUNNING AUTO ESCALATIONS\n"
    )

    result = (
        ActionEscalationService()
        .escalate_overdue_actions()
    )

    print(result)


def register_qc_notification_jobs() -> None:
    scheduler.add_job(
        run_qc_notification_cycle,
        "cron",
        hour=8,
        minute=0,
        id="qc_notification_cycle",
        replace_existing=True,
        max_instances=1,
    )


def start_scheduler():

    scheduler.add_job(

        run_escalations_job,

        trigger="interval",

        minutes=30,
    )

    register_qc_notification_jobs()

    scheduler.start()

    print(
        "\nSCHEDULER STARTED\n"
    )