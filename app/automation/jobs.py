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

from app.services.automation_run_service import (
    AutomationRunService
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

automation_run_service = (
    AutomationRunService()
)

circuit_breaker_service = (
    CircuitBreakerService()
)

# ==========================================
# JOB RUNNER
# ==========================================

def run_automation_job(
    job_name: str,
    log_prefix: str,
    handler,
):

    if not circuit_breaker_service.allow_request(
        job_name
    ):

        print(
            "[CIRCUIT_BREAKER] "
            f"Skipping {job_name}; "
            "breaker is open",
        )

        automation_run_service.skip_run(

            job_name=job_name,

            reason="CIRCUIT_BREAKER_OPEN",

            metadata={
                "job_type":
                    job_name.upper()
            },
        )

        return

    acquired = (
        automation_lock_service
        .acquire_lock(
            job_name
        )
    )

    if not acquired:

        automation_run_service.skip_run(

            job_name=job_name,

            reason="LOCK_NOT_ACQUIRED",

            metadata={
                "job_type":
                    job_name.upper()
            },
        )

        return

    run_id = (
        automation_run_service
        .start_run(

            job_name=job_name,

            metadata={
                "job_type":
                    job_name.upper()
            },
        )
    )

    try:

        print(
            f"[{log_prefix}] "
            f"Running {job_name} cycle..."
        )

        result = (
            handler()
            or {}
        )

        metadata = (
            result.get(
                "metadata"
            )
            or {}
        )

        metadata["job_type"] = (
            job_name.upper()
        )

        automation_run_service.complete_run(

            run_id=run_id,

            processed_count=result.get(
                "processed_count",
                0,
            ),

            error_count=result.get(
                "error_count",
                0,
            ),

            metadata=metadata,
        )

        circuit_breaker_service.record_success(
            job_name
        )

    except Exception as error:

        print(
            f"[{log_prefix}] "
            f"{job_name} failed:",
            str(error),
        )

        automation_run_service.fail_run(

            run_id=run_id,

            error=error,

            metadata={
                "job_type":
                    job_name.upper()
            },
        )

        circuit_breaker_service.record_failure(
            job_name
        )

    finally:

        automation_lock_service.release_lock(
            job_name
        )

# ==========================================
# SLA MONITORING JOB
# ==========================================

def run_sla_monitoring():

    run_automation_job(

        job_name="sla_monitoring",

        log_prefix="AUTOMATION",

        handler=sla_monitoring_service.run_monitoring_cycle,
    )

# ==========================================
# AI AUTOMATION JOB
# ==========================================

def run_ai_automation():

    run_automation_job(

        job_name="ai_automation",

        log_prefix="AI_AUTOMATION",

        handler=ai_automation_service.run_analysis_cycle,
    )

# ==========================================
# AI RECOVERY JOB
# ==========================================

def run_ai_recovery():

    run_automation_job(

        job_name="ai_recovery",

        log_prefix="AI_RECOVERY",

        handler=ai_recovery_service.run_recovery_cycle,
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
