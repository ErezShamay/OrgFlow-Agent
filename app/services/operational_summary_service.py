import time

from app.ai.ai_client import (
    AIClient
)

from app.repositories.operational_action_repository import (
    OperationalActionRepository
)

from app.repositories.ai_interpretation_repository import (
    AIInterpretationRepository
)

_SUMMARY_CACHE_TTL_SECONDS = 300
_summary_cache: dict[str, tuple[float, dict]] = {}


class OperationalSummaryService:

    def __init__(self):

        self.action_repository = (
            OperationalActionRepository()
        )

        self.review_repository = (
            AIInterpretationRepository()
        )

    def generate_project_summary(
        self,
        project_id: str,
        actions: list | None = None,
        reviews: list | None = None,
    ):

        cached = _summary_cache.get(project_id)
        if cached:
            cached_at, payload = cached
            if (
                time.time() - cached_at
                < _SUMMARY_CACHE_TTL_SECONDS
            ):
                return payload

        if actions is None:
            actions = (
                self.action_repository
                .get_open_actions_by_project(
                    project_id
                )
            )

        if reviews is None:
            reviews = (
                self.review_repository
                .get_reviews_by_project(
                    project_id
                )
            )

        prompt = f"""
אתה מנהל תפעול בכיר בתחום הבנייה
וההתחדשות העירונית.

המטרה שלך היא לייצר
סיכום תפעולי קצר,
ברור ומקצועי למנהל פרויקט.

נתוני הפרויקט:

פעולות פתוחות:
{len(actions)}

ביקורות בינה מלאכותית:
{len(reviews)}

רשימת פעולות:
{actions}

רשימת ביקורות:
{reviews}

החזר תשובה בעברית בלבד.
אל תשתמש בקיצור «AI» באנגלית — כתוב «בינה מלאכותית».
כשמציג מספרים ליד תווית, כתוב למשל: «מספר ביקורות בינה מלאכותית: 3».

המבנה:

1. מצב הפרויקט
2. סיכונים מרכזיים
3. פעולות דחופות
4. המלצת ניהול
"""

        try:
            summary = (
                AIClient()
                .generate(
                    prompt,
                    prompt_name=
                        "project_operational_summary"
                )
            )
        except Exception:
            summary = (
                "סיכום בינה מלאכותית אינו זמין כרגע.\n\n"
                f"פעולות פתוחות: {len(actions)}\n"
                f"מספר ביקורות בינה מלאכותית: {len(reviews)}"
            )

        payload = {

            "project_id":
                project_id,

            "summary":
                summary,
        }

        _summary_cache[project_id] = (
            time.time(),
            payload,
        )

        return payload
