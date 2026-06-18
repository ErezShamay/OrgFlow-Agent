from __future__ import annotations

from postgrest.exceptions import APIError

from app.db.supabase_client import supabase
from app.exceptions.exceptions import ForbiddenError, NotFoundError
from app.repositories.field_visit_report_line_repository import (
    FieldVisitReportLineRepository,
)
from app.repositories.project_apartment_repository import (
    ProjectApartmentRepository,
)
from app.repositories.project_repository import ProjectRepository
from app.repositories.quality_issue_repository import QualityIssueRepository
from app.schemas.project_apartment import (
    ProjectApartmentRecord,
    ResidentPortalIssueSummary,
    ResidentPortalPayload,
    ResidentPortalPdfDownload,
    ResidentPortalProgressItem,
    ResidentPortalReportLine,
    ResidentPortalReportSummary,
)
from app.schemas.quality_issue import IssueVisibility, resolve_tenant_view_status_he
from app.services.resident_portal_status_cards import build_status_cards
from app.services.resident_invite_service import RESIDENT_ROLE
from app.services.resident_portal_gantt import build_gantt_rows
from app.services.resident_portal_matching import (
    apartment_number_from_group_key,
    record_matches_apartment,
)

RESIDENT_PORTAL_PERMISSION = "resident_portal:read"
RESIDENT_PORTAL_PDF_PATH = "/resident-portal/reports/{report_id}/pdf"


def _is_published_visibility(value: object) -> bool:
    if value is None:
        return False
    normalized = str(value).strip().upper()
    return normalized == IssueVisibility.PUBLISHED.value


def _is_shared_property_group_key(group_key: object) -> bool:
    return not str(group_key or "").strip()


class ResidentPortalService:
    def __init__(
        self,
        apartment_repository: ProjectApartmentRepository | None = None,
        project_repository: ProjectRepository | None = None,
        line_repository: FieldVisitReportLineRepository | None = None,
        issue_repository: QualityIssueRepository | None = None,
    ) -> None:
        self.apartment_repository = (
            apartment_repository or ProjectApartmentRepository()
        )
        self.project_repository = project_repository or ProjectRepository()
        self.line_repository = line_repository or FieldVisitReportLineRepository()
        self.issue_repository = issue_repository or QualityIssueRepository()

    def get_portal_for_apartment(
        self,
        *,
        organization_id: str,
        apartment_id: str,
        actor_user_id: str,
        actor_role: str,
    ) -> dict:
        apartment = self.apartment_repository.get_by_id(apartment_id)
        if apartment is None:
            raise NotFoundError(message="Apartment not found")
        if str(apartment.get("organization_id")) != organization_id:
            raise NotFoundError(message="Apartment not found")

        self._assert_can_view_apartment(
            apartment=apartment,
            actor_user_id=actor_user_id,
            actor_role=actor_role,
        )

        project_id = str(apartment.get("project_id") or "")
        project = self.project_repository.get_project_by_id(project_id)
        project_name = project.get("project_name") if project else None

        group_key = str(apartment.get("group_key") or "")
        apartment_number = apartment_number_from_group_key(group_key)

        reports, report_lines, progress_timeline = self._collect_field_reports(
            organization_id=organization_id,
            project_id=project_id,
            group_key=group_key,
            actor_role=actor_role,
        )
        legacy_reports, legacy_lines = self._collect_legacy_weekly_reports(
            project_id=project_id,
            apartment_number=apartment_number,
        )
        reports.extend(legacy_reports)
        report_lines.extend(legacy_lines)

        reports.sort(
            key=lambda item: str(item.visit_date or ""),
            reverse=True,
        )

        issues, issue_records = self._collect_issues(
            organization_id=organization_id,
            project_id=project_id,
            group_key=group_key,
        )

        gantt_rows = build_gantt_rows(
            progress_timeline=progress_timeline,
            report_lines=report_lines,
        )

        status_cards = build_status_cards(issue_records)
        pdf_downloads = self._collect_pdf_downloads(reports)

        payload = ResidentPortalPayload(
            apartment=ProjectApartmentRecord.model_validate(apartment),
            project_name=project_name,
            default_view="trust_dashboard",
            status_cards=status_cards,
            pdf_downloads=pdf_downloads,
            reports=reports,
            report_lines=report_lines,
            issues=issues,
            progress_timeline=progress_timeline,
            gantt_rows=gantt_rows,
            read_only=True,
        )
        return payload.model_dump()

    def get_portal_for_resident(
        self,
        *,
        organization_id: str,
        actor_user_id: str,
        actor_role: str,
    ) -> dict:
        if actor_role.strip().upper() != RESIDENT_ROLE:
            raise ForbiddenError(message="Not a resident account")

        apartment = self.apartment_repository.get_by_resident_profile_id(
            actor_user_id
        )
        if apartment is None:
            raise NotFoundError(
                message="לא נמצאה דירה משויכת לחשבון זה",
            )

        return self.get_portal_for_apartment(
            organization_id=organization_id,
            apartment_id=str(apartment["id"]),
            actor_user_id=actor_user_id,
            actor_role=actor_role,
        )

    def assert_resident_can_access_report(
        self,
        *,
        organization_id: str,
        actor_user_id: str,
        actor_role: str,
        report_id: str,
    ) -> None:
        apartment = self.apartment_repository.get_by_resident_profile_id(
            actor_user_id
        )
        if apartment is None:
            raise NotFoundError(
                message="לא נמצאה דירה משויכת לחשבון זה",
            )
        if str(apartment.get("organization_id")) != organization_id:
            raise NotFoundError(message="Apartment not found")

        project_id = str(apartment.get("project_id") or "")
        group_key = str(apartment.get("group_key") or "")

        from app.repositories.field_visit_report_repository import (
            FieldVisitReportRepository,
        )

        report_repository = FieldVisitReportRepository()
        if not report_repository.is_storage_available():
            raise NotFoundError(message="Report not found")

        reports = report_repository.list_by_organization(
            organization_id,
            project_id=project_id,
        )
        report = next(
            (item for item in reports if str(item.get("id") or "") == report_id),
            None,
        )
        if report is None:
            raise NotFoundError(message="Report not found")

        if not str(report.get("pdf_storage_path") or "").strip():
            raise NotFoundError(message="Archived PDF not found")

        report_lines = self.line_repository.list_by_report(report_id)
        matching_lines = [
            line
            for line in report_lines
            if _is_published_visibility(line.get("visibility"))
            and (
                _is_shared_property_group_key(line.get("group_key"))
                or str(line.get("group_key") or "") == group_key
                or self._line_matches_apartment(line, group_key)
            )
        ]
        if not matching_lines:
            raise ForbiddenError(message="אין גישה לדוח זה")

    def _assert_can_view_apartment(
        self,
        *,
        apartment: dict,
        actor_user_id: str,
        actor_role: str,
    ) -> None:
        normalized_role = actor_role.strip().upper()
        if normalized_role == RESIDENT_ROLE:
            resident_profile_id = str(
                apartment.get("resident_profile_id") or ""
            )
            if resident_profile_id != actor_user_id:
                raise ForbiddenError(
                    message="אין גישה לתיק דירה זו",
                )

    def _collect_field_reports(
        self,
        *,
        organization_id: str,
        project_id: str,
        group_key: str,
        actor_role: str,
    ) -> tuple[
        list[ResidentPortalReportSummary],
        list[ResidentPortalReportLine],
        list[ResidentPortalProgressItem],
    ]:
        from app.repositories.field_visit_report_repository import (
            FieldVisitReportRepository,
        )

        report_repository = FieldVisitReportRepository()
        if not report_repository.is_storage_available():
            return [], [], []

        reports_raw = report_repository.list_by_organization(
            organization_id,
            project_id=project_id,
        )

        summaries: list[ResidentPortalReportSummary] = []
        lines_out: list[ResidentPortalReportLine] = []
        progress: list[ResidentPortalProgressItem] = []

        for report in reports_raw:
            report_id = str(report.get("id") or "")
            report_lines = self.line_repository.list_by_report(report_id)
            matching_lines = [
                line
                for line in report_lines
                if _is_published_visibility(line.get("visibility"))
                and (
                    _is_shared_property_group_key(line.get("group_key"))
                    or str(line.get("group_key") or "") == group_key
                    or self._line_matches_apartment(line, group_key)
                )
            ]

            if not matching_lines:
                document = report.get("document") or {}
                progress_rows = self._extract_progress_rows(document)
                if progress_rows:
                    visit_date = report.get("visit_date") or report.get(
                        "created_at"
                    )
                    for row in progress_rows:
                        progress.append(
                            ResidentPortalProgressItem(
                                description=str(
                                    row.get("description") or ""
                                ),
                                status=str(row.get("status") or ""),
                                completion_date=str(
                                    row.get("completion_date") or ""
                                ),
                                report_id=report_id,
                                visit_date=str(visit_date or ""),
                                report_title=report.get("title"),
                            )
                        )
                continue

            summaries.append(
                ResidentPortalReportSummary(
                    id=report_id,
                    title=report.get("title"),
                    visit_type=report.get("visit_type"),
                    visit_date=report.get("visit_date"),
                    status=report.get("status"),
                    pdf_url=self._portal_pdf_url(
                        report_id,
                        report,
                        actor_role=actor_role,
                    ),
                    line_count=len(matching_lines),
                )
            )

            visit_date = report.get("visit_date") or report.get("created_at")
            for line in matching_lines:
                lines_out.append(
                    ResidentPortalReportLine(
                        id=str(line.get("id") or ""),
                        report_id=report_id,
                        description=line.get("description"),
                        status=line.get("status"),
                        location=line.get("location"),
                        visit_date=str(visit_date or ""),
                        report_title=report.get("title"),
                    )
                )

        return summaries, lines_out, progress

    @staticmethod
    def _line_matches_apartment(line: dict, group_key: str) -> bool:
        apartment_number = apartment_number_from_group_key(group_key)
        if not apartment_number:
            return False
        if str(line.get("group_key") or "") == group_key:
            return True
        return record_matches_apartment(line, apartment_number)

    def _collect_legacy_weekly_reports(
        self,
        *,
        project_id: str,
        apartment_number: str,
    ) -> tuple[list[ResidentPortalReportSummary], list[ResidentPortalReportLine]]:
        if not apartment_number:
            return [], []

        summaries: list[ResidentPortalReportSummary] = []
        lines_out: list[ResidentPortalReportLine] = []
        seen_report_ids: set[str] = set()

        findings_by_report = self._load_findings_by_report(project_id)

        for source, table, source_kind in (
            ("weekly", "weekly_reports", "weekly"),
            ("legacy", "reports", "legacy"),
        ):
            _ = source
            try:
                query = (
                    supabase
                    .table(table)
                    .select("*")
                    .eq("project_id", project_id)
                )
                if table == "weekly_reports":
                    query = query.order("created_at", desc=True)
                else:
                    query = query.order("received_date", desc=True)
                response = query.execute()
            except APIError:
                continue

            for report in response.data or []:
                report_id = str(report.get("id") or "")
                if not report_id:
                    continue

                report_findings = findings_by_report.get(report_id, [])
                matching_findings = [
                    finding
                    for finding in report_findings
                    if record_matches_apartment(finding, apartment_number)
                ]

                report_matches = record_matches_apartment(
                    report,
                    apartment_number,
                )
                if not matching_findings and not report_matches:
                    continue

                if report_id not in seen_report_ids:
                    seen_report_ids.add(report_id)
                    title = (
                        report.get("email_subject")
                        or report.get("file_name")
                        or report.get("report_source")
                        or "דוח שבועי"
                    )
                    visit_date = (
                        report.get("reported_at")
                        or report.get("received_date")
                        or report.get("created_at")
                    )
                    summaries.append(
                        ResidentPortalReportSummary(
                            id=report_id,
                            title=str(title),
                            visit_type=source_kind,
                            visit_date=str(visit_date) if visit_date else None,
                            status=report.get("status"),
                            line_count=len(matching_findings),
                            source=source_kind,
                        )
                    )

                report_title = (
                    report.get("email_subject")
                    or report.get("file_name")
                    or "דוח שבועי"
                )
                report_date = (
                    report.get("reported_at")
                    or report.get("received_date")
                    or report.get("created_at")
                )
                for finding in matching_findings:
                    lines_out.append(
                        ResidentPortalReportLine(
                            id=str(finding.get("id") or ""),
                            report_id=report_id,
                            description=finding.get("title")
                            or finding.get("summary"),
                            status=finding.get("status"),
                            location=None,
                            visit_date=str(report_date) if report_date else None,
                            report_title=str(report_title),
                            source=source_kind,
                        )
                    )

        return summaries, lines_out

    @staticmethod
    def _load_findings_by_report(project_id: str) -> dict[str, list[dict]]:
        try:
            response = (
                supabase
                .table("findings")
                .select("*")
                .eq("project_id", project_id)
                .execute()
            )
        except APIError:
            return {}

        grouped: dict[str, list[dict]] = {}
        for finding in response.data or []:
            report_id = str(finding.get("report_id") or "")
            if not report_id:
                continue
            grouped.setdefault(report_id, []).append(finding)

        return grouped

    @staticmethod
    def _extract_progress_rows(document: object) -> list[dict]:
        if not isinstance(document, dict):
            return []

        blocks = document.get("blocks")
        if not isinstance(blocks, list):
            return []

        rows: list[dict] = []
        for block in blocks:
            if not isinstance(block, dict):
                continue
            if block.get("type") != "construction_progress":
                continue
            content = block.get("content")
            if not isinstance(content, dict):
                continue
            block_rows = content.get("rows")
            if isinstance(block_rows, list):
                rows.extend(
                    row for row in block_rows if isinstance(row, dict)
                )
        return rows

    def _collect_issues(
        self,
        *,
        organization_id: str,
        project_id: str,
        group_key: str,
    ) -> tuple[list[ResidentPortalIssueSummary], list[dict]]:
        if not self.issue_repository.is_storage_available():
            return [], []

        issues = self.issue_repository.list_by_project(project_id)
        filtered: list[ResidentPortalIssueSummary] = []
        records: list[dict] = []

        for issue in issues:
            if str(issue.get("organization_id") or "") != organization_id:
                continue
            if not _is_published_visibility(issue.get("visibility")):
                continue
            issue_group_key = str(issue.get("group_key") or "")
            apartment_number = apartment_number_from_group_key(group_key)
            if issue_group_key:
                if issue_group_key != group_key and not record_matches_apartment(
                    issue,
                    apartment_number,
                ):
                    continue

            records.append(issue)
            issue_status = issue.get("status")
            tenant_status_he = issue.get("tenant_view_status_he") or (
                resolve_tenant_view_status_he(issue_status)
            )
            filtered.append(
                ResidentPortalIssueSummary(
                    id=str(issue.get("id") or ""),
                    title=issue.get("title"),
                    status=issue_status,
                    tenant_view_status_he=tenant_status_he,
                    trade=issue.get("trade"),
                    location=issue.get("location"),
                    severity=issue.get("severity"),
                    catalog_issue_id=issue.get("catalog_issue_id"),
                    standard_ref=issue.get("standard_ref"),
                    first_seen_at=issue.get("first_seen_at"),
                    last_seen_at=issue.get("last_seen_at"),
                )
            )

        return filtered, records

    @staticmethod
    def _portal_pdf_url(
        report_id: str,
        report: dict,
        *,
        actor_role: str,
    ) -> str | None:
        if not str(report.get("pdf_storage_path") or "").strip():
            return None
        if actor_role.strip().upper() == RESIDENT_ROLE:
            return RESIDENT_PORTAL_PDF_PATH.format(report_id=report_id)
        return f"/field-reports/visits/{report_id}/pdf"

    @staticmethod
    def _collect_pdf_downloads(
        reports: list[ResidentPortalReportSummary],
    ) -> list[ResidentPortalPdfDownload]:
        downloads: list[ResidentPortalPdfDownload] = []
        for report in reports:
            if not report.pdf_url:
                continue
            downloads.append(
                ResidentPortalPdfDownload(
                    report_id=report.id,
                    title=report.title,
                    visit_date=report.visit_date,
                    pdf_url=report.pdf_url,
                    source=report.source,
                )
            )
        return downloads
