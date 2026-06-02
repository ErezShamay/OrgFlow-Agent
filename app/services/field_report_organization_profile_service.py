from __future__ import annotations

from postgrest.exceptions import APIError

from app.exceptions.exceptions import NotFoundError
from app.exceptions.exceptions import ValidationError
from app.repositories.organization_repository import (
    OrganizationRepository,
)
from app.repositories.postgrest_errors import (
    is_missing_column_error,
)
from app.services.field_report_module_service import (
    FieldReportModuleService,
)


class FieldReportOrganizationProfileService:
    def __init__(
        self,
        organization_repository:
            OrganizationRepository | None = None,
        module_service: FieldReportModuleService | None = None,
    ) -> None:
        self.organization_repository = (
            organization_repository or OrganizationRepository()
        )
        self.module_service = (
            module_service or FieldReportModuleService()
        )

    def get_profile(
        self,
        organization_id: str,
        *,
        require_module: bool = True,
    ) -> dict:
        if require_module:
            self.module_service.require_enabled(organization_id)

        organization = self.organization_repository.get_by_id(
            organization_id
        )

        if not organization:
            raise NotFoundError(
                message="Organization not found",
                resource_type="organization",
                resource_id=organization_id,
            )

        name = (
            organization.get("organization_name")
            or organization.get("name")
            or organization_id
        )
        logo_path = organization.get("logo_storage_path")

        return {
            "organization_id": organization_id,
            "organization_name": name,
            "contact_email": organization.get("contact_email"),
            "report_phone": organization.get("report_phone"),
            "report_address_line": organization.get(
                "report_address_line"
            ),
            "report_city": organization.get("report_city"),
            "report_tagline": organization.get("report_tagline"),
            "logo_storage_path": logo_path,
            "logo_url": logo_path,
        }

    def update_profile(
        self,
        organization_id: str,
        *,
        report_phone: str | None,
        report_address_line: str | None,
        report_city: str | None,
        report_tagline: str | None,
        logo_storage_path: str | None,
    ) -> dict:
        normalized_phone = _normalize_optional_text(report_phone)
        normalized_address = _normalize_optional_text(
            report_address_line
        )
        normalized_city = _normalize_optional_text(report_city)
        normalized_tagline = _normalize_optional_text(report_tagline)
        normalized_logo_path = _normalize_optional_text(
            logo_storage_path
        )

        if normalized_logo_path and not (
            normalized_logo_path.startswith("http://")
            or normalized_logo_path.startswith("https://")
            or normalized_logo_path.startswith("/")
        ):
            raise ValidationError(
                message=(
                    "logo_storage_path must be an https/http URL "
                    "or an absolute storage path"
                )
            )

        try:
            organization = (
                self.organization_repository.update_report_profile(
                    organization_id=organization_id,
                    report_phone=normalized_phone,
                    report_address_line=normalized_address,
                    report_city=normalized_city,
                    report_tagline=normalized_tagline,
                    logo_storage_path=normalized_logo_path,
                )
            )
        except APIError as error:
            missing_columns = [
                "report_phone",
                "report_address_line",
                "report_city",
                "report_tagline",
                "logo_storage_path",
            ]
            if any(
                is_missing_column_error(error, column)
                for column in missing_columns
            ):
                raise ValidationError(
                    message=(
                        "Organization report profile columns are missing. "
                        "Run migration "
                        "db/migrations/2026060101_organization_field_report_module.sql"
                    )
                ) from error
            raise

        if not organization:
            raise NotFoundError(
                message="Organization not found",
                resource_type="organization",
                resource_id=organization_id,
            )

        return self.get_profile(
            organization_id,
            require_module=False,
        )


def _normalize_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    if not normalized:
        return None
    return normalized
