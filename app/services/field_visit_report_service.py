from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from app.config.field_report_visit_types import (
    allowed_top_families,
    is_valid_visit_type,
    list_visit_types,
)
from app.exceptions.exceptions import (
    ConflictError,
    NotFoundError,
    ValidationError,
)
from app.lib.field_report_client_ids import (
    normalize_client_line_uuid,
    normalize_client_report_uuid,
)
from app.lib.field_report_structure_activity import (
    record_report_structure_activity_best_effort,
)
from app.lib.project_date_validation import (
    validate_header_fields_project_dates,
)
from app.repositories.field_visit_report_line_photo_repository import (
    FieldVisitReportLinePhotoRepository,
)
from app.repositories.field_visit_report_line_repository import (
    FieldVisitReportLineRepository,
)
from app.repositories.field_visit_report_repository import (
    FieldVisitReportRepository,
)
from app.repositories.workspace_activity_repository import (
    WorkspaceActivityRepository,
)
from app.repositories.project_apartment_repository import (
    ProjectApartmentRepository,
)
from app.repositories.project_repository import (
    ProjectRepository,
)
from app.schemas.quality_issue import (
    DEFAULT_ISSUE_VISIBILITY,
    IssueVisibility,
    parse_quality_issue_row,
)
from app.services.field_report_catalog_service import (
    FieldReportCatalogService,
)
from app.services.field_report_organization_profile_service import (
    FieldReportOrganizationProfileService,
)
from app.services.field_supervision_offline_bundle import (
    build_apartments_by_project,
    build_supervision_catalog,
    public_areas_for_offline_bundle,
)
from app.services.field_visit_report_archive_service import (
    build_project_field_report_archive,
)
from app.services.field_visit_report_photo_service import (
    FieldVisitReportPhotoService,
)
from app.services.field_visit_report_pdf_service import (
    FieldVisitReportPdfService,
)
from app.services.field_visit_report_core_adapter import (
    FieldVisitReportCoreAdapter,
)
from app.services.quality_issue_materialization_service import (
    MaterializationResult,
    QualityIssueMaterializationService,
    collect_materializable_finding_rows,
)
from app.services.qc_notification_service import QcNotificationService
from app.services.report_processing_service import (
    ReportProcessingService,
)

VISIT_STATUS_LABELS_HE: dict[str, str] = {
    "IN_PROGRESS": "בעבודה",
    "CLOSED": "סגור",
    "PENDING_UPLOAD": "ממתין לשליחה",
    "LOCKED": "נעול",
}

EDITABLE_STATUSES = frozenset({"IN_PROGRESS"})
REOPENABLE_STATUSES = frozenset({"CLOSED"})
PUBLISHABLE_STATUSES = frozenset({"CLOSED"})
SENDABLE_STATUSES = frozenset({"CLOSED"})
SYNCABLE_STATUSES = frozenset({
    "IN_PROGRESS",
    "CLOSED",
    "PENDING_UPLOAD",
})
OFFLINE_MAX_DAYS = 7
LIST_HIDDEN_STATUSES = frozenset({"LOCKED"})
REQUEST_SEND_ERROR_CODE_INVALID_STATUS = (
    "FIELD_VISIT_REPORT_SEND_INVALID_STATUS"
)
REQUEST_SEND_ERROR_CODE_CORE_FAILED = (
    "FIELD_VISIT_REPORT_CORE_SEND_FAILED"
)

MAX_LINE_PHOTOS = 5
LEGACY_LINE_PHOTO_ID = "legacy"


class FieldVisitReportService:
    def __init__(
        self,
        report_repository:
            FieldVisitReportRepository | None = None,
        line_repository:
            FieldVisitReportLineRepository | None = None,
        line_photo_repository:
            FieldVisitReportLinePhotoRepository | None = None,
        project_repository:
            ProjectRepository | None = None,
        apartment_repository:
            ProjectApartmentRepository | None = None,
        organization_profile_service:
            FieldReportOrganizationProfileService | None = None,
        catalog_service:
            FieldReportCatalogService | None = None,
        photo_service:
            FieldVisitReportPhotoService | None = None,
        pdf_service:
            FieldVisitReportPdfService | None = None,
        core_adapter:
            FieldVisitReportCoreAdapter | None = None,
        report_processing_service:
            ReportProcessingService | None = None,
        materialization_service:
            QualityIssueMaterializationService | None = None,
        qc_notification_service:
            QcNotificationService | None = None,
        activity_recorder=None,
    ) -> None:
        self.report_repository = (
            report_repository or FieldVisitReportRepository()
        )
        self.line_repository = (
            line_repository or FieldVisitReportLineRepository()
        )
        self.line_photo_repository = (
            line_photo_repository or FieldVisitReportLinePhotoRepository()
        )
        self.project_repository = (
            project_repository or ProjectRepository()
        )
        self.apartment_repository = (
            apartment_repository or ProjectApartmentRepository()
        )
        self.organization_profile_service = (
            organization_profile_service
            or FieldReportOrganizationProfileService()
        )
        self.catalog_service = (
            catalog_service or FieldReportCatalogService()
        )
        self.photo_service = (
            photo_service or FieldVisitReportPhotoService()
        )
        self.pdf_service = (
            pdf_service or FieldVisitReportPdfService()
        )
        self.core_adapter = core_adapter or FieldVisitReportCoreAdapter(
            report_processing_service=report_processing_service
            or ReportProcessingService(),
        )
        self.materialization_service = (
            materialization_service or QualityIssueMaterializationService()
        )
        self.qc_notification_service = qc_notification_service
        self.activity_recorder = (
            activity_recorder or WorkspaceActivityRepository.create_activity
        )

    def _record_structure_activity_if_changed(
        self,
        *,
        record: dict,
        before_header_fields: dict | None,
        after_header_fields: dict | None,
        actor_id: str | None = None,
    ) -> None:
        record_report_structure_activity_best_effort(
            activity_recorder=self.activity_recorder,
            project_id=str(record.get("project_id") or "") or None,
            report_id=str(record.get("id") or ""),
            before_header_fields=before_header_fields,
            after_header_fields=after_header_fields,
            actor_id=actor_id,
        )

    def is_storage_available(self) -> bool:
        return self.report_repository.is_storage_available()

    def are_lines_available(self) -> bool:
        return self.line_repository.is_storage_available()

    def are_line_photos_available(self) -> bool:
        return self.line_photo_repository.is_storage_available()

    def get_visit_types(self) -> dict:
        catalog = self.catalog_service.get_catalog_summary()
        return {
            "visit_types": list_visit_types(),
            "storage_available": self.is_storage_available(),
            "lines_storage_available": self.are_lines_available(),
            "catalog_version": catalog.get("catalog_version"),
            "catalog_issue_count": catalog.get("issue_count"),
            "catalog_errors": catalog.get("errors"),
        }

    def get_catalog(
        self,
        *,
        visit_type: str | None = None,
    ) -> dict:
        if visit_type:
            if not is_valid_visit_type(visit_type):
                raise ValidationError(
                    message="סוג ביקור לא תקין",
                    details={"visit_type": visit_type},
                )
            return self.catalog_service.get_catalog_for_visit_type(
                visit_type
            )
        return self.catalog_service.get_full_catalog()

    def build_offline_prep_bundle(
        self,
        organization_id: str,
    ) -> dict:
        if not self.is_storage_available():
            raise ValidationError(
                message=(
                    "טבלת דוחות ביקור אינה מוגדרת במסד הנתונים. "
                    "יש להריץ את המיגרציה "
                    "db/migrations/2026060102_field_visit_reports.sql"
                ),
            )

        projects = self.project_repository.get_projects_by_organization(
            organization_id
        )
        organization_profile = (
            self.organization_profile_service.get_profile(
                organization_id,
                require_module=False,
            )
        )
        catalog = self.catalog_service.get_full_catalog()
        project_payload = [
            {
                "id": str(project["id"]),
                "project_name": project.get("project_name"),
                "city": project.get("city"),
                "scheme": project.get("scheme"),
                "developer_name": project.get("developer_name"),
                "developer_pm_name": project.get("developer_pm_name"),
                "contractor_name": project.get("contractor_name"),
                "lawyer_name": project.get("lawyer_name"),
                "accompanying_lawyer": project.get(
                    "accompanying_lawyer"
                ),
                "architect_name": project.get("architect_name"),
                "site_manager_name": project.get("site_manager_name"),
                "housing_units_count": project.get(
                    "housing_units_count"
                ),
                "project_start_date": project.get(
                    "project_start_date"
                ),
                "project_end_date": project.get("project_end_date"),
                "project_grace_end_date": project.get(
                    "project_grace_end_date"
                ),
                "structure_documentation_date": project.get(
                    "structure_documentation_date"
                ),
                "illustration_url": project.get("illustration_url"),
                "illustration_source_he": project.get(
                    "illustration_source_he"
                ),
                "project_type": project.get("project_type"),
            }
            for project in projects
        ]
        project_ids = [
            str(project["id"])
            for project in projects
            if project.get("id")
        ]

        return {
            "organization_id": organization_id,
            "offline_max_days": OFFLINE_MAX_DAYS,
            "catalog_version": catalog.get("catalog_version"),
            "catalog": catalog,
            "supervision_catalog": build_supervision_catalog(catalog),
            "public_areas": public_areas_for_offline_bundle(),
            "apartments_by_project": build_apartments_by_project(
                organization_id=organization_id,
                project_ids=project_ids,
                apartment_repository=self.apartment_repository,
            ),
            "visit_types": list_visit_types(),
            "organization_profile": organization_profile,
            "projects": project_payload,
            "reports": self.list_reports(
                organization_id,
                status="IN_PROGRESS",
            )["reports"],
            "lines_storage_available": self.are_lines_available(),
        }

    def build_offline_prep_bundle_for_project(
        self,
        organization_id: str,
        project_id: str,
    ) -> dict:
        project = self.project_repository.get_project_by_id(project_id)
        if project is None:
            raise NotFoundError(message="Project not found")
        if str(project.get("organization_id")) != organization_id:
            raise NotFoundError(message="Project not found")

        bundle = self.build_offline_prep_bundle(organization_id)
        project_key = str(project_id)
        apartments_by_project = bundle.get("apartments_by_project") or {}
        if not isinstance(apartments_by_project, dict):
            apartments_by_project = {}

        bundle["focused_project_id"] = project_key
        bundle["projects"] = [
            item
            for item in bundle.get("projects") or []
            if str(item.get("id")) == project_key
        ]
        bundle["apartments_by_project"] = {
            key: value
            for key, value in apartments_by_project.items()
            if str(key) == project_key
        }
        bundle["reports"] = [
            item
            for item in bundle.get("reports") or []
            if str(item.get("project_id")) == project_key
        ]
        return bundle

    def list_reports(
        self,
        organization_id: str,
        *,
        status: str | None = None,
        project_id: str | None = None,
        project_names: dict[str, str] | None = None,
    ) -> dict:
        if not self.is_storage_available():
            raise ValidationError(
                message=(
                    "טבלת דוחות ביקור אינה מוגדרת במסד הנתונים. "
                    "יש להריץ את המיגרציה "
                    "db/migrations/2026060102_field_visit_reports.sql"
                ),
            )

        records = self.report_repository.list_by_organization(
            organization_id,
            status=status,
            project_id=project_id,
        )
        if status is None:
            records = [
                record
                for record in records
                if str(record.get("status") or "")
                not in LIST_HIDDEN_STATUSES
            ]

        return {
            "reports": [
                self._serialize_report(
                    record,
                    project_name=(
                        (project_names or {}).get(
                            str(record["project_id"])
                        )
                    ),
                    include_lines=False,
                )
                for record in records
            ],
            "total": len(records),
        }

    def get_report(
        self,
        *,
        organization_id: str,
        report_id: str,
        project_name: str | None = None,
        include_lines: bool = True,
    ) -> dict:
        record = self._get_org_report(
            organization_id=organization_id,
            report_id=report_id,
        )

        if project_name is None:
            project = self.project_repository.get_project_by_id(
                str(record["project_id"])
            )
            if project:
                project_name = project.get("project_name")

        return self._serialize_report(
            record,
            project_name=project_name,
            include_lines=include_lines,
        )

    def create_report(
        self,
        *,
        organization_id: str,
        actor_profile_id: str,
        project_id: str,
        visit_type: str,
        visit_date: str,
        header_fields: dict | None = None,
        catalog_version: str | None = None,
        snapshot_organization_profile: bool = True,
        client_report_uuid: str | None = None,
    ) -> dict:
        if not self.is_storage_available():
            raise ValidationError(
                message=(
                    "טבלת דוחות ביקור אינה מוגדרת במסד הנתונים. "
                    "יש להריץ את המיגרציה "
                    "db/migrations/2026060102_field_visit_reports.sql"
                ),
            )

        if not is_valid_visit_type(visit_type):
            raise ValidationError(
                message="סוג ביקור לא תקין",
                details={"visit_type": visit_type},
            )

        project = self.project_repository.get_project_by_id(
            project_id
        )

        if not project:
            raise NotFoundError(
                message="Project not found",
                resource_type="project",
                resource_id=project_id,
            )

        if str(project.get("organization_id")) != organization_id:
            raise NotFoundError(
                message="Project not found",
                resource_type="project",
                resource_id=project_id,
            )

        existing = self.report_repository.get_open_for_project(
            organization_id=organization_id,
            project_id=project_id,
        )

        if existing:
            raise ConflictError(
                message=(
                    "כבר קיים דוח בעבודה לפרויקט זה. "
                    "יש להמשיך את הדוח הקיים או לסגור אותו."
                ),
                details={
                    "existing_report_id": str(existing["id"]),
                    "project_id": project_id,
                },
            )

        profile_snapshot = None

        if snapshot_organization_profile:
            profile_snapshot = (
                self.organization_profile_service.get_profile(
                    organization_id,
                    require_module=False,
                )
            )

        merged_header_fields = _merge_header_fields(
            project,
            header_fields,
            visit_type=visit_type,
            visit_date=visit_date,
        )
        resolved_catalog_version = (
            catalog_version
            or self.catalog_service.get_catalog_summary().get(
                "catalog_version"
            )
        )

        normalized_client_report_uuid = normalize_client_report_uuid(
            client_report_uuid
        )

        if normalized_client_report_uuid:
            existing_client = (
                self.report_repository.get_by_client_report_uuid(
                    normalized_client_report_uuid
                )
            )
            if existing_client:
                raise ConflictError(
                    message="דוח עם מזהה מכשיר זה כבר קיים",
                    details={
                        "client_report_uuid": normalized_client_report_uuid,
                        "existing_report_id": str(existing_client["id"]),
                    },
                )

        record = self.report_repository.create(
            organization_id=organization_id,
            project_id=project_id,
            created_by_profile_id=actor_profile_id,
            visit_type=visit_type,
            visit_date=visit_date,
            header_fields=merged_header_fields,
            catalog_version=resolved_catalog_version,
            organization_profile_snapshot=profile_snapshot,
            client_report_uuid=normalized_client_report_uuid,
        )

        return self._serialize_report(
            record,
            project_name=project.get("project_name"),
        )

    def preview_publish_report(
        self,
        *,
        organization_id: str,
        report_id: str,
    ) -> dict:
        record = self._get_org_report(
            organization_id=organization_id,
            report_id=report_id,
        )
        self._ensure_publishable(record)

        current_catalog_version = (
            self.catalog_service.get_catalog_summary().get(
                "catalog_version"
            )
        )
        lines = self._load_lines(
            report_id,
            current_catalog_version=current_catalog_version,
        )
        materializable = collect_materializable_finding_rows(
            header_fields=record.get("header_fields") or {},
            lines=self._lines_for_materialization(report_id),
        )
        close_preview = _build_close_preview(lines)
        draft_count = sum(
            1
            for line in lines
            if str(line.get("visibility") or IssueVisibility.DRAFT.value)
            != IssueVisibility.PUBLISHED.value
        )
        published_count = len(lines) - draft_count
        already_published = self._is_report_published(record, lines)

        warnings = list(close_preview.get("warnings") or [])
        if already_published:
            warnings.append("הדוח כבר פורסם — פרסום חוזר יעדכן registry בלבד.")
        if not materializable:
            warnings.append(
                "אין שורות שייווצרו מ-registry — "
                "הדוח יפורסם לפורטל עם מה שקיים."
            )

        return {
            "line_count": len(lines),
            "draft_line_count": draft_count,
            "published_line_count": published_count,
            "materializable_line_count": len(materializable),
            "already_published": already_published,
            "warnings": warnings,
            "close_preview": close_preview,
        }

    def publish_report(
        self,
        *,
        organization_id: str,
        report_id: str,
        actor_id: str | None = None,
        source_filename: str | None = None,
        source_content: bytes | None = None,
    ) -> dict:
        record = self._get_org_report(
            organization_id=organization_id,
            report_id=report_id,
        )
        self._ensure_publishable(record)

        published_line_count = self._publish_report_lines(report_id)

        materialization = (
            self.materialization_service.materialize_issues_from_report(
                organization_id=organization_id,
                report_id=report_id,
                actor_id=actor_id,
            )
        )

        record = self.report_repository.get_by_id(report_id) or record
        if source_content:
            record = self._archive_report_pdf_if_needed(
                organization_id=organization_id,
                report_id=report_id,
                record=record,
                source_filename=source_filename or "",
                source_content=source_content,
            )

        project = self.project_repository.get_project_by_id(
            str(record["project_id"])
        )
        project_name = (
            project.get("project_name") if project else None
        )

        serialized = self._serialize_report(
            record,
            project_name=project_name,
        )
        pdf_archived = bool(record.get("pdf_storage_path"))
        publish_warnings: list[str] = []
        if not pdf_archived:
            publish_warnings.append(
                "ה-PDF לא נשמר בארכיון — הפרסום לא הושלם. "
                "יש להעלות PDF בפרסום."
            )
        return {
            **serialized,
            "publish_result": {
                "published_line_count": published_line_count,
                "issue_materialization": materialization.model_dump(
                    mode="json"
                ),
                "pdf_archived": pdf_archived,
                "warnings": publish_warnings,
            },
        }

    def preview_close_report(
        self,
        *,
        organization_id: str,
        report_id: str,
    ) -> dict:
        record = self._get_org_report(
            organization_id=organization_id,
            report_id=report_id,
        )
        self._ensure_editable(record)

        current_catalog_version = (
            self.catalog_service.get_catalog_summary().get(
                "catalog_version"
            )
        )
        lines = self._load_lines(
            report_id,
            current_catalog_version=current_catalog_version,
        )
        return _build_close_preview(lines)

    def close_report(
        self,
        *,
        organization_id: str,
        report_id: str,
        actor_id: str | None = None,
    ) -> dict:
        record = self._get_org_report(
            organization_id=organization_id,
            report_id=report_id,
        )
        self._ensure_editable(record)

        current_catalog_version = (
            self.catalog_service.get_catalog_summary().get(
                "catalog_version"
            )
        )
        lines = self._load_lines(
            report_id,
            current_catalog_version=current_catalog_version,
        )
        close_preview = _build_close_preview(lines)

        updated = self.report_repository.update(
            report_id,
            {
                "status": "CLOSED",
                "closed_at": datetime.now(UTC).isoformat(),
            },
        )

        if not updated:
            raise NotFoundError(
                message="Field visit report not found",
                resource_type="field_visit_report",
                resource_id=report_id,
            )

        materialization = self._materialize_issues_after_close(
            organization_id=organization_id,
            report_id=report_id,
            actor_id=actor_id,
        )

        project = self.project_repository.get_project_by_id(
            str(record["project_id"])
        )
        project_name = (
            project.get("project_name") if project else None
        )

        serialized = self._serialize_report(
            updated,
            project_name=project_name,
        )
        return {
            **serialized,
            "close_preview": close_preview,
            "issue_materialization": materialization,
        }

    def reopen_report(
        self,
        *,
        organization_id: str,
        report_id: str,
    ) -> dict:
        record = self._get_org_report(
            organization_id=organization_id,
            report_id=report_id,
        )
        status = str(record.get("status") or "")

        if status not in REOPENABLE_STATUSES:
            raise ConflictError(
                message="ניתן לערוך שוב רק דוח במצב סגור",
                details={"status": status},
            )

        project_id = str(record["project_id"])
        existing = self.report_repository.get_open_for_project(
            organization_id=organization_id,
            project_id=project_id,
        )

        if existing and str(existing["id"]) != report_id:
            raise ConflictError(
                message=(
                    "כבר קיים דוח בעבודה לפרויקט זה. "
                    "יש לסגור או לשלוח את הדוח הפתוח לפני עריכה מחדש."
                ),
                details={
                    "existing_report_id": str(existing["id"]),
                    "project_id": project_id,
                },
            )

        updated = self.report_repository.update(
            report_id,
            {"status": "IN_PROGRESS"},
        )

        if not updated:
            raise NotFoundError(
                message="Field visit report not found",
                resource_type="field_visit_report",
                resource_id=report_id,
            )

        project = self.project_repository.get_project_by_id(
            project_id
        )
        project_name = (
            project.get("project_name") if project else None
        )

        return self._serialize_report(
            updated,
            project_name=project_name,
        )

    def request_send_to_core(
        self,
        *,
        organization_id: str,
        report_id: str,
        source_filename: str,
        source_content: bytes,
    ) -> dict:
        record = self._get_org_report(
            organization_id=organization_id,
            report_id=report_id,
        )
        status = str(record.get("status") or "")

        project = self.project_repository.get_project_by_id(
            str(record["project_id"])
        )
        project_name = (
            project.get("project_name") if project else None
        )

        # 3D.4 idempotency:
        # If the report was already successfully sent (locked),
        # return the current report state instead of failing the retry.
        if status in {"LOCKED", "PENDING_UPLOAD"}:
            return self._serialize_report(
                record,
                project_name=project_name,
            )

        if status not in SENDABLE_STATUSES:
            raise ConflictError(
                message="ניתן לשלוח לליבה רק דוח במצב סגור",
                details={
                    "status": status,
                    "error_code": REQUEST_SEND_ERROR_CODE_INVALID_STATUS,
                    "retryable": False,
                },
            )

        record = self._archive_report_pdf_if_needed(
            organization_id=organization_id,
            report_id=report_id,
            record=record,
            source_filename=source_filename,
            source_content=source_content,
        )

        core_result = self._send_to_core_pipeline(
            record,
            source_filename=source_filename,
            source_content=source_content,
        )
        if not core_result.get("success"):
            core_error_code = str(
                core_result.get("error_code")
                or REQUEST_SEND_ERROR_CODE_CORE_FAILED
            )
            raise ConflictError(
                message=(
                    core_result.get("error_message")
                    or "שליחה לליבה נכשלה"
                ),
                details={
                    "error_code": core_error_code,
                    "retryable": True,
                },
            )

        lock_payload: dict = {
            "status": "LOCKED",
            "locked_at": datetime.now(UTC).isoformat(),
        }
        core_report_id = core_result.get("report_id")
        if core_report_id:
            lock_payload["core_report_id"] = str(core_report_id)

        updated = self.report_repository.update(
            report_id,
            lock_payload,
        )

        if not updated:
            raise NotFoundError(
                message="Field visit report not found",
                resource_type="field_visit_report",
                resource_id=report_id,
            )

        return self._serialize_report(
            updated,
            project_name=project_name,
        )

    def get_project_field_report_archive(
        self,
        *,
        organization_id: str,
        project_id: str,
    ) -> dict:
        project = self.project_repository.get_project_by_id(project_id)
        if not project:
            raise NotFoundError(
                message="Project not found",
                resource_type="project",
                resource_id=project_id,
            )

        if str(project.get("organization_id") or "") != organization_id:
            raise NotFoundError(
                message="Project not found",
                resource_type="project",
                resource_id=project_id,
            )

        records = self.report_repository.list_archived_by_project(
            organization_id=organization_id,
            project_id=project_id,
        )

        return build_project_field_report_archive(
            records,
            project_id=project_id,
            project_name=project.get("project_name"),
        )

    def get_archived_report_pdf(
        self,
        *,
        organization_id: str,
        report_id: str,
    ) -> tuple[bytes, str, str]:
        record = self._get_org_report(
            organization_id=organization_id,
            report_id=report_id,
        )
        storage_path = str(record.get("pdf_storage_path") or "").strip()
        if not storage_path:
            raise NotFoundError(
                message="Archived PDF not found",
                resource_type="field_visit_report_pdf",
                resource_id=report_id,
            )

        try:
            content, content_type = self.pdf_service.read_pdf(
                storage_path
            )
        except FileNotFoundError as error:
            raise NotFoundError(
                message="Archived PDF file missing on server",
                resource_type="field_visit_report_pdf",
                resource_id=report_id,
            ) from error

        filename = (
            record.get("pdf_filename")
            or self._build_core_upload_filename(record)
        )
        return content, content_type, str(filename)

    def _archive_report_pdf_if_needed(
        self,
        *,
        organization_id: str,
        report_id: str,
        record: dict,
        source_filename: str,
        source_content: bytes,
    ) -> dict:
        existing_path = str(record.get("pdf_storage_path") or "").strip()
        if existing_path:
            return record

        filename = (
            source_filename.strip()
            if source_filename
            else self._build_core_upload_filename(record)
        )
        storage_path, saved_filename = self.pdf_service.save_pdf(
            organization_id=organization_id,
            project_id=str(record["project_id"]),
            report_id=report_id,
            content=source_content,
            filename=filename,
        )

        updated = self.report_repository.update(
            report_id,
            {
                "pdf_storage_path": storage_path,
                "pdf_filename": saved_filename,
            },
        )
        return updated or {
            **record,
            "pdf_storage_path": storage_path,
            "pdf_filename": saved_filename,
        }

    def update_report(
        self,
        *,
        organization_id: str,
        report_id: str,
        visit_date: str | None = None,
        header_fields: dict | None = None,
        catalog_version: str | None = None,
        actor_user_id: str | None = None,
    ) -> dict:
        record = self._get_org_report(
            organization_id=organization_id,
            report_id=report_id,
        )
        self._ensure_editable(record)

        payload: dict = {}
        before_header_fields = record.get("header_fields") or {}
        merged_header_fields: dict | None = None

        if visit_date is not None:
            payload["visit_date"] = visit_date

        if header_fields is not None:
            merged_header_fields = {
                **before_header_fields,
                **header_fields,
            }
            try:
                validate_header_fields_project_dates(
                    merged_header_fields
                )
            except ValueError as error:
                raise ValidationError(str(error)) from error
            payload["header_fields"] = merged_header_fields

        if catalog_version is not None:
            payload["catalog_version"] = catalog_version

        if not payload:
            return self.get_report(
                organization_id=organization_id,
                report_id=report_id,
            )

        updated = self.report_repository.update(report_id, payload)
        if not updated:
            raise NotFoundError(
                message="Field visit report not found",
                resource_type="field_visit_report",
                resource_id=report_id,
            )

        if merged_header_fields is not None:
            self._record_structure_activity_if_changed(
                record=updated,
                before_header_fields=before_header_fields,
                after_header_fields=merged_header_fields,
                actor_id=actor_user_id,
            )

        return self.get_report(
            organization_id=organization_id,
            report_id=report_id,
        )

    def sync_visit_report(
        self,
        *,
        organization_id: str,
        actor_profile_id: str,
        client_report_uuid: str,
        project_id: str,
        visit_type: str,
        visit_date: str,
        header_fields: dict | None = None,
        catalog_version: str | None = None,
        organization_profile_snapshot: dict | None = None,
        status: str | None = None,
        closed_at: str | None = None,
        lines: list[dict] | None = None,
        idempotency_key: str | None = None,
    ) -> dict:
        """
        Upsert דוח+שורות לפי `client_report_uuid` (Tablet Wins, FR-021).
        יצירה אם לא קיים; עדכון אם קיים. מפתח idempotency אופציונלי = UUID הדוח.
        """
        if not self.is_storage_available():
            raise ValidationError(
                message=(
                    "טבלת דוחות ביקור אינה מוגדרת במסד הנתונים. "
                    "יש להריץ את המיגרציה "
                    "db/migrations/2026060102_field_visit_reports.sql"
                ),
            )

        normalized_client_uuid = normalize_client_report_uuid(
            client_report_uuid
        )
        if not normalized_client_uuid:
            raise ValidationError(
                message="client_report_uuid נדרש לסנכרון",
                details={"client_report_uuid": client_report_uuid},
            )

        if idempotency_key:
            key = idempotency_key.strip()
            if key and key != normalized_client_uuid:
                raise ValidationError(
                    message=(
                        "מפתח Idempotency חייב להתאים ל-client_report_uuid"
                    ),
                    details={
                        "idempotency_key": key,
                        "client_report_uuid": normalized_client_uuid,
                    },
                )

        existing = self.report_repository.get_by_client_report_uuid(
            normalized_client_uuid
        )

        if existing:
            report = self._sync_update_existing_report(
                organization_id=organization_id,
                existing=existing,
                project_id=project_id,
                visit_type=visit_type,
                visit_date=visit_date,
                header_fields=header_fields,
                catalog_version=catalog_version,
                organization_profile_snapshot=(
                    organization_profile_snapshot
                ),
                status=status,
                closed_at=closed_at,
                lines=lines or [],
                actor_profile_id=actor_profile_id,
            )
            created = False
        else:
            report = self._sync_create_new_report(
                organization_id=organization_id,
                actor_profile_id=actor_profile_id,
                client_report_uuid=normalized_client_uuid,
                project_id=project_id,
                visit_type=visit_type,
                visit_date=visit_date,
                header_fields=header_fields,
                catalog_version=catalog_version,
                organization_profile_snapshot=(
                    organization_profile_snapshot
                ),
                status=status,
                closed_at=closed_at,
                lines=lines or [],
            )
            created = True

        return {
            "created": created,
            "client_report_uuid": normalized_client_uuid,
            "id": str(report["id"]),
            "report": report,
        }

    def list_lines(
        self,
        *,
        organization_id: str,
        report_id: str,
    ) -> dict:
        record = self._get_org_report(
            organization_id=organization_id,
            report_id=report_id,
        )
        current_catalog_version = self._current_catalog_version()
        lines = self._load_lines(
            str(record["id"]),
            current_catalog_version=current_catalog_version,
        )
        return {
            "lines": lines,
            "total": len(lines),
        }

    def create_line(
        self,
        *,
        organization_id: str,
        report_id: str,
        payload: dict,
    ) -> dict:
        if not self.are_lines_available():
            raise ValidationError(
                message=(
                    "טבלת שורות דוח אינה מוגדרת במסד הנתונים. "
                    "יש להריץ את המיגרציה "
                    "db/migrations/2026060103_field_visit_report_lines.sql"
                ),
            )

        record = self._get_org_report(
            organization_id=organization_id,
            report_id=report_id,
        )
        self._ensure_editable(record)

        line_payload = self._build_line_payload(
            record=record,
            incoming=payload,
            for_create=True,
        )

        client_line_uuid = line_payload.get("client_line_uuid")
        if client_line_uuid:
            existing_line = (
                self.line_repository.get_by_client_line_uuid(
                    client_line_uuid
                )
            )
            if existing_line:
                raise ConflictError(
                    message="שורה עם מזהה מכשיר זה כבר קיימת",
                    details={
                        "client_line_uuid": client_line_uuid,
                        "existing_line_id": str(existing_line["id"]),
                    },
                )

        created = self.line_repository.create(line_payload)
        return self._serialize_line(
            created,
            current_catalog_version=self._current_catalog_version(),
        )

    def update_line(
        self,
        *,
        organization_id: str,
        report_id: str,
        line_id: str,
        payload: dict,
    ) -> dict:
        if not self.are_lines_available():
            raise ValidationError(
                message=(
                    "טבלת שורות דוח אינה מוגדרת במסד הנתונים. "
                    "יש להריץ את המיגרציה "
                    "db/migrations/2026060103_field_visit_report_lines.sql"
                ),
            )

        record = self._get_org_report(
            organization_id=organization_id,
            report_id=report_id,
        )
        self._ensure_editable(record)

        existing = self._get_org_line(
            organization_id=organization_id,
            report_id=report_id,
            line_id=line_id,
        )

        update_payload = self._build_line_update_payload(
            record=record,
            existing=existing,
            incoming=payload,
        )

        current_catalog_version = self._current_catalog_version()
        if not update_payload:
            return self._serialize_line(
                existing,
                current_catalog_version=current_catalog_version,
            )

        updated = self.line_repository.update(line_id, update_payload)
        if not updated:
            raise NotFoundError(
                message="Field visit report line not found",
                resource_type="field_visit_report_line",
                resource_id=line_id,
            )

        return self._serialize_line(
            updated,
            current_catalog_version=current_catalog_version,
        )

    def materialize_draft_issue_from_line(
        self,
        *,
        organization_id: str,
        report_id: str,
        line_id: str,
        actor_id: str | None = None,
        checklist_item_id: str | None = None,
    ) -> dict:
        """Instant-loop L1 — DRAFT quality issue from an in-progress defect line."""
        self._get_org_line(
            organization_id=organization_id,
            report_id=report_id,
            line_id=line_id,
        )

        result = self.materialization_service.materialize_draft_from_defect(
            organization_id=organization_id,
            report_id=report_id,
            line_id=line_id,
            actor_id=actor_id,
            checklist_item_id=checklist_item_id,
        )
        issue = self.materialization_service.issue_repository.get_for_organization(
            issue_id=result.issue_id,
            organization_id=organization_id,
        )
        if issue is None:
            raise NotFoundError(
                message="Quality issue not found after draft materialization",
                resource_type="quality_issue",
                resource_id=result.issue_id,
            )

        response: dict = {
            "draft_materialization": result.model_dump(),
            "issue": parse_quality_issue_row(issue),
        }
        if result.created and self.qc_notification_service is not None:
            notification = self.qc_notification_service.notify_contractor_on_draft_issue(
                organization_id=organization_id,
                project_id=str(issue.get("project_id") or result.project_id),
                report_id=report_id,
                issue_id=result.issue_id,
                line_id=line_id,
                actor_id=actor_id,
            )
            response["draft_notification"] = notification.model_dump()

        return response

    def delete_line(
        self,
        *,
        organization_id: str,
        report_id: str,
        line_id: str,
    ) -> dict:
        if not self.are_lines_available():
            raise ValidationError(
                message=(
                    "טבלת שורות דוח אינה מוגדרת במסד הנתונים. "
                    "יש להריץ את המיגרציה "
                    "db/migrations/2026060103_field_visit_report_lines.sql"
                ),
            )

        record = self._get_org_report(
            organization_id=organization_id,
            report_id=report_id,
        )
        self._ensure_editable(record)

        existing = self._get_org_line(
            organization_id=organization_id,
            report_id=report_id,
            line_id=line_id,
        )

        self._delete_all_line_photos(existing)

        self.line_repository.delete(line_id)
        return {"deleted": True, "id": line_id}

    def list_line_photos(
        self,
        *,
        organization_id: str,
        report_id: str,
        line_id: str,
    ) -> dict:
        if not self.are_lines_available():
            raise ValidationError(
                message=(
                    "טבלת שורות דוח אינה מוגדרת במסד הנתונים. "
                    "יש להריץ את המיגרציה "
                    "db/migrations/2026060103_field_visit_report_lines.sql"
                ),
            )

        self._get_org_report(
            organization_id=organization_id,
            report_id=report_id,
        )
        existing = self._get_org_line(
            organization_id=organization_id,
            report_id=report_id,
            line_id=line_id,
        )
        return self._serialize_line_photos_payload(
            report_id=report_id,
            line_id=line_id,
            photos=self._photos_for_line(existing),
        )

    def upload_line_photo(
        self,
        *,
        organization_id: str,
        report_id: str,
        line_id: str,
        content: bytes,
        content_type: str | None,
        filename: str | None = None,
    ) -> dict:
        if not self.are_lines_available():
            raise ValidationError(
                message=(
                    "טבלת שורות דוח אינה מוגדרת במסד הנתונים. "
                    "יש להריץ את המיגרציה "
                    "db/migrations/2026060103_field_visit_report_lines.sql"
                ),
            )

        record = self._get_org_report(
            organization_id=organization_id,
            report_id=report_id,
        )
        self._ensure_editable(record)

        existing = self._get_org_line(
            organization_id=organization_id,
            report_id=report_id,
            line_id=line_id,
        )

        self._delete_all_line_photos(existing)
        updated = self._store_line_photo(
            organization_id=organization_id,
            report_id=report_id,
            line=existing,
            content=content,
            content_type=content_type,
            filename=filename,
        )
        return self._serialize_line(updated)

    def add_line_photo(
        self,
        *,
        organization_id: str,
        report_id: str,
        line_id: str,
        content: bytes,
        content_type: str | None,
        filename: str | None = None,
    ) -> dict:
        if not self.are_lines_available():
            raise ValidationError(
                message=(
                    "טבלת שורות דוח אינה מוגדרת במסד הנתונים. "
                    "יש להריץ את המיגרציה "
                    "db/migrations/2026060103_field_visit_report_lines.sql"
                ),
            )

        record = self._get_org_report(
            organization_id=organization_id,
            report_id=report_id,
        )
        self._ensure_editable(record)

        existing = self._get_org_line(
            organization_id=organization_id,
            report_id=report_id,
            line_id=line_id,
        )
        existing = self._migrate_legacy_line_photo(
            organization_id=organization_id,
            report_id=report_id,
            line=existing,
        )
        photos = self._photos_for_line(existing)
        if len(photos) >= MAX_LINE_PHOTOS:
            raise ValidationError(
                message=f"ניתן לצרף עד {MAX_LINE_PHOTOS} תמונות לשורה",
            )

        updated = self._store_line_photo(
            organization_id=organization_id,
            report_id=report_id,
            line=existing,
            content=content,
            content_type=content_type,
            filename=filename,
        )
        return self._serialize_line(updated)

    def add_line_photo_by_client_uuids(
        self,
        *,
        organization_id: str,
        client_report_uuid: str,
        client_line_uuid: str,
        content: bytes,
        content_type: str | None,
        filename: str | None = None,
        idempotency_key: str | None = None,
    ) -> dict:
        """
        העלאת תמונה לשורה לפי מזהי קליינט (§7 ג.ב.4, FR-023).
        הדוח חייב להיות מסונכרן קודם (`PUT .../visits/sync`).
        """
        if not self.are_lines_available():
            raise ValidationError(
                message=(
                    "טבלת שורות דוח אינה מוגדרת במסד הנתונים. "
                    "יש להריץ את המיגרציה "
                    "db/migrations/2026060103_field_visit_report_lines.sql"
                ),
            )

        report, line = self._resolve_sync_line_by_client_uuids(
            organization_id=organization_id,
            client_report_uuid=client_report_uuid,
            client_line_uuid=client_line_uuid,
            idempotency_key=idempotency_key,
        )
        self._ensure_syncable(report)

        report_id = str(report["id"])
        line_id = str(line["id"])
        existing = self._migrate_legacy_line_photo(
            organization_id=organization_id,
            report_id=report_id,
            line=line,
        )
        photos = self._photos_for_line(existing)
        if len(photos) >= MAX_LINE_PHOTOS:
            raise ValidationError(
                message=f"ניתן לצרף עד {MAX_LINE_PHOTOS} תמונות לשורה",
            )

        updated = self._store_line_photo(
            organization_id=organization_id,
            report_id=report_id,
            line=existing,
            content=content,
            content_type=content_type,
            filename=filename,
        )
        return self._serialize_line(updated)

    def get_line_photo(
        self,
        *,
        organization_id: str,
        report_id: str,
        line_id: str,
    ) -> tuple[bytes, str]:
        if not self.are_lines_available():
            raise ValidationError(
                message=(
                    "טבלת שורות דוח אינה מוגדרת במסד הנתונים. "
                    "יש להריץ את המיגרציה "
                    "db/migrations/2026060103_field_visit_report_lines.sql"
                ),
            )

        self._get_org_report(
            organization_id=organization_id,
            report_id=report_id,
        )
        existing = self._get_org_line(
            organization_id=organization_id,
            report_id=report_id,
            line_id=line_id,
        )

        photos = self._photos_for_line(existing)
        if not photos:
            raise NotFoundError(
                message="Line photo not found",
                resource_type="field_visit_report_line_photo",
                resource_id=line_id,
            )

        return self._read_photo_record(photos[0])

    def get_line_photo_by_id(
        self,
        *,
        organization_id: str,
        report_id: str,
        line_id: str,
        photo_id: str,
    ) -> tuple[bytes, str]:
        if not self.are_lines_available():
            raise ValidationError(
                message=(
                    "טבלת שורות דוח אינה מוגדרת במסד הנתונים. "
                    "יש להריץ את המיגרציה "
                    "db/migrations/2026060103_field_visit_report_lines.sql"
                ),
            )

        self._get_org_report(
            organization_id=organization_id,
            report_id=report_id,
        )
        existing = self._get_org_line(
            organization_id=organization_id,
            report_id=report_id,
            line_id=line_id,
        )
        photo = self._find_line_photo(existing, photo_id)
        if not photo:
            raise NotFoundError(
                message="Line photo not found",
                resource_type="field_visit_report_line_photo",
                resource_id=photo_id,
            )

        return self._read_photo_record(photo)

    def delete_line_photo(
        self,
        *,
        organization_id: str,
        report_id: str,
        line_id: str,
    ) -> dict:
        if not self.are_lines_available():
            raise ValidationError(
                message=(
                    "טבלת שורות דוח אינה מוגדרת במסד הנתונים. "
                    "יש להריץ את המיגרציה "
                    "db/migrations/2026060103_field_visit_report_lines.sql"
                ),
            )

        record = self._get_org_report(
            organization_id=organization_id,
            report_id=report_id,
        )
        self._ensure_editable(record)

        existing = self._get_org_line(
            organization_id=organization_id,
            report_id=report_id,
            line_id=line_id,
        )

        self._delete_all_line_photos(existing)
        updated = self.line_repository.update(
            line_id,
            {"photo_storage_path": None},
        )
        if not updated:
            raise NotFoundError(
                message="Field visit report line not found",
                resource_type="field_visit_report_line",
                resource_id=line_id,
            )

        return self._serialize_line(updated)

    def delete_line_photo_by_id(
        self,
        *,
        organization_id: str,
        report_id: str,
        line_id: str,
        photo_id: str,
    ) -> dict:
        if not self.are_lines_available():
            raise ValidationError(
                message=(
                    "טבלת שורות דוח אינה מוגדרת במסד הנתונים. "
                    "יש להריץ את המיגרציה "
                    "db/migrations/2026060103_field_visit_report_lines.sql"
                ),
            )

        record = self._get_org_report(
            organization_id=organization_id,
            report_id=report_id,
        )
        self._ensure_editable(record)

        existing = self._get_org_line(
            organization_id=organization_id,
            report_id=report_id,
            line_id=line_id,
        )
        photo = self._find_line_photo(existing, photo_id)
        if not photo:
            raise NotFoundError(
                message="Line photo not found",
                resource_type="field_visit_report_line_photo",
                resource_id=photo_id,
            )

        self._delete_photo_record(existing, photo)
        refreshed = self.line_repository.get_by_id(line_id) or existing
        updated = self._sync_line_primary_storage_path(refreshed)
        return self._serialize_line(updated)

    def _get_org_line(
        self,
        *,
        organization_id: str,
        report_id: str,
        line_id: str,
    ) -> dict:
        existing = self.line_repository.get_by_id(line_id)
        if (
            not existing
            or str(existing.get("report_id")) != report_id
            or str(existing.get("organization_id")) != organization_id
        ):
            raise NotFoundError(
                message="Field visit report line not found",
                resource_type="field_visit_report_line",
                resource_id=line_id,
            )
        return existing

    def _build_line_payload(
        self,
        *,
        record: dict,
        incoming: dict,
        for_create: bool,
    ) -> dict:
        visit_type = str(record.get("visit_type") or "")
        report_id = str(record["id"])
        organization_id = str(record["organization_id"])

        normalized = dict(incoming)
        issue_id = normalized.get("issue_id")
        if issue_id:
            issue_id = str(issue_id).strip().upper()
            normalized["issue_id"] = issue_id
            catalog_issue = self.catalog_service.find_issue(issue_id)
            if not catalog_issue:
                raise ValidationError(
                    message="ממצא לא נמצא בקטלוג",
                    details={"issue_id": issue_id},
                )
            allowed = set(allowed_top_families(visit_type))
            if catalog_issue["top_family"] not in allowed:
                raise ValidationError(
                    message=(
                        "ממצא זה אינו זמין לסוג הביקור שנבחר"
                    ),
                    details={
                        "issue_id": issue_id,
                        "visit_type": visit_type,
                    },
                )
            normalized = _apply_catalog_issue_defaults(
                normalized,
                catalog_issue,
                catalog_version=record.get("catalog_version"),
            )
        else:
            normalized["issue_id"] = None
            normalized["standard_ref"] = None
            normalized["top_family"] = None
            normalized["category_id"] = None
            normalized["category_name_he"] = None

        sort_order = normalized.pop("sort_order", None)
        if sort_order is None and for_create:
            sort_order = self.line_repository.next_sort_order(
                report_id
            )

        client_line_uuid = None
        if for_create and "client_line_uuid" in incoming:
            client_line_uuid = normalize_client_line_uuid(
                incoming.get("client_line_uuid")
            )

        payload = {
            "report_id": report_id,
            "organization_id": organization_id,
            "sort_order": sort_order or 0,
            "location": normalized.get("location"),
            "trade": normalized.get("trade"),
            "status": normalized.get("status"),
            "description": normalized.get("description"),
            "notes": normalized.get("notes"),
            "severity": normalized.get("severity"),
            "standard_ref": normalized.get("standard_ref"),
            "catalog_reference_id": normalized.get("catalog_reference_id"),
            "engineering_impact": normalized.get(
                "engineering_impact"
            ),
            "issue_id": normalized.get("issue_id"),
            "catalog_version": normalized.get("catalog_version"),
            "top_family": normalized.get("top_family"),
            "category_id": normalized.get("category_id"),
            "category_name_he": normalized.get("category_name_he"),
            "group_key": normalized.get("group_key"),
            "group_label_he": normalized.get("group_label_he"),
            "block_id": normalized.get("block_id"),
            "linked_issue_id": normalized.get("linked_issue_id"),
        }

        if for_create:
            payload["visibility"] = (
                normalized.get("visibility") or DEFAULT_ISSUE_VISIBILITY.value
            )

        if client_line_uuid:
            payload["client_line_uuid"] = client_line_uuid

        return payload

    def _build_line_update_payload(
        self,
        *,
        record: dict,
        existing: dict,
        incoming: dict,
    ) -> dict:
        if "issue_id" in incoming and incoming["issue_id"] is None:
            merged = {
                **existing,
                **incoming,
                "issue_id": None,
                "standard_ref": None,
                "catalog_reference_id": None,
                "top_family": None,
                "category_id": None,
                "category_name_he": None,
                "catalog_version": None,
            }
            editable_keys = (
                "location",
                "trade",
                "status",
                "description",
                "notes",
                "severity",
                "engineering_impact",
                "sort_order",
                "group_key",
                "group_label_he",
                "block_id",
                "linked_issue_id",
            )
            payload = {
                key: merged.get(key)
                for key in editable_keys
                if key in incoming
            }
            payload.update(
                {
                    "issue_id": None,
                    "standard_ref": None,
                    "top_family": None,
                    "category_id": None,
                    "category_name_he": None,
                    "catalog_version": None,
                }
            )
            return payload

        if incoming.get("issue_id"):
            return self._build_line_payload(
                record=record,
                incoming={
                    **existing,
                    **incoming,
                },
                for_create=False,
            )

        update_payload = {}
        for key in (
            "location",
            "trade",
            "status",
            "description",
            "notes",
            "severity",
            "engineering_impact",
            "sort_order",
            "group_key",
            "group_label_he",
            "block_id",
            "linked_issue_id",
        ):
            if key in incoming:
                update_payload[key] = incoming[key]

        if existing.get("issue_id"):
            if "standard_ref" in incoming:
                raise ValidationError(
                    message=(
                        "לא ניתן לערוך תקן כשהשורה מקושרת לממצא במפרט"
                    ),
                )

        return update_payload

    def _current_catalog_version(self) -> str | None:
        return self.catalog_service.get_catalog_summary().get(
            "catalog_version"
        )

    def _materialize_issues_after_close(
        self,
        *,
        organization_id: str,
        report_id: str,
        actor_id: str | None,
    ) -> dict | None:
        record = self.report_repository.get_by_id(report_id)
        if record is None or str(record.get("organization_id")) != organization_id:
            return None

        result = MaterializationResult(
            report_id=report_id,
            project_id=str(record.get("project_id") or ""),
            created_count=0,
            linked_count=0,
            skipped_count=0,
        )
        return result.model_dump(mode="json")

    def _publish_report_lines(self, report_id: str) -> int:
        if not self.are_lines_available():
            return 0

        published_count = 0
        for line in self.line_repository.list_by_report(report_id):
            if (
                str(line.get("visibility") or IssueVisibility.DRAFT.value)
                != IssueVisibility.PUBLISHED.value
            ):
                self.line_repository.update(
                    str(line["id"]),
                    {"visibility": IssueVisibility.PUBLISHED.value},
                )
                published_count += 1
        return published_count

    def _lines_for_materialization(self, report_id: str) -> list[dict]:
        if not self.are_lines_available():
            return []

        serialized: list[dict] = []
        for line in self.line_repository.list_by_report(report_id):
            line_id = str(line["id"])
            photos = self._photos_for_line(line)
            photo_ids = [str(photo["id"]) for photo in photos]
            serialized.append(
                {
                    "id": line_id,
                    "location": line.get("location"),
                    "trade": line.get("trade"),
                    "description": line.get("description"),
                    "notes": line.get("notes"),
                    "severity": line.get("severity"),
                    "standard_ref": line.get("standard_ref"),
                    "catalog_reference_id": line.get("catalog_reference_id"),
                    "issue_id": line.get("issue_id"),
                    "group_key": line.get("group_key"),
                    "group_label_he": line.get("group_label_he"),
                    "linked_issue_id": line.get("linked_issue_id"),
                    "photo_ids": photo_ids,
                    "has_photo": bool(photo_ids),
                }
            )
        return serialized

    @staticmethod
    def _is_report_published(record: dict, lines: list[dict]) -> bool:
        if lines:
            return all(
                str(line.get("visibility") or IssueVisibility.DRAFT.value)
                == IssueVisibility.PUBLISHED.value
                for line in lines
            )
        return bool(record.get("pdf_storage_path"))

    @staticmethod
    def _report_publish_flags(
        *,
        record: dict,
        lines: list[dict],
    ) -> dict[str, bool]:
        status = str(record.get("status") or "")
        is_published = FieldVisitReportService._is_report_published(
            record,
            lines,
        )
        can_publish = status in PUBLISHABLE_STATUSES and not is_published
        return {
            "is_published": is_published,
            "can_publish": can_publish,
            "pending_publish": can_publish,
        }

    @staticmethod
    def _ensure_publishable(record: dict) -> None:
        status = str(record.get("status") or "")
        if status not in PUBLISHABLE_STATUSES:
            raise ConflictError(
                message="ניתן לפרסם רק דוח במצב סגור",
                details={"status": status},
            )

    def _load_lines(
        self,
        report_id: str,
        *,
        current_catalog_version: str | None = None,
    ) -> list[dict]:
        if not self.are_lines_available():
            return []

        return [
            self._serialize_line(
                line,
                current_catalog_version=current_catalog_version,
            )
            for line in self.line_repository.list_by_report(
                report_id
            )
        ]

    def _get_org_report(
        self,
        *,
        organization_id: str,
        report_id: str,
    ) -> dict:
        record = self.report_repository.get_by_id(report_id)

        if not record or str(record.get("organization_id")) != organization_id:
            raise NotFoundError(
                message="Field visit report not found",
                resource_type="field_visit_report",
                resource_id=report_id,
            )

        return record

    def _resolve_sync_line_by_client_uuids(
        self,
        *,
        organization_id: str,
        client_report_uuid: str,
        client_line_uuid: str,
        idempotency_key: str | None = None,
    ) -> tuple[dict, dict]:
        normalized_report_uuid = normalize_client_report_uuid(
            client_report_uuid
        )
        if not normalized_report_uuid:
            raise ValidationError(
                message="client_report_uuid נדרש",
                details={"client_report_uuid": client_report_uuid},
            )

        normalized_line_uuid = normalize_client_line_uuid(
            client_line_uuid
        )
        if not normalized_line_uuid:
            raise ValidationError(
                message="client_line_uuid נדרש",
                details={"client_line_uuid": client_line_uuid},
            )

        if idempotency_key:
            key = idempotency_key.strip()
            if key and key != normalized_line_uuid:
                raise ValidationError(
                    message=(
                        "מפתח Idempotency חייב להתאים ל-client_line_uuid"
                    ),
                    details={
                        "idempotency_key": key,
                        "client_line_uuid": normalized_line_uuid,
                    },
                )

        report = self.report_repository.get_by_client_report_uuid(
            normalized_report_uuid
        )
        if (
            not report
            or str(report.get("organization_id")) != organization_id
        ):
            raise NotFoundError(
                message="Field visit report not found",
                resource_type="field_visit_report",
                resource_id=normalized_report_uuid,
            )

        line = self.line_repository.get_by_client_line_uuid(
            normalized_line_uuid
        )
        if (
            not line
            or str(line.get("report_id")) != str(report["id"])
            or str(line.get("organization_id")) != organization_id
        ):
            raise NotFoundError(
                message="Field visit report line not found",
                resource_type="field_visit_report_line",
                resource_id=normalized_line_uuid,
            )

        return report, line

    @staticmethod
    def _ensure_editable(record: dict) -> None:
        status = str(record.get("status") or "")
        if status not in EDITABLE_STATUSES:
            raise ConflictError(
                message="הדוח אינו במצב עריכה",
                details={"status": status},
            )

    @staticmethod
    def _ensure_syncable(record: dict) -> None:
        status = str(record.get("status") or "")
        if status not in SYNCABLE_STATUSES:
            raise ConflictError(
                message="לא ניתן לסנכרן דוח במצב זה",
                details={"status": status},
            )

    def _sync_create_new_report(
        self,
        *,
        organization_id: str,
        actor_profile_id: str,
        client_report_uuid: str,
        project_id: str,
        visit_type: str,
        visit_date: str,
        header_fields: dict | None,
        catalog_version: str | None,
        organization_profile_snapshot: dict | None,
        status: str | None,
        closed_at: str | None,
        lines: list[dict],
    ) -> dict:
        if not is_valid_visit_type(visit_type):
            raise ValidationError(
                message="סוג ביקור לא תקין",
                details={"visit_type": visit_type},
            )

        project = self.project_repository.get_project_by_id(
            project_id
        )
        if (
            not project
            or str(project.get("organization_id")) != organization_id
        ):
            raise NotFoundError(
                message="Project not found",
                resource_type="project",
                resource_id=project_id,
            )

        open_report = self.report_repository.get_open_for_project(
            organization_id=organization_id,
            project_id=project_id,
        )
        if open_report:
            raise ConflictError(
                message=(
                    "כבר קיים דוח בעבודה לפרויקט זה. "
                    "יש להמשיך את הדוח הקיים או לסגור אותו."
                ),
                details={
                    "existing_report_id": str(open_report["id"]),
                    "project_id": project_id,
                },
            )

        merged_header_fields = _merge_header_fields(
            project,
            header_fields,
            visit_type=visit_type,
            visit_date=visit_date,
        )
        resolved_catalog_version = (
            catalog_version
            or self.catalog_service.get_catalog_summary().get(
                "catalog_version"
            )
        )

        record = self.report_repository.create(
            organization_id=organization_id,
            project_id=project_id,
            created_by_profile_id=actor_profile_id,
            visit_type=visit_type,
            visit_date=visit_date,
            header_fields=merged_header_fields,
            catalog_version=resolved_catalog_version,
            organization_profile_snapshot=organization_profile_snapshot,
            client_report_uuid=client_report_uuid,
        )

        if lines:
            if not self.are_lines_available():
                raise ValidationError(
                    message=(
                        "טבלת שורות דוח אינה מוגדרת במסד הנתונים. "
                        "יש להריץ את המיגרציה "
                        "db/migrations/2026060103_field_visit_report_lines.sql"
                    ),
                )
            record = self._sync_lines_for_report(
                record=record,
                incoming_lines=lines,
            )

        status_update = self._build_sync_status_payload(
            status=status,
            closed_at=closed_at,
        )
        if status_update:
            updated = self.report_repository.update(
                str(record["id"]),
                status_update,
            )
            if updated:
                record = updated

        return self._serialize_report(
            record,
            project_name=project.get("project_name"),
        )

    def _sync_update_existing_report(
        self,
        *,
        organization_id: str,
        existing: dict,
        project_id: str,
        visit_type: str,
        visit_date: str,
        header_fields: dict | None,
        catalog_version: str | None,
        organization_profile_snapshot: dict | None,
        status: str | None,
        closed_at: str | None,
        lines: list[dict],
        actor_profile_id: str | None = None,
    ) -> dict:
        report_id = str(existing["id"])

        if str(existing.get("organization_id")) != organization_id:
            raise NotFoundError(
                message="Field visit report not found",
                resource_type="field_visit_report",
                resource_id=report_id,
            )

        self._ensure_syncable(existing)

        if str(existing.get("project_id")) != project_id:
            raise ValidationError(
                message="לא ניתן לשנות פרויקט בדוח מסונכרן",
                details={
                    "project_id": project_id,
                    "existing_project_id": str(existing["project_id"]),
                },
            )

        if not is_valid_visit_type(visit_type):
            raise ValidationError(
                message="סוג ביקור לא תקין",
                details={"visit_type": visit_type},
            )

        project = self.project_repository.get_project_by_id(
            project_id
        )
        project_name = project.get("project_name") if project else None

        update_payload: dict = {
            "visit_type": visit_type,
            "visit_date": visit_date,
        }
        before_header_fields = existing.get("header_fields") or {}
        merged_header_fields: dict | None = None

        if header_fields is not None:
            merged_header_fields = {
                **before_header_fields,
                **header_fields,
            }
            try:
                validate_header_fields_project_dates(
                    merged_header_fields
                )
            except ValueError as error:
                raise ValidationError(str(error)) from error
            update_payload["header_fields"] = merged_header_fields

        if catalog_version is not None:
            update_payload["catalog_version"] = catalog_version

        if organization_profile_snapshot is not None:
            update_payload["organization_profile_snapshot"] = (
                organization_profile_snapshot
            )

        update_payload.update(
            self._build_sync_status_payload(
                status=status,
                closed_at=closed_at,
            )
        )

        record = self.report_repository.update(
            report_id,
            update_payload,
        )
        if not record:
            raise NotFoundError(
                message="Field visit report not found",
                resource_type="field_visit_report",
                resource_id=report_id,
            )

        if merged_header_fields is not None:
            self._record_structure_activity_if_changed(
                record=record,
                before_header_fields=before_header_fields,
                after_header_fields=merged_header_fields,
                actor_id=actor_profile_id,
            )

        if lines:
            if not self.are_lines_available():
                raise ValidationError(
                    message=(
                        "טבלת שורות דוח אינה מוגדרת במסד הנתונים. "
                        "יש להריץ את המיגרציה "
                        "db/migrations/2026060103_field_visit_report_lines.sql"
                    ),
                )
            record = self._sync_lines_for_report(
                record=record,
                incoming_lines=lines,
            )

        return self._serialize_report(
            record,
            project_name=project_name,
        )

    def _sync_lines_for_report(
        self,
        *,
        record: dict,
        incoming_lines: list[dict],
    ) -> dict:
        report_id = str(record["id"])
        existing_lines = self.line_repository.list_by_report(report_id)
        existing_by_client = {
            str(line["client_line_uuid"]): line
            for line in existing_lines
            if line.get("client_line_uuid")
        }
        seen_client_uuids: set[str] = set()

        for incoming in incoming_lines:
            client_line_uuid = normalize_client_line_uuid(
                incoming.get("client_line_uuid")
            )
            if not client_line_uuid:
                raise ValidationError(
                    message="כל שורה בסנכרון חייבת client_line_uuid",
                )

            seen_client_uuids.add(client_line_uuid)

            if client_line_uuid in existing_by_client:
                existing_line = existing_by_client[client_line_uuid]
                update_payload = self._build_line_update_payload(
                    record=record,
                    existing=existing_line,
                    incoming=incoming,
                )
                if update_payload:
                    updated = self.line_repository.update(
                        str(existing_line["id"]),
                        update_payload,
                    )
                    if updated:
                        existing_by_client[client_line_uuid] = updated
            else:
                line_payload = self._build_line_payload(
                    record=record,
                    incoming=incoming,
                    for_create=True,
                )
                created = self.line_repository.create(line_payload)
                existing_by_client[client_line_uuid] = created

        for existing_line in existing_lines:
            client_line_uuid = existing_line.get("client_line_uuid")
            if not client_line_uuid:
                continue
            if str(client_line_uuid) not in seen_client_uuids:
                self._delete_all_line_photos(existing_line)
                self.line_repository.delete(str(existing_line["id"]))

        refreshed = self.report_repository.get_by_id(report_id)
        return refreshed or record

    @staticmethod
    def _build_sync_status_payload(
        *,
        status: str | None,
        closed_at: str | None,
    ) -> dict:
        if not status:
            return {}

        if status == "CLOSED":
            payload: dict = {"status": "CLOSED"}
            if closed_at:
                payload["closed_at"] = closed_at
            else:
                payload["closed_at"] = datetime.now(UTC).isoformat()
            return payload

        if status == "IN_PROGRESS":
            return {
                "status": "IN_PROGRESS",
                "closed_at": None,
            }

        raise ValidationError(
            message="סטטוס לא נתמך לסנכרון",
            details={"status": status},
        )

    def _serialize_report(
        self,
        record: dict,
        *,
        project_name: str | None = None,
        include_lines: bool = True,
    ) -> dict:
        status = str(record.get("status") or "IN_PROGRESS")
        visit_type = str(record.get("visit_type") or "")
        report_id = str(record["id"])
        current_catalog_version = (
            self.catalog_service.get_catalog_summary().get(
                "catalog_version"
            )
        )
        lines = (
            self._load_lines(
                report_id,
                current_catalog_version=current_catalog_version,
            )
            if include_lines
            else []
        )
        report_catalog_version = record.get("catalog_version")
        catalog_sync = _catalog_sync_state(
            report_catalog_version=report_catalog_version,
            current_catalog_version=current_catalog_version,
        )
        publish_flags = self._report_publish_flags(
            record=record,
            lines=lines,
        )

        return {
            "id": report_id,
            "client_report_uuid": record.get("client_report_uuid"),
            "organization_id": str(record["organization_id"]),
            "project_id": str(record["project_id"]),
            "project_name": project_name,
            "created_by_profile_id": str(
                record["created_by_profile_id"]
            ),
            "visit_type": visit_type,
            "visit_type_label_he": _visit_type_label(visit_type),
            "status": status,
            "status_label_he": VISIT_STATUS_LABELS_HE.get(
                status,
                status,
            ),
            "visit_date": record.get("visit_date"),
            "header_fields": record.get("header_fields") or {},
            "catalog_version": report_catalog_version,
            "current_catalog_version": current_catalog_version,
            "catalog_sync": catalog_sync,
            "closed_at": record.get("closed_at"),
            "locked_at": record.get("locked_at"),
            "created_at": record.get("created_at"),
            "updated_at": record.get("updated_at"),
            "lines": lines,
            "line_count": len(lines),
            "is_editable": status in EDITABLE_STATUSES,
            "can_reopen": status in REOPENABLE_STATUSES,
            "can_send_to_core": status in SENDABLE_STATUSES,
            "can_publish": publish_flags["can_publish"],
            "is_published": publish_flags["is_published"],
            "pending_publish": publish_flags["pending_publish"],
            "was_closed": bool(record.get("closed_at")),
            "organization_profile_snapshot": (
                record.get("organization_profile_snapshot")
            ),
            "pdf_filename": record.get("pdf_filename"),
            "has_archived_pdf": bool(record.get("pdf_storage_path")),
            "core_report_id": record.get("core_report_id"),
        }

    def _line_photo_url(
        self,
        *,
        report_id: str,
        line_id: str,
        photo_id: str,
    ) -> str:
        if photo_id == LEGACY_LINE_PHOTO_ID:
            return (
                f"/field-reports/visits/{report_id}/lines/{line_id}/photo"
            )
        return (
            f"/field-reports/visits/{report_id}/lines/{line_id}"
            f"/photos/{photo_id}"
        )

    def _photos_for_line(self, line: dict) -> list[dict]:
        line_id = str(line["id"])
        if self.are_line_photos_available():
            photos = self.line_photo_repository.list_by_line(line_id)
            if photos:
                return photos

        legacy_path = line.get("photo_storage_path")
        if legacy_path:
            return [
                {
                    "id": LEGACY_LINE_PHOTO_ID,
                    "line_id": line_id,
                    "storage_path": legacy_path,
                    "sort_order": 0,
                }
            ]

        return []

    def _find_line_photo(
        self,
        line: dict,
        photo_id: str,
    ) -> dict | None:
        for photo in self._photos_for_line(line):
            if str(photo.get("id")) == photo_id:
                return photo
        return None

    def _read_photo_record(self, photo: dict) -> tuple[bytes, str]:
        storage_path = photo.get("storage_path")
        if not storage_path:
            raise NotFoundError(
                message="Line photo file not found",
                resource_type="field_visit_report_line_photo",
                resource_id=str(photo.get("id")),
            )

        try:
            return self.photo_service.read_photo(str(storage_path))
        except FileNotFoundError as error:
            raise NotFoundError(
                message="Line photo file not found",
                resource_type="field_visit_report_line_photo",
                resource_id=str(photo.get("id")),
            ) from error

    def _serialize_line_photos_payload(
        self,
        *,
        report_id: str,
        line_id: str,
        photos: list[dict],
    ) -> dict:
        serialized = [
            {
                "id": str(photo["id"]),
                "url": self._line_photo_url(
                    report_id=report_id,
                    line_id=line_id,
                    photo_id=str(photo["id"]),
                ),
                "sort_order": int(photo.get("sort_order") or 0),
            }
            for photo in photos
        ]
        return {
            "line_id": line_id,
            "photo_ids": [item["id"] for item in serialized],
            "photos": serialized,
        }

    def _migrate_legacy_line_photo(
        self,
        *,
        organization_id: str,
        report_id: str,
        line: dict,
    ) -> dict:
        if not self.are_line_photos_available():
            return line

        line_id = str(line["id"])
        if self.line_photo_repository.list_by_line(line_id):
            return line

        legacy_path = line.get("photo_storage_path")
        if not legacy_path:
            return line

        photo_id = str(uuid4())
        self.line_photo_repository.create(
            {
                "id": photo_id,
                "organization_id": organization_id,
                "report_id": report_id,
                "line_id": line_id,
                "storage_path": legacy_path,
                "sort_order": 0,
            }
        )
        return self.line_repository.get_by_id(line_id) or line

    def _store_line_photo(
        self,
        *,
        organization_id: str,
        report_id: str,
        line: dict,
        content: bytes,
        content_type: str | None,
        filename: str | None,
    ) -> dict:
        line_id = str(line["id"])
        line = self._migrate_legacy_line_photo(
            organization_id=organization_id,
            report_id=report_id,
            line=line,
        )
        photo_id = str(uuid4())
        storage_path = self.photo_service.save_photo(
            organization_id=organization_id,
            report_id=report_id,
            line_id=line_id,
            content=content,
            content_type=content_type,
            filename=filename,
            photo_id=photo_id if self.are_line_photos_available() else None,
        )

        if self.are_line_photos_available():
            self.line_photo_repository.create(
                {
                    "id": photo_id,
                    "organization_id": organization_id,
                    "report_id": report_id,
                    "line_id": line_id,
                    "storage_path": storage_path,
                    "sort_order": self.line_photo_repository.next_sort_order(
                        line_id
                    ),
                }
            )
            refreshed = self.line_repository.get_by_id(line_id) or line
            return self._sync_line_primary_storage_path(refreshed)

        updated = self.line_repository.update(
            line_id,
            {"photo_storage_path": storage_path},
        )
        if not updated:
            self.photo_service.delete_photo(storage_path)
            raise NotFoundError(
                message="Field visit report line not found",
                resource_type="field_visit_report_line",
                resource_id=line_id,
            )

        return updated

    def _sync_line_primary_storage_path(self, line: dict) -> dict:
        line_id = str(line["id"])
        photos = self._photos_for_line(line)
        primary_path = (
            str(photos[0]["storage_path"]) if photos else None
        )
        updated = self.line_repository.update(
            line_id,
            {"photo_storage_path": primary_path},
        )
        return updated or line

    def _delete_photo_record(self, line: dict, photo: dict) -> None:
        storage_path = photo.get("storage_path")
        if storage_path:
            self.photo_service.delete_photo(str(storage_path))

        photo_id = str(photo.get("id"))
        if (
            self.are_line_photos_available()
            and photo_id != LEGACY_LINE_PHOTO_ID
        ):
            self.line_photo_repository.delete(photo_id)
        elif photo_id == LEGACY_LINE_PHOTO_ID:
            self.line_repository.update(
                str(line["id"]),
                {"photo_storage_path": None},
            )

    def _delete_all_line_photos(self, line: dict) -> None:
        line_id = str(line["id"])
        for photo in self._photos_for_line(line):
            storage_path = photo.get("storage_path")
            if storage_path:
                self.photo_service.delete_photo(str(storage_path))

        if self.are_line_photos_available():
            self.line_photo_repository.delete_by_line(line_id)

        self.line_repository.update(
            line_id,
            {"photo_storage_path": None},
        )

    def _serialize_line(
        self,
        record: dict,
        *,
        current_catalog_version: str | None = None,
    ) -> dict:
        issue_id = record.get("issue_id")
        line_id = str(record["id"])
        report_id = str(record["report_id"])
        photos = self._photos_for_line(record)
        photo_storage_path = (
            photos[0].get("storage_path") if photos else None
        )
        has_photo = bool(photos)
        photo_ids = [str(photo["id"]) for photo in photos]
        serialized_photos = self._serialize_line_photos_payload(
            report_id=report_id,
            line_id=line_id,
            photos=photos,
        )["photos"]
        catalog_warning = _line_catalog_warning(
            issue_id=issue_id,
            line_catalog_version=record.get("catalog_version"),
            current_catalog_version=current_catalog_version,
            catalog_issue=(
                self.catalog_service.find_issue(str(issue_id))
                if issue_id
                else None
            ),
        )
        return {
            "id": line_id,
            "client_line_uuid": record.get("client_line_uuid"),
            "report_id": report_id,
            "sort_order": int(record.get("sort_order") or 0),
            "location": record.get("location"),
            "trade": record.get("trade"),
            "status": record.get("status"),
            "description": record.get("description"),
            "notes": record.get("notes"),
            "severity": record.get("severity"),
            "standard_ref": record.get("standard_ref"),
            "engineering_impact": record.get("engineering_impact"),
            "issue_id": issue_id,
            "catalog_version": record.get("catalog_version"),
            "top_family": record.get("top_family"),
            "category_id": record.get("category_id"),
            "category_name_he": record.get("category_name_he"),
            "photo_storage_path": photo_storage_path,
            "has_photo": has_photo,
            "photo_ids": photo_ids,
            "photos": serialized_photos,
            "photo_url": (
                self._line_photo_url(
                    report_id=report_id,
                    line_id=line_id,
                    photo_id=photo_ids[0],
                )
                if has_photo
                else None
            ),
            "has_catalog_issue": bool(issue_id),
            "catalog_warning": catalog_warning,
            "group_key": record.get("group_key"),
            "group_label_he": record.get("group_label_he"),
            "block_id": record.get("block_id"),
            "linked_issue_id": record.get("linked_issue_id"),
            "visibility": record.get("visibility") or IssueVisibility.DRAFT.value,
            "created_at": record.get("created_at"),
            "updated_at": record.get("updated_at"),
        }

    def _send_to_core_pipeline(
        self,
        record: dict,
        *,
        source_filename: str,
        source_content: bytes,
    ) -> dict:
        return self.core_adapter.send_closed_report(
            project_id=str(record["project_id"]),
            source_filename=source_filename,
            source_content=source_content,
            fallback_filename=self._build_core_upload_filename(record),
        )

    @staticmethod
    def _build_core_upload_filename(record: dict) -> str:
        report_id = str(record["id"])
        visit_date = str(record.get("visit_date") or "unknown-date")
        return f"field-visit-{visit_date}-{report_id}.pdf"


def _line_is_empty(line: dict) -> bool:
    description = str(line.get("description") or "").strip()
    return not description


def _build_close_preview(lines: list[dict]) -> dict:
    empty_lines = [
        line for line in lines if _line_is_empty(line)
    ]
    catalog_warnings = [
        line
        for line in lines
        if line.get("catalog_warning")
    ]

    warnings: list[str] = []

    if not lines:
        warnings.append("אין שורות ממצאים בדוח.")

    if empty_lines:
        warnings.append(
            f"{len(empty_lines)} שורות ללא תיאור - מומלץ למלא לפני הפקת PDF."
        )

    if catalog_warnings:
        warnings.append(
            f"{len(catalog_warnings)} שורות עם אזהרת מפרט - "
            "מומלץ לבדוק לפני סגירה."
        )

    return {
        "line_count": len(lines),
        "empty_line_count": len(empty_lines),
        "empty_line_ids": [str(line["id"]) for line in empty_lines],
        "catalog_warning_count": len(catalog_warnings),
        "warnings": warnings,
    }


def _catalog_sync_state(
    *,
    report_catalog_version: str | None,
    current_catalog_version: str | None,
) -> dict:
    if not current_catalog_version:
        return {
            "is_current": True,
            "message": None,
        }

    if not report_catalog_version:
        return {
            "is_current": False,
            "message": (
                "דוח זה נפתח לפני שמירת גרסת קטלוג. "
                "מומלץ לסנכרן מפרט בהכנה לא מקוון."
            ),
        }

    if report_catalog_version != current_catalog_version:
        return {
            "is_current": False,
            "message": (
                f"גרסת הקטלוג במערכת ({current_catalog_version}) "
                f"חדשה מגרסת הדוח ({report_catalog_version})."
            ),
        }

    return {
        "is_current": True,
        "message": None,
    }


def _line_catalog_warning(
    *,
    issue_id: str | None,
    line_catalog_version: str | None,
    current_catalog_version: str | None,
    catalog_issue: dict | None,
) -> str | None:
    if not issue_id:
        return None

    if not catalog_issue:
        return (
            f"ממצא {issue_id} אינו קיים בקטלוג הנוכחי. "
            "השורה לא נמחקה - יש לעדכן ידנית."
        )

    if (
        current_catalog_version
        and line_catalog_version
        and line_catalog_version != current_catalog_version
    ):
        return (
            f"השורה נשמרה עם קטלוג {line_catalog_version}; "
            f"הגרסה הנוכחית היא {current_catalog_version}."
        )

    return None


def _merge_header_fields(
    project: dict,
    header_fields: dict | None,
    *,
    visit_type: str,
    visit_date: str | None = None,
) -> dict:
    from app.config.field_report_block_defaults import (
        default_fixed_text_blocks_for_new_report,
        default_report_blocks_for_visit_type,
    )
    from app.config.field_report_construction_progress import (
        default_construction_progress_rows,
    )
    from app.config.field_report_pdf_defaults import (
        DEFAULT_CONTRACTOR_NOTES_HE,
        DEFAULT_PROJECT_UPDATES_HE,
        DEFAULT_WINTER_RECOMMENDATIONS_HE,
    )

    fixed_text_blocks = default_fixed_text_blocks_for_new_report(visit_date)
    winter_block = next(
        (
            block
            for block in fixed_text_blocks
            if block.get("kind") == "winter_recommendations"
        ),
        None,
    )
    winter_text = (
        winter_block.get("body_he", DEFAULT_WINTER_RECOMMENDATIONS_HE)
        if winter_block and winter_block.get("enabled")
        else ""
    )

    default_blocks = default_report_blocks_for_visit_type(visit_type)
    if visit_type == "FINISHING_APARTMENTS":
        default_progress = []
    else:
        default_progress = default_construction_progress_rows(visit_type)

    defaults = {
        "developer_name": project.get("developer_name"),
        "developer_pm_name": project.get("developer_pm_name")
        or project.get("contractor_name"),
        "contractor_name": project.get("contractor_name"),
        "lawyer_name": project.get("lawyer_name"),
        "accompanying_lawyer": project.get("accompanying_lawyer"),
        "architect_name": project.get("architect_name"),
        "site_address": project.get("city"),
        "project_updates": list(DEFAULT_PROJECT_UPDATES_HE),
        "winter_recommendations": winter_text,
        "contractor_notes": list(DEFAULT_CONTRACTOR_NOTES_HE),
        "inspector_title": "",
        "inspector_license": "",
        "construction_progress": default_progress,
        "fixed_text_blocks": fixed_text_blocks,
        "include_fixed_text_blocks": True,
    }
    if default_blocks and not (header_fields or {}).get("blocks"):
        defaults["blocks"] = default_blocks

    merged = {**defaults, **(header_fields or {})}
    if not merged.get("fixed_text_blocks"):
        merged["fixed_text_blocks"] = fixed_text_blocks
    if merged.get("include_fixed_text_blocks") is None:
        merged["include_fixed_text_blocks"] = True
    if not merged.get("blocks") and default_blocks:
        merged["blocks"] = default_blocks
    if visit_type == "FINISHING_APARTMENTS" and not (
        header_fields or {}
    ).get("construction_progress"):
        merged["construction_progress"] = []
    elif not merged.get("construction_progress"):
        merged["construction_progress"] = default_construction_progress_rows(
            visit_type
        )

    from app.services.field_report_project_prefill import (
        merge_project_prefill_into_header_fields,
    )

    merged = merge_project_prefill_into_header_fields(project, merged)
    try:
        validate_header_fields_project_dates(merged)
    except ValueError as error:
        raise ValidationError(str(error)) from error
    return merged


def _apply_catalog_issue_defaults(
    payload: dict,
    catalog_issue: dict,
    *,
    catalog_version: str | None,
) -> dict:
    standard_ref = (
        catalog_issue.get("standard_ref")
        or catalog_issue.get("category_standard_id")
    )
    catalog_reference_id = (
        catalog_issue.get("catalog_reference_id")
        or payload.get("catalog_reference_id")
    )
    return {
        **payload,
        "trade": payload.get("trade") or catalog_issue.get(
            "issue_name_he"
        ),
        "description": payload.get("description")
        or catalog_issue.get("description"),
        "notes": payload.get("notes")
        or catalog_issue.get("rectification_action"),
        "severity": payload.get("severity")
        or catalog_issue.get("severity"),
        "standard_ref": standard_ref,
        "catalog_reference_id": catalog_reference_id,
        "engineering_impact": payload.get("engineering_impact")
        or catalog_issue.get("engineering_impact"),
        "top_family": catalog_issue.get("top_family"),
        "category_id": catalog_issue.get("category_id"),
        "category_name_he": catalog_issue.get("category_name_he"),
        "catalog_version": payload.get("catalog_version")
        or catalog_version,
        "location": payload.get("location")
        or catalog_issue.get("target_elements"),
    }


def _visit_type_label(visit_type: str) -> str:
    from app.config.field_report_visit_types import (
        VISIT_TYPE_CONFIG,
    )

    config = VISIT_TYPE_CONFIG.get(visit_type)
    if not config:
        return visit_type
    return str(config["label_he"])
