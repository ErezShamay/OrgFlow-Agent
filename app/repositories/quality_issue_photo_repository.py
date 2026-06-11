from __future__ import annotations

from datetime import UTC, datetime

from postgrest.exceptions import APIError

from app.db.supabase_client import supabase
from app.repositories.postgrest_errors import is_missing_table_error

QUALITY_ISSUE_PHOTOS_MIGRATION = (
    "db/migrations/2026060915_quality_issue_photos.sql"
)


class QualityIssuePhotoRepository:
    TABLE = "quality_issue_photos"

    def __init__(self) -> None:
        self.client = supabase
        self._table_available: bool | None = None

    def is_storage_available(self) -> bool:
        if self._table_available is not None:
            return self._table_available

        try:
            (
                self.client
                .table(self.TABLE)
                .select("id")
                .limit(1)
                .execute()
            )
            self._table_available = True
        except APIError as error:
            if is_missing_table_error(error, self.TABLE):
                self._table_available = False
            else:
                raise

        return self._table_available

    def list_by_issue(self, issue_id: str) -> list[dict]:
        if not self.is_storage_available():
            return []

        response = (
            self.client
            .table(self.TABLE)
            .select("*")
            .eq("issue_id", issue_id)
            .order("sort_order")
            .order("created_at")
            .execute()
        )
        return response.data or []

    def get_by_id(self, photo_id: str) -> dict | None:
        if not self.is_storage_available():
            return None

        response = (
            self.client
            .table(self.TABLE)
            .select("*")
            .eq("id", photo_id)
            .limit(1)
            .execute()
        )

        if not response.data:
            return None

        return response.data[0]

    def get_for_issue(
        self,
        *,
        issue_id: str,
        photo_id: str,
        organization_id: str,
    ) -> dict | None:
        photo = self.get_by_id(photo_id)
        if photo is None:
            return None
        if str(photo.get("issue_id")) != issue_id:
            return None
        if str(photo.get("organization_id")) != organization_id:
            return None
        return photo

    def next_sort_order(self, issue_id: str) -> int:
        photos = self.list_by_issue(issue_id)
        if not photos:
            return 0
        return max(int(photo.get("sort_order") or 0) for photo in photos) + 1

    def create(self, payload: dict) -> dict:
        if not self.is_storage_available():
            raise RuntimeError(
                f"Table {self.TABLE} is not available. "
                f"Apply {QUALITY_ISSUE_PHOTOS_MIGRATION}"
            )

        now = datetime.now(UTC).isoformat()
        payload.setdefault("created_at", now)
        payload.setdefault("updated_at", now)

        response = (
            self.client
            .table(self.TABLE)
            .insert(payload)
            .execute()
        )
        return response.data[0]
