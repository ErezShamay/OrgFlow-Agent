from datetime import (
    datetime,
    timedelta,
    timezone,
)


class AIRetryStrategyService:

    # ==========================================
    # CALCULATE NEXT RETRY
    # ==========================================

    def calculate_next_retry(
        self,
        failure_type: str,
        retry_count: int,
    ):

        # ======================================
        # TIMEOUT
        # ======================================

        if failure_type == "TIMEOUT":

            delay_minutes = (
                1 * retry_count
            )

        # ======================================
        # RATE LIMIT
        # ======================================

        elif failure_type == "RATE_LIMIT":

            delay_minutes = (
                5 * retry_count
            )

        # ======================================
        # DATABASE
        # ======================================

        elif failure_type == "DATABASE":

            delay_minutes = (
                3 * retry_count
            )

        # ======================================
        # DEFAULT
        # ======================================

        else:

            delay_minutes = (
                2 * retry_count
            )

        return (

            datetime.now(
                timezone.utc
            )

            + timedelta(
                minutes=delay_minutes
            )
        )