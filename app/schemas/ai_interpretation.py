import json

from datetime import datetime

from pydantic import BaseModel


class AIInterpretation(BaseModel):

    finding_id: str

    model_name: str

    business_impact: str

    tenant_risk: str

    recommended_action: str

    raw_response: str

    review_status: str = "PENDING"

    reviewed_by: str | None = None

    reviewed_at: datetime | None = None

    review_notes: str | None = None

    created_at: datetime | None = None

    @classmethod
    def from_ai_response(
        cls,
        finding_id: str,
        model_name: str,
        raw_response: str,
    ):

        try:

            start = (
                raw_response.find("{")
            )

            end = (
                raw_response.rfind("}")
            )

            cleaned_response = (
                raw_response[
                    start:end + 1
                ]
            )

            parsed = json.loads(
                cleaned_response
            )

            return cls(

                finding_id=
                    finding_id,

                model_name=
                    model_name,

                business_impact=
                    parsed.get(
                        "business_impact",
                        "לא זוהה"
                    ),

                tenant_risk=
                    parsed.get(
                        "tenant_risk",
                        "לא זוהה"
                    ),

                recommended_action=
                    parsed.get(
                        "recommended_action",
                        "נדרשת בדיקה ידנית"
                    ),

                raw_response=
                    raw_response,
            )

        except Exception:

            return cls(

                finding_id=
                    finding_id,

                model_name=
                    model_name,

                business_impact=
                    "נדרשת בדיקה ידנית",

                tenant_risk=
                    "לא זוהה",

                recommended_action=
                    "יש לבצע בדיקה ידנית של הממצא",

                raw_response=
                    raw_response,
            )