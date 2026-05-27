from app.services.portfolio_insights_service import (
    PortfolioInsightsService
)


class AlertEngineService:

    def __init__(self):

        self.portfolio_service = (
            PortfolioInsightsService()
        )

    def generate_alerts(
        self,
    ):

        portfolio = (
            self.portfolio_service
            .generate_portfolio_summary()
        )

        alerts = []

        for project in portfolio["projects"]:

            prediction = (
                project["prediction"]
            )

            health = (
                project["health"]
            )

            # =========================
            # HIGH RISK
            # =========================

            if (
                prediction[
                    "prediction"
                ]
                == "HIGH_RISK"
            ):

                alerts.append({

                    "severity":
                        "CRITICAL",

                    "project_id":
                        project[
                            "project_id"
                        ],

                    "project_name":
                        project[
                            "project_name"
                        ],

                    "title":
                        "סיכון הידרדרות גבוה",

                    "message":
                        prediction[
                            "message"
                        ],
                })

            # =========================
            # LOW HEALTH
            # =========================

            if (
                health["score"]
                < 40
            ):

                alerts.append({

                    "severity":
                        "HIGH",

                    "project_id":
                        project[
                            "project_id"
                        ],

                    "project_name":
                        project[
                            "project_name"
                        ],

                    "title":
                        "Health Score נמוך",

                    "message":
                        "הפרויקט נמצא במצב תפעולי מסוכן",
                })

        return {

            "alerts":
                alerts,

            "total_alerts":
                len(alerts),
        }