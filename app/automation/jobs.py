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

from app.services.circuit_breaker_service import (
    CircuitBreakerService
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

circuit_breaker_service = (
    CircuitBreakerService()
)

# ==========================================
# SLA MONITORING JOB
# ==========================================

def run_sla_monitoring():

    lock_key = (
        "sla_monitoring"
    )

    if not circuit_breaker_service.allow_request(
        lock_key
    ):

        print(
            "[CIRCUIT_BREAKER] "
            "Skipping SLA monitoring; "
            "breaker is open"
        )

        return

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

        circuit_breaker_service.record_success(
            lock_key
        )

    except Exception as error:

        print(
            "[AUTOMATION] "
            "SLA monitoring failed:",
            str(error),
        )

        circuit_breaker_service.record_failure(
            lock_key
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

    if not circuit_breaker_service.allow_request(
        lock_key
    ):

        print(
            "[CIRCUIT_BREAKER] "
            "Skipping AI automation; "
            "breaker is open"
        )

        return

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

        circuit_breaker_service.record_success(
            lock_key
        )

    except Exception as error:

        print(
            "[AI_AUTOMATION] "
            "AI automation failed:",
            str(error),
        )

        circuit_breaker_service.record_failure(
            lock_key
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

    if not circuit_breaker_service.allow_request(
        lock_key
    ):

        print(
            "[CIRCUIT_BREAKER] "
            "Skipping AI recovery; "
            "breaker is open"
        )

        return

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

        circuit_breaker_service.record_success(
            lock_key
        )

    except Exception as error:

        print(
            "[AI_RECOVERY] "
            "AI recovery failed:",
            str(error),
        )

        circuit_breaker_service.record_failure(
            lock_key
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
