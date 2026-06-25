from __future__ import annotations

from datetime import UTC, datetime

from postgrest.exceptions import APIError

from app.db.supabase_client import supabase
from app.repositories.postgrest_errors import is_missing_table_error


def build_apartment_group_key(apartment_number: str) -> str:
    return f"apartment:{apartment_number.strip()}"


class ProjectApartmentRepository:
    TABLE = "project_apartments"

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

    def list_by_project(self, project_id: str) -> list[dict]:
        if not self.is_storage_available():
            return []

        response = (
            self.client
            .table(self.TABLE)
            .select("*")
            .eq("project_id", project_id)
            .order("apartment_number")
            .execute()
        )
        return response.data or []

    def get_by_id(self, apartment_id: str) -> dict | None:
        if not self.is_storage_available():
            return None

        response = (
            self.client
            .table(self.TABLE)
            .select("*")
            .eq("id", apartment_id)
            .limit(1)
            .execute()
        )
        if not response.data:
            return None
        return response.data[0]

    def get_by_resident_profile_id(
        self,
        profile_id: str,
    ) -> dict | None:
        if not self.is_storage_available():
            return None

        response = (
            self.client
            .table(self.TABLE)
            .select("*")
            .eq("resident_profile_id", profile_id)
            .limit(1)
            .execute()
        )
        if not response.data:
            return None
        return response.data[0]

    def bulk_create_apartments(
        self,
        *,
        organization_id: str,
        project_id: str,
        apartments: list[dict],
    ) -> list[dict]:
        if not self.is_storage_available():
            raise RuntimeError(
                f"Table {self.TABLE} is not available. "
                "Apply db/migrations/2026061201_project_apartments.sql"
            )

        if not apartments:
            return []

        now = datetime.now(UTC).isoformat()
        payload: list[dict] = []

        for item in apartments:
            normalized_number = str(item.get("apartment_number") or "").strip()
            owner_name = str(
                item.get("owner_name") or "דייר"
            ).strip()
            if not normalized_number or not owner_name:
                continue

            payload.append(
                {
                    "organization_id": organization_id,
                    "project_id": project_id,
                    "apartment_number": normalized_number,
                    "group_key": build_apartment_group_key(normalized_number),
                    "owner_name": owner_name,
                    "phone": None,
                    "email": None,
                    "building": None,
                    "entrance": None,
                    "created_at": now,
                    "updated_at": now,
                }
            )

        if not payload:
            return []

        response = (
            self.client
            .table(self.TABLE)
            .insert(payload)
            .execute()
        )
        return response.data or []

    def upsert_apartment(
        self,
        *,
        organization_id: str,
        project_id: str,
        apartment_number: str,
        owner_name: str,
        phone: str | None = None,
        email: str | None = None,
        building: str | None = None,
        entrance: str | None = None,
    ) -> tuple[dict, bool]:
        if not self.is_storage_available():
            raise RuntimeError(
                f"Table {self.TABLE} is not available. "
                "Apply db/migrations/2026061201_project_apartments.sql"
            )

        normalized_number = apartment_number.strip()
        now = datetime.now(UTC).isoformat()
        payload = {
            "organization_id": organization_id,
            "project_id": project_id,
            "apartment_number": normalized_number,
            "group_key": build_apartment_group_key(normalized_number),
            "owner_name": owner_name.strip(),
            "phone": (phone or "").strip() or None,
            "email": (email or "").strip().lower() or None,
            "building": (building or "").strip() or None,
            "entrance": (entrance or "").strip() or None,
            "updated_at": now,
        }

        existing = (
            self.client
            .table(self.TABLE)
            .select("id")
            .eq("project_id", project_id)
            .eq("apartment_number", normalized_number)
            .limit(1)
            .execute()
        )

        if existing.data:
            apartment_id = str(existing.data[0]["id"])
            response = (
                self.client
                .table(self.TABLE)
                .update(payload)
                .eq("id", apartment_id)
                .execute()
            )
            return response.data[0], False

        payload["created_at"] = now
        response = (
            self.client
            .table(self.TABLE)
            .insert(payload)
            .execute()
        )
        return response.data[0], True

    def get_by_project_and_number(
        self,
        *,
        project_id: str,
        apartment_number: str,
    ) -> dict | None:
        if not self.is_storage_available():
            return None

        normalized_number = apartment_number.strip()
        response = (
            self.client
            .table(self.TABLE)
            .select("*")
            .eq("project_id", project_id)
            .eq("apartment_number", normalized_number)
            .limit(1)
            .execute()
        )
        if not response.data:
            return None
        return response.data[0]

    def update_apartment_by_id(
        self,
        *,
        apartment_id: str,
        apartment_number: str,
        owner_name: str,
        phone: str | None = None,
        email: str | None = None,
    ) -> dict | None:
        if not self.is_storage_available():
            raise RuntimeError(
                f"Table {self.TABLE} is not available. "
                "Apply db/migrations/2026061201_project_apartments.sql"
            )

        normalized_number = apartment_number.strip()
        now = datetime.now(UTC).isoformat()
        payload = {
            "apartment_number": normalized_number,
            "group_key": build_apartment_group_key(normalized_number),
            "owner_name": owner_name.strip(),
            "phone": (phone or "").strip() or None,
            "email": (email or "").strip().lower() or None,
            "updated_at": now,
        }

        response = (
            self.client
            .table(self.TABLE)
            .update(payload)
            .eq("id", apartment_id)
            .execute()
        )
        if not response.data:
            return None
        return response.data[0]

    def link_resident_profile(
        self,
        *,
        apartment_id: str,
        profile_id: str,
        invite_status: str,
    ) -> dict:
        if not self.is_storage_available():
            raise RuntimeError(
                f"Table {self.TABLE} is not available. "
                "Apply db/migrations/2026061201_project_apartments.sql"
            )

        now = datetime.now(UTC).isoformat()
        response = (
            self.client
            .table(self.TABLE)
            .update(
                {
                    "resident_profile_id": profile_id,
                    "invite_status": invite_status,
                    "updated_at": now,
                }
            )
            .eq("id", apartment_id)
            .execute()
        )
        return response.data[0]

    def set_profile_apartment_link(
        self,
        *,
        profile_id: str,
        apartment_id: str,
    ) -> None:
        (
            self.client
            .table("profiles")
            .update({"project_apartment_id": apartment_id})
            .eq("id", profile_id)
            .execute()
        )

    def activate_resident_by_profile_id(self, profile_id: str) -> bool:
        if not self.is_storage_available():
            return False

        apartment = self.get_by_resident_profile_id(profile_id)
        if apartment is None:
            return False

        current_status = str(apartment.get("invite_status") or "")
        if current_status == "active":
            return False

        now = datetime.now(UTC).isoformat()
        (
            self.client
            .table(self.TABLE)
            .update(
                {
                    "invite_status": "active",
                    "updated_at": now,
                }
            )
            .eq("id", str(apartment["id"]))
            .execute()
        )
        return True

    def clear_resident_profile_link(self, *, profile_id: str) -> None:
        if not self.is_storage_available():
            return

        now = datetime.now(UTC).isoformat()
        (
            self.client
            .table(self.TABLE)
            .update(
                {
                    "resident_profile_id": None,
                    "invite_status": "none",
                    "updated_at": now,
                }
            )
            .eq("resident_profile_id", profile_id)
            .execute()
        )
