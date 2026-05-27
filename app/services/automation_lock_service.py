from uuid import uuid4

from datetime import (
    datetime,
    timedelta,
    timezone,
)

from app.schemas.automation_lock import (
    AutomationLock
)

from app.repositories.automation_lock_repository import (
    AutomationLockRepository
)


class AutomationLockService:

    def __init__(self):

        self.repository = (
            AutomationLockRepository()
        )

    # ==========================================
    # ACQUIRE LOCK
    # ==========================================

    def acquire_lock(
        self,
        lock_key: str,
        ttl_minutes: int = 10,
    ):

        existing_lock = (
            self.repository
            .get_lock(
                lock_key
            )
        )

        # ======================================
        # ACTIVE LOCK EXISTS
        # ======================================

        if existing_lock:

            is_expired = (
                self.repository
                .is_lock_expired(
                    existing_lock
                )
            )

            if not is_expired:

                print(
                    "[AUTOMATION_LOCK] "
                    f"Lock already active: "
                    f"{lock_key}"
                )

                return False

            # ==================================
            # CLEAN EXPIRED LOCK
            # ==================================

            self.repository.delete_lock(
                lock_key
            )

        # ======================================
        # CREATE NEW LOCK
        # ======================================

        now = (
            datetime.now(
                timezone.utc
            )
        )

        expires_at = (
            now
            + timedelta(
                minutes=ttl_minutes
            )
        )

        lock = AutomationLock(

            id=str(uuid4()),

            lock_key=
                lock_key,

            created_at=
                now,

            expires_at=
                expires_at,
        )

        self.repository.create_lock(
            lock
        )

        print(
            "[AUTOMATION_LOCK] "
            f"Lock acquired: "
            f"{lock_key}"
        )

        return True

    # ==========================================
    # RELEASE LOCK
    # ==========================================

    def release_lock(
        self,
        lock_key: str,
    ):

        self.repository.delete_lock(
            lock_key
        )

        print(
            "[AUTOMATION_LOCK] "
            f"Lock released: "
            f"{lock_key}"
        )