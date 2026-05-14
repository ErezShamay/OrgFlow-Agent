from app.agent.intent_detector import IntentDetector


def test_detect_check_missing_reports():
    detector = IntentDetector()

    result = detector.detect("בדוק איזה פרויקטים חסרים דוח השבוע")

    assert IntentDetector.CHECK_MISSING_REPORTS in result["intents"]
    assert result["source"] == "RULE_BASED"


def test_detect_send_reminders():
    detector = IntentDetector()

    result = detector.detect("שלח תזכורת למפקחים שלא שלחו דוח")

    assert IntentDetector.SEND_REMINDERS in result["intents"]
    assert result["source"] == "RULE_BASED"


def test_detect_find_report():
    detector = IntentDetector()

    result = detector.detect("מצא לי את הדוח האחרון של פרויקט מגדלי הצפון")

    assert IntentDetector.FIND_REPORT in result["intents"]
    assert result["source"] == "RULE_BASED"


def test_detect_summary():
    detector = IntentDetector()

    result = detector.detect("סכם לי את הסטטוס של פרויקט מגדלי הצפון")

    assert IntentDetector.SUMMARIZE_PROJECT_STATUS in result["intents"]
    assert result["source"] == "RULE_BASED"