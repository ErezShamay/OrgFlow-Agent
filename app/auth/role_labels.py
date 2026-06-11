from __future__ import annotations

ROLE_LABELS_HE: dict[str, str] = {
    "PLATFORM_ADMIN": "מנהל גלובלי",
    "ADMIN": "מנהל לקוח",
    "SUPERVISOR": "מפקח",
    "CONTRACTOR": "קבלן",
    "DEVELOPER": "יזם",
    "VIEWER": "משתמש כללי",
    "MANAGER": "מנהל",
    "ANALYST": "אנליסט",
}

ROLE_DESCRIPTIONS_HE: dict[str, str] = {
    "PLATFORM_ADMIN": (
        "גישה לכל הלקוחות, יצירת לקוחות חדשים "
        "וניהול משתמשים בכל ארגון"
    ),
    "ADMIN": (
        "גישה רק ללקוח אחד, ניהול משתמשים "
        "והרשאות בתוך הארגון שלו בלבד"
    ),
    "SUPERVISOR": (
        "גישה לפרויקטים ודוחות, ללא הרשאות ניהול משתמשים"
    ),
    "CONTRACTOR": (
        "צפייה בליקויים פתוחים והגשת תיקון - ללא גישה לדוחות שטח או תיק QC"
    ),
    "DEVELOPER": (
        "תיק QC וליקויים לקריאה בלבד - ללא עריכת דוחות או ליקויים"
    ),
    "VIEWER": (
        "צפייה בפרויקטים ודוחות בלבד, ללא הרשאות ניהול"
    ),
}


def get_role_label(role: str | None) -> str:
    normalized = (role or "").strip().upper()
    return ROLE_LABELS_HE.get(normalized, normalized or "-")
