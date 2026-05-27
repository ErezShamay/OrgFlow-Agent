class AIFailureClassificationService:

    # ==========================================
    # CLASSIFY FAILURE
    # ==========================================

    def classify_failure(
        self,
        error: Exception,
    ):

        error_text = (
            str(error)
            .lower()
        )

        # ======================================
        # TIMEOUT
        # ======================================

        if (
            "timeout" in error_text
            or "timed out" in error_text
        ):

            return {

                "failure_type":
                    "TIMEOUT",

                "severity":
                    "MEDIUM",

                "replayable":
                    True,
            }

        # ======================================
        # RATE LIMIT
        # ======================================

        if (
            "rate limit" in error_text
            or "429" in error_text
        ):

            return {

                "failure_type":
                    "RATE_LIMIT",

                "severity":
                    "LOW",

                "replayable":
                    True,
            }

        # ======================================
        # PERMISSION
        # ======================================

        if (
            "permission" in error_text
            or "unauthorized" in error_text
            or "forbidden" in error_text
        ):

            return {

                "failure_type":
                    "PERMISSION",

                "severity":
                    "HIGH",

                "replayable":
                    False,
            }

        # ======================================
        # DATA
        # ======================================

        if (
            "missing" in error_text
            or "invalid" in error_text
            or "not found" in error_text
        ):

            return {

                "failure_type":
                    "DATA_ERROR",

                "severity":
                    "HIGH",

                "replayable":
                    False,
            }

        # ======================================
        # DEFAULT
        # ======================================

        return {

            "failure_type":
                "UNKNOWN",

            "severity":
                "MEDIUM",

            "replayable":
                True,
        }