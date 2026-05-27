from datetime import datetime
from datetime import timezone
from uuid import uuid4

from app.repositories.automation_run_repository import (
    AutomationRunRepository
)

from app.schemas.automation_run import (
    AutomationRun
)


class AutomationRunService:

    def __init__(
        self,
    ):

        self.repository = (
            AutomationRunRepository()
        )

    def start_run(
        self,
        job_name: str,
        metadata: dict | None = None,
    ):

        run_id = (
            str(uuid4())
        )

        run = AutomationRun(

            id=run_id,

            job_name=job_name,

            started_at=datetime.now(
                timezone.utc
            ),

            status="RUNNING",

            metadata=metadata,
        )

        self.repository.create_run(
            run
        )

        return run_id

    def complete_run(
        self,
        run_id: str,
        processed_count: int = 0,
        error_count: int = 0,
        metadata: dict | None = None,
    ):

        payload = {

            "completed_at":
                datetime.now(
                    timezone.utc
                ).isoformat(),

            "status":
                (
                    "COMPLETED"
                    if error_count == 0
                    else "COMPLETED_WITH_ERRORS"
                ),

            "processed_count":
                processed_count,

            "error_count":
                error_count,
        }

        if metadata is not None:

            payload["metadata"] = metadata

        return self.repository.update_run(
            run_id,
            payload,
        )

    def fail_run(
        self,
        run_id: str,
        error: Exception,
        metadata: dict | None = None,
    ):

        run_metadata = (
            metadata.copy()
            if metadata
            else {}
        )

        run_metadata["error"] = (
            str(error)
        )

        return self.repository.update_run(

            run_id,

            {
                "completed_at":
                    datetime.now(
                        timezone.utc
                    ).isoformat(),

                "status":
                    "FAILED",

                "error_count":
                    1,

                "metadata":
                    run_metadata,
            },
        )

    def skip_run(
        self,
        job_name: str,
        reason: str,
        metadata: dict | None = None,
    ):

        run_metadata = (
            metadata.copy()
            if metadata
            else {}
        )

        run_metadata["skip_reason"] = (
            reason
        )

        now = datetime.now(
            timezone.utc
        )

        run = AutomationRun(

            id=str(uuid4()),

            job_name=job_name,

            started_at=now,

            completed_at=now,

            status="SKIPPED",

            metadata=run_metadata,
        )

        return self.repository.create_run(
            run
        )
