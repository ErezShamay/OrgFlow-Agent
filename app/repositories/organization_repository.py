from uuid import uuid4

from postgrest.exceptions import APIError

from app.db.supabase_client import (
    supabase
)
from app.repositories.postgrest_errors import (
    is_missing_column_error,
)


class OrganizationRepository:

    def __init__(self):

        self.client = supabase

    def get_by_id(
        self,
        organization_id: str,
    ):

        response = (
            self.client
            .table("organizations")
            .select("*")
            .eq("id", organization_id)
            .limit(1)
            .execute()
        )

        if not response.data:
            return None

        return response.data[0]

    def get_first_organization(self):

        response = (
            self.client
            .table("organizations")
            .select("*")
            .order("created_at")
            .limit(1)
            .execute()
        )

        if not response.data:
            return None

        return response.data[0]

    def create_organization(
        self,
        *,
        name: str,
        contact_email: str,
        owner_profile_id: str | None = None,
    ):

        org_id = str(uuid4())
        payloads = [
            {
                "id": org_id,
                "organization_name": name,
                "contact_email": contact_email,
                "status": "ACTIVE",
                "owner_profile_id": owner_profile_id,
            },
            {
                "id": org_id,
                "organization_name": name,
                "contact_email": contact_email,
                "status": "ACTIVE",
            },
            {
                "id": org_id,
                "organization_name": name,
            },
            {
                "id": org_id,
                "name": name,
            },
        ]

        last_error = None

        for payload in payloads:
            cleaned = {
                key: value
                for key, value in payload.items()
                if value is not None
            }

            try:
                response = (
                    self.client
                    .table("organizations")
                    .insert(cleaned)
                    .execute()
                )
                return response.data[0]
            except APIError as error:
                last_error = error

        if last_error:
            raise last_error

        raise RuntimeError("Failed creating organization")

    def profile_owns_organization(
        self,
        *,
        profile_id: str,
        organization_id: str,
    ) -> bool:

        try:
            response = (
                self.client
                .table("organizations")
                .select("id")
                .eq("id", organization_id)
                .eq("owner_profile_id", profile_id)
                .limit(1)
                .execute()
            )
            return bool(response.data)
        except APIError as error:
            if is_missing_column_error(
                error,
                "owner_profile_id",
            ):
                return False
            raise

    def list_accessible_for_profile(
        self,
        profile_id: str,
    ) -> list[dict]:

        organizations: dict[str, dict] = {}

        try:
            owned_response = (
                self.client
                .table("organizations")
                .select("*")
                .eq("owner_profile_id", profile_id)
                .execute()
            )

            for organization in owned_response.data or []:
                organizations[str(organization["id"])] = organization
        except APIError as error:
            if not is_missing_column_error(
                error,
                "owner_profile_id",
            ):
                raise

        from app.repositories.profile_repository import (
            ProfileRepository,
        )

        profile = ProfileRepository().get_profile_by_id(
            profile_id
        )

        if profile:
            profile_org_id = (
                ProfileRepository.extract_organization_id(
                    profile
                )
            )

            if profile_org_id and profile_org_id not in organizations:
                organization = self.get_by_id(profile_org_id)

                if organization:
                    organizations[profile_org_id] = organization

        return list(organizations.values())

    def supports_owner_profile_column(self) -> bool:

        try:
            (
                self.client
                .table("organizations")
                .select("owner_profile_id")
                .limit(1)
                .execute()
            )
            return True
        except APIError as error:
            if is_missing_column_error(
                error,
                "owner_profile_id",
            ):
                return False
            raise

    def attach_projects(
        self,
        organizations: list[dict],
    ) -> list[dict]:

        if not organizations:
            return organizations

        org_ids = [
            organization["id"]
            for organization in organizations
        ]

        projects_response = (
            self.client
            .table("projects")
            .select("*")
            .in_(
                "organization_id",
                org_ids,
            )
            .execute()
        )

        projects_by_org: dict[str, list] = {
            org_id: []
            for org_id in org_ids
        }

        for project in projects_response.data or []:
            org_id = project.get("organization_id")

            if org_id in projects_by_org:
                projects_by_org[org_id].append(project)

        for organization in organizations:
            organization["projects"] = (
                projects_by_org.get(
                    organization["id"],
                    [],
                )
            )

        return organizations

    def get_all_organizations(self):

        organizations_response = (
            self.client
            .table("organizations")
            .select("*")
            .execute()
        )

        organizations = (
            organizations_response.data or []
        )

        return self.attach_projects(organizations)

    def update_report_profile(
        self,
        *,
        organization_id: str,
        report_phone: str | None,
        report_address_line: str | None,
        report_city: str | None,
        report_tagline: str | None,
        logo_storage_path: str | None,
    ) -> dict | None:

        payload = {
            "report_phone": report_phone,
            "report_address_line": report_address_line,
            "report_city": report_city,
            "report_tagline": report_tagline,
            "logo_storage_path": logo_storage_path,
        }
        response = (
            self.client
            .table("organizations")
            .update(payload)
            .eq("id", organization_id)
            .execute()
        )

        if not response.data:
            return None

        return response.data[0]
