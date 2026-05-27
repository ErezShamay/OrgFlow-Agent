class AIConfidenceService:

    # ==========================================
    # CALCULATE CONFIDENCE
    # ==========================================

    def calculate_confidence(
        self,
        health: dict,
        risk_analysis: dict,
    ):

        score = 100

        # ======================================
        # HEALTH STATUS
        # ======================================

        status = (
            health.get(
                "status"
            )
        )

        if status == "CRITICAL":

            score += 20

        elif status == "WARNING":

            score += 10

        # ======================================
        # HEALTH SCORE
        # ======================================

        health_score = (
            health.get(
                "score",
                100
            )
        )

        if health_score < 30:

            score += 25

        elif health_score < 50:

            score += 15

        # ======================================
        # RISK LEVEL
        # ======================================

        risk_level = (
            risk_analysis.get(
                "risk_level",
                "LOW"
            )
        )

        if risk_level == "HIGH":

            score += 25

        elif risk_level == "MEDIUM":

            score += 10

        # ======================================
        # CLAMP
        # ======================================

        score = min(
            score,
            100
        )

        return {

            "score":
                score,

            "confidence_level":
                self.get_confidence_level(
                    score
                ),
        }

    # ==========================================
    # GET LEVEL
    # ==========================================

    def get_confidence_level(
        self,
        score: int,
    ):

        if score >= 90:
            return "VERY_HIGH"

        if score >= 75:
            return "HIGH"

        if score >= 50:
            return "MEDIUM"

        return "LOW"