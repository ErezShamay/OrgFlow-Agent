from __future__ import annotations

from typing import Any

from postgrest.exceptions import APIError

from app.config.standards_seed import iter_seed_standards
from app.db.supabase_client import supabase
from app.repositories.postgrest_errors import is_missing_table_error

STANDARDS_MIGRATION = (
    "db/migrations/2026061802_standards_and_regulations.sql"
)


def _normalize_record(record: dict[str, Any]) -> dict[str, Any]:
    return dict(record)


class StandardsRepository:
    def __init__(self) -> None:
        self.client = supabase

    def is_storage_available(self) -> bool:
        try:
            self.client.table("standards_and_regulations").select("id").limit(1).execute()
            return True
        except APIError as error:
            if is_missing_table_error(error, "standards_and_regulations"):
                return False
            raise

    def list_all(self) -> list[dict[str, Any]]:
        try:
            response = (
                self.client.table("standards_and_regulations")
                .select("*")
                .order("standard_code")
                .execute()
            )
            records = [_normalize_record(item) for item in (response.data or [])]
            if records:
                return records
        except APIError as error:
            if is_missing_table_error(error, "standards_and_regulations"):
                return [
                    _normalize_record(dict(record))
                    for record in iter_seed_standards()
                ]
            raise

        return [
            _normalize_record(dict(record))
            for record in iter_seed_standards()
        ]

    def get_by_id(self, standard_id: str) -> dict[str, Any] | None:
        try:
            response = (
                self.client.table("standards_and_regulations")
                .select("*")
                .eq("id", standard_id)
                .limit(1)
                .execute()
            )
        except APIError as error:
            if is_missing_table_error(error, "standards_and_regulations"):
                for record in iter_seed_standards():
                    if str(record.get("id")) == standard_id:
                        return _normalize_record(dict(record))
                return None
            raise

        if response.data:
            return _normalize_record(response.data[0])

        for record in iter_seed_standards():
            if str(record.get("id")) == standard_id:
                return _normalize_record(dict(record))
        return None

    def get_by_code(self, standard_code: str) -> dict[str, Any] | None:
        normalized = (standard_code or "").strip()
        if not normalized:
            return None

        try:
            response = (
                self.client.table("standards_and_regulations")
                .select("*")
                .eq("standard_code", normalized)
                .limit(1)
                .execute()
            )
        except APIError as error:
            if is_missing_table_error(error, "standards_and_regulations"):
                for record in iter_seed_standards():
                    if str(record.get("standard_code") or "") == normalized:
                        return _normalize_record(dict(record))
                return None
            raise

        if response.data:
            return _normalize_record(response.data[0])

        for record in iter_seed_standards():
            if str(record.get("standard_code") or "") == normalized:
                return _normalize_record(dict(record))
        return None
