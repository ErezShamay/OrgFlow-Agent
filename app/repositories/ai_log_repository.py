import logging
import re
from datetime import datetime

from postgrest.exceptions import APIError

from app.db.supabase_client import (
    supabase
)
from app.repositories.postgrest_errors import (
    is_invalid_uuid_error,
    is_missing_column_error,
)

logger = logging.getLogger(__name__)

AI_LOG_COLUMNS = frozenset({
    "provider",
    "model_name",
    "prompt_name",
    "prompt",
    "response",
    "success",
    "error_message",
    "duration_ms",
    "prompt_tokens",
    "completion_tokens",
    "cache_hit",
    "confidence_score",
    "hallucination_risk",
    "governance",
    "replay_token",
    "organization_id",
    "project_id",
})

# Older Supabase deployments may not have runtime-metadata columns yet.
AI_LOG_LEGACY_COLUMNS = frozenset({
    "provider",
    "model_name",
    "prompt_name",
    "prompt",
    "response",
    "success",
    "error_message",
    "duration_ms",
})


def _is_missing_column_error(exc: Exception) -> bool:
    message = str(exc)
    return (
        "PGRST204" in message
        or "Could not find the" in message
        and "column of 'ai_logs'" in message
    )


_EMPTY_SCOPE_ID = "00000000-0000-0000-0000-000000000000"


class AILogRepository:

    def __init__(self) -> None:
        self._supports_organization_id_column: bool | None = None
        self._supports_project_id_column: bool | None = None

    def _supports_organization_scope(self) -> bool:
        if self._supports_organization_id_column is not None:
            return self._supports_organization_id_column

        try:
            (
                supabase
                .table("ai_logs")
                .select("organization_id")
                .limit(1)
                .execute()
            )
            self._supports_organization_id_column = True
        except APIError as error:
            if is_missing_column_error(error, "organization_id"):
                self._supports_organization_id_column = False
            else:
                raise

        return self._supports_organization_id_column

    def _supports_project_scope(self) -> bool:
        if self._supports_project_id_column is not None:
            return self._supports_project_id_column

        try:
            (
                supabase
                .table("ai_logs")
                .select("project_id")
                .limit(1)
                .execute()
            )
            self._supports_project_id_column = True
        except APIError as error:
            if is_missing_column_error(error, "project_id"):
                self._supports_project_id_column = False
            else:
                raise

        return self._supports_project_id_column

    def _apply_organization_scope(
        self,
        request,
        organization_id: str | None,
        project_ids: list[str] | None = None,
    ):
        if not organization_id:
            return request

        scoped_project_ids = [
            project_id
            for project_id in (project_ids or [])
            if project_id
        ]

        if not self._supports_organization_scope():
            if scoped_project_ids and self._supports_project_scope():
                return request.in_(
                    "project_id",
                    scoped_project_ids,
                )
            return request.eq(
                "id",
                _EMPTY_SCOPE_ID,
            )

        if scoped_project_ids and self._supports_project_scope():
            return request.or_(
                f"organization_id.eq.{organization_id},"
                f"project_id.in.({','.join(scoped_project_ids)})"
            )

        return request.eq(
            "organization_id",
            organization_id,
        )

    def list_recent_for_scope(
        self,
        *,
        limit: int = 100,
        organization_id: str | None = None,
        project_ids: list[str] | None = None,
    ) -> list[dict]:
        request = (
            supabase
            .table("ai_logs")
            .select("*")
            .order("created_at", desc=True)
            .limit(limit)
        )
        request = self._apply_organization_scope(
            request,
            organization_id,
            project_ids,
        )

        try:
            response = request.execute()
        except APIError as error:
            if is_invalid_uuid_error(error):
                return []
            raise

        return response.data or []

    def list_for_usage_summary(
        self,
        *,
        since: datetime | None = None,
        limit: int = 20000,
    ) -> list[dict]:
        columns = (
            "organization_id,project_id,prompt_name,model_name,"
            "prompt_tokens,completion_tokens,cache_hit,success,created_at"
        )
        request = (
            supabase
            .table("ai_logs")
            .select(columns)
            .order("created_at", desc=True)
            .limit(limit)
        )

        if since is not None:
            request = request.gte(
                "created_at",
                since.isoformat(),
            )

        try:
            response = request.execute()
        except APIError as error:
            if is_invalid_uuid_error(error):
                return []
            raise

        return response.data or []

    @staticmethod
    def create_log(
        log_data: dict
    ):
        payload = {
            key: value
            for key, value in log_data.items()
            if key in AI_LOG_COLUMNS
        }

        try:
            supabase.table("ai_logs").insert(payload).execute()
            return
        except Exception as exc:
            if not _is_missing_column_error(exc):
                logger.warning("Failed to write ai_log: %s", exc)
                return

            missing_columns = re.findall(
                r"Could not find the '([^']+)' column of 'ai_logs'",
                str(exc),
            )
            legacy_payload = {
                key: value
                for key, value in payload.items()
                if key in AI_LOG_LEGACY_COLUMNS
                and key not in missing_columns
            }

            try:
                supabase.table("ai_logs").insert(legacy_payload).execute()
            except Exception as legacy_exc:
                logger.warning(
                    "Failed to write ai_log after column fallback: %s",
                    legacy_exc,
                )

    @staticmethod
    def create_review_audit_log(
        interpretation_id: str,
        event_type: str,
        actor: str | None = None,
        details: dict | None = None,
    ):
        payload = {
            "provider":
                "internal",
            "model_name":
                "review-audit",
            "prompt_name":
                f"REVIEW_AUDIT:{interpretation_id}",
            "prompt":
                event_type,
            "response":
                str(details or {}),
            "success":
                True,
            "error_message":
                None,
        }

        if actor:
            payload["response"] = str({
                **(details or {}),
                "actor": actor,
            })

        AILogRepository.create_log(payload)

    @staticmethod
    def list_review_audit_logs(
        interpretation_id: str
    ):
        response = (
            supabase
            .table("ai_logs")
            .select("*")
            .eq(
                "prompt_name",
                f"REVIEW_AUDIT:{interpretation_id}"
            )
            .order(
                "created_at",
                desc=False
            )
            .execute()
        )

        return (
            response.data
            or []
        )

    @staticmethod
    def create_review_comment(
        interpretation_id: str,
        author: str,
        comment: str,
    ):
        payload = {
            "provider": "internal",
            "model_name": "review-comment",
            "prompt_name": f"REVIEW_COMMENT:{interpretation_id}",
            "prompt": author,
            "response": comment,
            "success": True,
            "error_message": None,
        }
        AILogRepository.create_log(payload)

    @staticmethod
    def list_review_comments(
        interpretation_id: str
    ):
        response = (
            supabase
            .table("ai_logs")
            .select("*")
            .eq(
                "prompt_name",
                f"REVIEW_COMMENT:{interpretation_id}"
            )
            .order(
                "created_at",
                desc=False
            )
            .execute()
        )
        return response.data or []

    @staticmethod
    def create_review_notification(
        interpretation_id: str,
        recipient_id: str,
        message: str,
        channel: str = "IN_APP",
    ):
        payload = {
            "provider": "internal",
            "model_name": "review-notification",
            "prompt_name": f"REVIEW_NOTIFICATION:{interpretation_id}",
            "prompt": recipient_id,
            "response": f"{channel}:{message}",
            "success": True,
            "error_message": None,
        }
        AILogRepository.create_log(payload)

    @staticmethod
    def list_review_notifications(
        interpretation_id: str
    ):
        response = (
            supabase
            .table("ai_logs")
            .select("*")
            .eq(
                "prompt_name",
                f"REVIEW_NOTIFICATION:{interpretation_id}"
            )
            .order(
                "created_at",
                desc=False
            )
            .execute()
        )
        return response.data or []