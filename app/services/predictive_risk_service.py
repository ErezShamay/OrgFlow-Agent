class PredictiveRiskService:

    @staticmethod
    def predict_project_risk(
        workspace: dict,
    ):

        health = (
            workspace["health"]
        )

        summary = (
            workspace["summary"]
        )

        risk_score = 0

        # =========================
        # HEALTH SCORE
        # =========================

        if (
            health["score"] < 50
        ):

            risk_score += 40

        elif (
            health["score"] < 80
        ):

            risk_score += 20

        # =========================
        # ESCALATIONS
        # =========================

        escalations = (
            summary[
                "escalations_count"
            ]
        )

        risk_score += (
            escalations * 10
        )

        # =========================
        # OPEN ACTIONS
        # =========================

        actions = (
            summary[
                "actions_count"
            ]
        )

        risk_score += (
            actions * 2
        )

        # =========================
        # PREDICTION
        # =========================

        if risk_score >= 70:

            prediction = (
                "HIGH_RISK"
            )

            message = (
                "הפרויקט צפוי להידרדר בטווח הקרוב"
            )

        elif risk_score >= 40:

            prediction = (
                "MEDIUM_RISK"
            )

            message = (
                "נדרשת בקרה מוגברת בפרויקט"
            )

        else:

            prediction = (
                "LOW_RISK"
            )

            message = (
                "הפרויקט יציב בשלב זה"
            )

        return {

            "prediction":
                prediction,

            "risk_score":
                risk_score,

            "message":
                message,
        }

    @staticmethod
    def analyze_portfolio(portfolio_summary: dict) -> dict:
        projects = portfolio_summary.get("projects", [])
        distribution = {
            "HIGH_RISK": 0,
            "MEDIUM_RISK": 0,
            "LOW_RISK": 0,
        }
        total_risk_score = 0
        high_risk_projects = []

        for project in projects:
            prediction = project["prediction"]["prediction"]
            distribution[prediction] = distribution.get(prediction, 0) + 1
            total_risk_score += project["prediction"]["risk_score"]

            if prediction == "HIGH_RISK":
                high_risk_projects.append({
                    "project_id": project["project_id"],
                    "project_name": project["project_name"],
                    "risk_score": project["prediction"]["risk_score"],
                })

        average_risk_score = 0
        if projects:
            average_risk_score = round(total_risk_score / len(projects), 2)

        if average_risk_score >= 70:
            portfolio_risk_level = "HIGH"
        elif average_risk_score >= 40:
            portfolio_risk_level = "MEDIUM"
        else:
            portfolio_risk_level = "LOW"

        return {
            "portfolio_risk_level": portfolio_risk_level,
            "average_risk_score": average_risk_score,
            "distribution": distribution,
            "high_risk_projects": high_risk_projects,
        }