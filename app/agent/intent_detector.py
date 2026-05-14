class IntentDetector:
    CHECK_MISSING_REPORTS = "CHECK_MISSING_REPORTS"
    SEND_REMINDERS = "SEND_REMINDERS"
    SUMMARIZE_PROJECT_STATUS = "SUMMARIZE_PROJECT_STATUS"
    FIND_REPORT = "FIND_REPORT"
    UNKNOWN = "UNKNOWN"

    def detect(self, user_request: str) -> dict:
        normalized_request = user_request.strip().lower()
        intents = []
        confidence = 0.0

        missing_report_keywords = [
            "חסרים דוח",
            "חסר דוח",
            "לא שלחו דוח",
            "מי לא שלח",
            "בדוק איזה פרויקטים חסרים"
        ]

        reminder_keywords = [
            "שלח תזכורת",
            "תזכורת למפקחים",
            "שלח להם תזכורת",
            "שלח מייל",
            "תזכיר"
        ]

        summary_keywords = [
            "סכם",
            "סטטוס",
            "סיכום"
        ]

        find_report_keywords = [
            "מצא",
            "דוח אחרון",
            "הדוח האחרון",
            "איפה הדוח",
            "תביא לי את הדוח",
            "מצא לי את הדוח"
        ]

        if any(keyword in normalized_request for keyword in missing_report_keywords):
            intents.append(self.CHECK_MISSING_REPORTS)
            confidence = max(confidence, 0.95)

        if any(keyword in normalized_request for keyword in reminder_keywords):
            intents.append(self.SEND_REMINDERS)
            confidence = max(confidence, 0.90)

        if any(keyword in normalized_request for keyword in summary_keywords):
            intents.append(self.SUMMARIZE_PROJECT_STATUS)
            confidence = max(confidence, 0.90)

        if any(keyword in normalized_request for keyword in find_report_keywords):
            intents.append(self.FIND_REPORT)
            confidence = max(confidence, 0.90)

        if not intents:
            intents.append(self.UNKNOWN)
            confidence = 0.0

        return {
            "intents": intents,
            "confidence": confidence,
            "source": "RULE_BASED"
        }