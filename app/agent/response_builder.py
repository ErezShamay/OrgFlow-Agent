class ResponseBuilder:
    def success(
        self,
        summary: str,
        detected_intents: list[str],
        actions: list[str],
        execution_plan: dict | None = None,
        extra: dict | None = None
    ) -> dict:
        response = {
            "status": "SUCCESS",
            "detected_intents": detected_intents,
            "execution_plan": execution_plan,
            "summary": summary,
            "actions": actions
        }

        if extra:
            response.update(extra)

        return response

    def failed(
        self,
        summary: str,
        detected_intents: list[str],
        actions: list[str] | None = None,
        execution_plan: dict | None = None,
        extra: dict | None = None
    ) -> dict:
        response = {
            "status": "FAILED",
            "detected_intents": detected_intents,
            "execution_plan": execution_plan,
            "summary": summary,
            "actions": actions or []
        }

        if extra:
            response.update(extra)

        return response

    def needs_clarification(
        self,
        summary: str,
        detected_intents: list[str],
        next_step: str,
        actions: list[str] | None = None,
        execution_plan: dict | None = None,
        extra: dict | None = None
    ) -> dict:
        response = {
            "status": "NEEDS_CLARIFICATION",
            "detected_intents": detected_intents,
            "execution_plan": execution_plan,
            "summary": summary,
            "actions": actions or [],
            "next_step": next_step
        }

        if extra:
            response.update(extra)

        return response

    def waiting_for_confirmation(
        self,
        run_id: str,
        summary: str,
        detected_intents: list[str],
        confirmation_message: str,
        actions: list[str],
        execution_plan: dict | None = None,
        extra: dict | None = None
    ) -> dict:
        response = {
            "run_id": run_id,
            "status": "WAITING_FOR_CONFIRMATION",
            "detected_intents": detected_intents,
            "execution_plan": execution_plan,
            "summary": summary,
            "actions": actions,
            "confirmation_required": True,
            "confirmation_message": confirmation_message
        }

        if extra:
            response.update(extra)

        return response