from app.automation.scheduler import (
    scheduler
)

from app.services.sla_monitoring_service import (
    SLAMonitoringService
)

from app.services.ai_automation_service import (
    AIAutomationService
)

from app.services.ai_recovery_service import (
    AIRecoveryService
)

from app.services.automation_lock_service import (
    AutomationLockService
)

# ==========================================
# SERVICES
# ==========================================

sla_monitoring_service = (
    SLAMonitoringService()
)

ai_automation_service = (
    AIAutomationService()
)

ai_recovery_service = (
    AIRecoveryService()
)

automation_lock_service = (
    AutomationLockService()
)

# ==========================================
# SLA MONITORING JOB
# ==========================================

def run_sla_monitoring():

    lock_key = (
        "sla_monitoring"
    )

    acquired = (
        automation_lock_service
        .acquire_lock(
            lock_key
        )
    )

    if not acquired:

        return

    try:

        print(
            "[AUTOMATION] "
            "Running SLA monitoring cycle..."
        )

        sla_monitoring_service.run_monitoring_cycle()

    except Exception as error:

        print(
            "[AUTOMATION] "
            "SLA monitoring failed:",
            str(error),
        )

    finally:

        automation_lock_service.release_lock(
            lock_key
        )

# ==========================================
# AI AUTOMATION JOB
# ==========================================

def run_ai_automation():

    lock_key = (
        "ai_automation"
    )

    acquired = (
        automation_lock_service
        .acquire_lock(
            lock_key
        )
    )

    if not acquired:

        return

    try:

        print(
            "[AI_AUTOMATION] "
            "Running AI automation cycle..."
        )

        ai_automation_service.run_analysis_cycle()

    except Exception as error:

        print(
            "[AI_AUTOMATION] "
            "AI automation failed:",
            str(error),
        )

    finally:

        automation_lock_service.release_lock(
            lock_key
        )

# ==========================================
# AI RECOVERY JOB
# ==========================================

def run_ai_recovery():

    lock_key = (
        "ai_recovery"
    )

    acquired = (
        automation_lock_service
        .acquire_lock(
            lock_key
        )
    )

    if not acquired:

        return

    try:

        print(
            "[AI_RECOVERY] "
            "Running AI recovery cycle..."
        )

        ai_recovery_service.run_recovery_cycle()

    except Exception as error:

        print(
            "[AI_RECOVERY] "
            "AI recovery failed:",
            str(error),
        )

    finally:

        automation_lock_service.release_lock(
            lock_key
        )

# ==========================================
# REGISTER JOBS
# ==========================================

def register_automation_jobs():

    scheduler.add_job(

        run_sla_monitoring,

        "interval",

        minutes=5,

        id="sla_monitoring",

        replace_existing=True,

        max_instances=1,
    )

    scheduler.add_job(

        run_ai_automation,

        "interval",

        minutes=15,

        id="ai_automation",

        replace_existing=True,

        max_instances=1,
    )

    scheduler.add_job(

        run_ai_recovery,

        "interval",

        minutes=3,

        id="ai_recovery",

        replace_existing=True,

        max_instances=1,
    )

    print(
        "[AUTOMATION] Jobs registered"
    )
