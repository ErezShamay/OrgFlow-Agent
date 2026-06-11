from __future__ import annotations

import logging
import shutil

from postgrest.exceptions import APIError

from app.auth.roles import is_platform_admin
from app.db.supabase_client import supabase
from app.exceptions.exceptions import (
    ForbiddenError,
    NotFoundError,
)
from app.repositories.organization_repository import (
    OrganizationRepository,
)
from app.repositories.postgrest_errors import (
    is_missing_column_error,
    is_missing_table_error,
)
from app.repositories.profile_repository import (
    ProfileRepository,
)
from app.repositories.project_repository import (
    ProjectRepository,
)
from app.services.field_visit_report_pdf_service import (
    FieldVisitReportPdfService,
)
from app.services.field_visit_report_photo_service import (
    FieldVisitReportPhotoService,
)

logger = logging.getLogger(__name__)

PROJECT_ID_CHUNK_SIZE = 50

ORGANIZATION_SCOPED_TABLES: tuple[str, ...] = (
    "field_visit_report_line_photos",
    "field_visit_report_lines",
    "field_visit_reports",
    "organization_field_report_modules",
    "organization_tenant_manager_modules",
    "ai_interpretations",
    "operational_actions",
    "weekly_reports",
    "automation_runs",
    "ai_execution_logs",
)

PROJECT_SCOPED_TABLES: tuple[str, ...] = (
    "findings",
    "reports",
    "workspace_activity",
)


class OrganizationDeletionService:
    def __init__(
        self,
        *,
        organization_repository: OrganizationRepository | None = None,
        profile_repository: ProfileRepository | None = None,
        project_repository: ProjectRepository | None = None,
        photo_service: FieldVisitReportPhotoService | None = None,
        pdf_service: FieldVisitReportPdfService | None = None,
        client=supabase,
    ) -> None:
        self.client = client
        self.organization_repository = (
            organization_repository or OrganizationRepository()
        )
        self.profile_repository = (
            profile_repository or ProfileRepository()
        )
        self.project_repository = (
            project_repository or ProjectRepository()
        )
        self.photo_service = (
            photo_service or FieldVisitReportPhotoService()
        )
        self.pdf_service = (
            pdf_service or FieldVisitReportPdfService()
        )

    def delete_organization(
        self,
        *,
        organization_id: str,
        actor_user_id: str,
        actor_role: str,
    ) -> dict:
        if not is_platform_admin(actor_role):
            raise ForbiddenError(
                message="Only platform admins can delete customer organizations"
            )

        normalized_org_id = organization_id.strip()
        organization = self.organization_repository.get_by_id(
            normalized_org_id
        )

        if not organization:
            raise NotFoundError(
                message="Organization not found",
                resource_type="organization",
                resource_id=normalized_org_id,
            )

        project_ids = (
            self.project_repository
            .get_projects_by_organization(normalized_org_id)
        )
        project_id_list = [
            str(project["id"])
            for project in project_ids
            if project.get("id")
        ]

        profiles = (
            self.profile_repository
            .list_profiles_by_organization(normalized_org_id)
        )

        deleted_counts: dict[str, int] = {}

        deleted_counts["field_report_photos"] = (
            self._purge_field_report_photo_files(normalized_org_id)
        )
        deleted_counts["field_report_pdfs"] = (
            self._purge_field_report_pdf_files(normalized_org_id)
        )
        deleted_counts["action_comments"] = (
            self._delete_action_comments_for_organization(
                normalized_org_id
            )
        )

        for table_name in ORGANIZATION_SCOPED_TABLES:
            deleted_counts[table_name] = self._delete_rows_by_organization(
                table_name,
                normalized_org_id,
            )

        for table_name in PROJECT_SCOPED_TABLES:
            deleted_counts[table_name] = (
                self._delete_rows_by_project_ids(
                    table_name,
                    project_id_list,
                )
            )

        deleted_counts["projects"] = self._delete_rows_by_organization(
            "projects",
            normalized_org_id,
        )

        deleted_user_ids: list[str] = []
        cleared_platform_admin_ids: list[str] = []

        profile_ids_to_delete: list[str] = []

        for profile in profiles:
            profile_id = str(profile.get("id") or "").strip()
            if not profile_id:
                continue

            if is_platform_admin(profile.get("role")):
                self._clear_profile_organization(profile_id)
                cleared_platform_admin_ids.append(profile_id)
                continue

            profile_ids_to_delete.append(profile_id)

        deleted_counts["notifications"] = (
            self._delete_notifications_for_profiles(
                profile_ids_to_delete
            )
        )

        for profile_id in profile_ids_to_delete:
            self._delete_auth_user(profile_id)
            self.profile_repository.delete_profile(profile_id)
            deleted_user_ids.append(profile_id)

        deleted_counts["profiles"] = len(deleted_user_ids)
        deleted_counts["organizations"] = (
            1
            if self.organization_repository.delete_organization(
                normalized_org_id
            )
            else 0
        )

        logger.info(
            "Customer organization deleted",
            extra={
                "event": "audit.organization_delete",
                "organization_id": normalized_org_id,
                "actor_user_id": actor_user_id,
                "deleted_user_count": len(deleted_user_ids),
                "cleared_platform_admin_count": len(
                    cleared_platform_admin_ids
                ),
                "project_count": len(project_id_list),
            },
        )

        return {
            "status": "deleted",
            "organization_id": normalized_org_id,
            "deleted_user_ids": deleted_user_ids,
            "cleared_platform_admin_ids": cleared_platform_admin_ids,
            "deleted_counts": deleted_counts,
        }

    def _purge_field_report_photo_files(
        self,
        organization_id: str,
    ) -> int:
        removed = 0

        try:
            response = (
                self.client
                .table("field_visit_report_line_photos")
                .select("storage_path")
                .eq("organization_id", organization_id)
                .execute()
            )
        except APIError as error:
            if is_missing_table_error(
                error,
                "field_visit_report_line_photos",
            ):
                return 0
            raise

        for row in response.data or []:
            storage_path = str(row.get("storage_path") or "").strip()
            if not storage_path:
                continue

            try:
                self.photo_service.delete_photo(storage_path)
                removed += 1
            except Exception as error:
                logger.warning(
                    "Failed deleting field report photo file",
                    extra={
                        "organization_id": organization_id,
                        "storage_path": storage_path,
                        "error": str(error),
                    },
                )

        org_photo_dir = (
            self.photo_service.photos_root / organization_id
        )
        if org_photo_dir.is_dir():
            shutil.rmtree(org_photo_dir, ignore_errors=True)

        return removed

    def _purge_field_report_pdf_files(
        self,
        organization_id: str,
    ) -> int:
        removed = 0

        try:
            response = (
                self.client
                .table("field_visit_reports")
                .select("pdf_storage_path")
                .eq("organization_id", organization_id)
                .execute()
            )
        except APIError as error:
            if is_missing_table_error(error, "field_visit_reports"):
                return 0
            if is_missing_column_error(error, "pdf_storage_path"):
                return 0
            raise

        for row in response.data or []:
            storage_path = str(row.get("pdf_storage_path") or "").strip()
            if not storage_path:
                continue

            try:
                self.pdf_service.delete_pdf(storage_path)
                removed += 1
            except Exception as error:
                logger.warning(
                    "Failed deleting field report PDF file",
                    extra={
                        "organization_id": organization_id,
                        "storage_path": storage_path,
                        "error": str(error),
                    },
                )

        org_pdf_dir = self.pdf_service.pdfs_root / organization_id
        if org_pdf_dir.is_dir():
            shutil.rmtree(org_pdf_dir, ignore_errors=True)

        return removed

    def _delete_notifications_for_profiles(
        self,
        profile_ids: list[str],
    ) -> int:
        if not profile_ids:
            return 0

        deleted = 0

        for chunk in self._chunked(profile_ids):
            try:
                response = (
                    self.client
                    .table("notifications")
                    .delete()
                    .in_("profile_id", chunk)
                    .execute()
                )
            except APIError as error:
                if is_missing_table_error(error, "notifications"):
                    return deleted
                raise

            deleted += len(response.data or [])

        return deleted

    def _delete_action_comments_for_organization(
        self,
        organization_id: str,
    ) -> int:
        try:
            actions_response = (
                self.client
                .table("operational_actions")
                .select("id")
                .eq("organization_id", organization_id)
                .execute()
            )
        except APIError as error:
            if is_missing_table_error(error, "operational_actions"):
                return 0
            if is_missing_column_error(error, "organization_id"):
                return 0
            raise

        action_ids = [
            str(row.get("id"))
            for row in actions_response.data or []
            if row.get("id")
        ]

        if not action_ids:
            return 0

        deleted = 0
        for chunk in self._chunked(action_ids):
            try:
                response = (
                    self.client
                    .table("action_comments")
                    .delete()
                    .in_("action_id", chunk)
                    .execute()
                )
            except APIError as error:
                if is_missing_table_error(error, "action_comments"):
                    return deleted
                raise

            deleted += len(response.data or [])

        return deleted

    def _delete_rows_by_organization(
        self,
        table_name: str,
        organization_id: str,
    ) -> int:
        try:
            response = (
                self.client
                .table(table_name)
                .delete()
                .eq("organization_id", organization_id)
                .execute()
            )
        except APIError as error:
            if is_missing_table_error(error, table_name):
                return 0
            if is_missing_column_error(error, "organization_id"):
                return 0
            raise

        return len(response.data or [])

    def _delete_rows_by_project_ids(
        self,
        table_name: str,
        project_ids: list[str],
    ) -> int:
        if not project_ids:
            return 0

        deleted = 0

        for chunk in self._chunked(project_ids):
            try:
                response = (
                    self.client
                    .table(table_name)
                    .delete()
                    .in_("project_id", chunk)
                    .execute()
                )
            except APIError as error:
                if is_missing_table_error(error, table_name):
                    return deleted
                if is_missing_column_error(error, "project_id"):
                    return deleted
                raise

            deleted += len(response.data or [])

        return deleted

    def _clear_profile_organization(
        self,
        profile_id: str,
    ) -> None:
        if not self.profile_repository.supports_organization_column():
            return

        try:
            self.profile_repository.update_profile(
                profile_id,
                {"organization_id": None},
            )
        except Exception as error:
            logger.warning(
                "Failed clearing organization_id on platform admin profile",
                extra={
                    "profile_id": profile_id,
                    "error": str(error),
                },
            )

    def _delete_auth_user(
        self,
        profile_id: str,
    ) -> None:
        try:
            self.client.auth.admin.delete_user(profile_id)
        except Exception as error:
            logger.warning(
                "Failed deleting auth user during organization purge",
                extra={
                    "profile_id": profile_id,
                    "error": str(error),
                },
            )

    @staticmethod
    def _chunked(values: list[str]) -> list[list[str]]:
        return [
            values[index : index + PROJECT_ID_CHUNK_SIZE]
            for index in range(0, len(values), PROJECT_ID_CHUNK_SIZE)
        ]
