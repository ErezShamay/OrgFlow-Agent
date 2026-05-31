class AIExecutiveRecommendationsService:
    def generate_recommendations(
        self,
        portfolio_summary: dict,
        trend_analysis: dict,
        risk_analysis: dict,
        executive_kpis: dict,
    ) -> dict:
        recommendations = []

        if executive_kpis.get("critical_project_ratio", 0) > 0.2:
            recommendations.append({
                "priority": "HIGH",
                "category": "RISK",
                "title": "צמצום חשיפה לפרויקטים קריטיים",
                "message": (
                    "שיעור הפרויקטים הקריטיים גבוה מהסף המומלץ. "
                    "מומלץ להקצות משאבי בקרה מרכזיים."
                ),
            })

        if trend_analysis.get("dominant_trend") == "DECLINING":
            recommendations.append({
                "priority": "HIGH",
                "category": "TREND",
                "title": "התערבות מגמה שלילית",
                "message": (
                    "רוב הפרויקטים מציגים מגמת הידרדרות. "
                    "יש להפעיל סקירת תפעול שבועית מרוכזת."
                ),
            })

        high_risk_count = risk_analysis.get("distribution", {}).get("HIGH_RISK", 0)
        if high_risk_count > 0:
            recommendations.append({
                "priority": "CRITICAL",
                "category": "PREDICTION",
                "title": "טיפול מיידי בפרויקטים בסיכון גבוה",
                "message": (
                    f"זוהו {high_risk_count} פרויקטים בסיכון גבוה. "
                    "מומלץ לפתוח תוכנית התערבות תוך 48 שעות."
                ),
            })

        if executive_kpis.get("escalation_pressure", 0) > 8:
            recommendations.append({
                "priority": "MEDIUM",
                "category": "OPERATIONS",
                "title": "הפחתת לחץ הסלמות",
                "message": (
                    "עומס ההסלמות גבוה ביחס לתיק הפרויקטים. "
                    "מומלץ לבחון הקצאת בעלי תפקידים."
                ),
            })

        if not recommendations:
            recommendations.append({
                "priority": "LOW",
                "category": "STABILITY",
                "title": "שמירה על יציבות תיק",
                "message": (
                    "התיק התפעולי יציב. "
                    "מומלץ להמשיך מעקב שגרתי."
                ),
            })

        return {
            "recommendations": recommendations,
            "recommendation_count": len(recommendations),
            "top_priority": recommendations[0]["priority"],
        }
