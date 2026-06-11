from pathlib import Path
import json
import re
from uuid import uuid4
from datetime import UTC, datetime

from app.db.supabase_client import supabase
from app.repositories.workspace_activity_repository import WorkspaceActivityRepository
from app.repositories.weekly_report_repository import WeeklyReportRepository
from app.services.quality_issue_upload_finding_service import (
    QualityIssueUploadFindingService,
)
from app.services.report_text_extraction_service import ReportTextExtractionService


class ReportProcessingService:
    ALLOWED_REPORT_EXTENSIONS = {
        "pdf", "doc", "docx", "xls", "xlsx", "csv", "txt", "png", "jpg", "jpeg",
    }
    MAX_REPORT_FILE_SIZE_BYTES = 10 * 1024 * 1024

    def __init__(self):
        self.report_repository = WeeklyReportRepository()
        self.upload_finding_materialization = QualityIssueUploadFindingService()
        self.report_attachments: dict[str, list[dict]] = {}
        self.report_tags: dict[str, list[str]] = {}
        self.report_index: dict[str, dict] = {}
        self.bulk_upload_jobs: dict[str, dict] = {}

    def process_uploaded_report(
        self,
        project_id: str,
        filename: str,
        file_path: str,
    ):
        upload_policy = self._validate_upload_policy(filename=filename, file_path=file_path)
        if not upload_policy["is_valid"]:
            return {
                "success": False,
                "project_id": project_id,
                "filename": filename,
                "error_code": upload_policy["error_code"],
                "error_message": upload_policy["error_message"],
            }

        malware_scan = self._scan_for_malware(file_path=file_path, filename=filename)
        if not malware_scan["is_clean"]:
            self._safe_create_activity(
                project_id=project_id,
                activity_type="MALWARE_REPORT",
                title="Malware report rejected",
                description=f"Rejected suspicious file: {filename}",
                metadata={
                    "filename": filename,
                    "error_code": malware_scan["error_code"],
                    "error_message": malware_scan["error_message"],
                    "signals": malware_scan["signals"],
                },
            )
            return {
                "success": False,
                "project_id": project_id,
                "filename": filename,
                "error_code": malware_scan["error_code"],
                "error_message": malware_scan["error_message"],
            }

        integrity = self._validate_file_integrity(file_path=file_path, filename=filename)
        if not integrity["is_valid"]:
            WorkspaceActivityRepository.create_activity(
                project_id=project_id,
                activity_type="CORRUPTED_REPORT",
                title="Corrupted report rejected",
                description=f"Rejected file: {filename}",
                metadata={
                    "filename": filename,
                    "error_code": integrity["error_code"],
                    "error_message": integrity["error_message"],
                },
            )
            return {
                "success": False,
                "project_id": project_id,
                "filename": filename,
                "error_code": integrity["error_code"],
                "error_message": integrity["error_message"],
            }

        extracted_text = self._extract_text_for_ocr(file_path)
        text_preview = extracted_text[:500] if extracted_text else "No textual content detected"
        metadata = self._extract_report_metadata(
            filename=filename,
            file_path=file_path,
            extracted_text=extracted_text,
        )
        classification = self._classify_report(filename=filename, extracted_text=extracted_text)
        existing_reports = (
            self.report_repository
            .get_reports_by_project(project_id)
        )
        duplicate_detection = self._detect_duplicate_report(
            project_id=project_id,
            filename=filename,
            text_preview=text_preview,
            existing_reports=existing_reports,
        )
        ai_insights = self._build_ai_insights(
            extracted_text=extracted_text,
            classification=classification,
        )

        if duplicate_detection["is_duplicate"]:
            WorkspaceActivityRepository.create_activity(
                project_id=project_id,
                activity_type="DUPLICATE_REPORT",
                title="Duplicate report detected",
                description=f"Skipped duplicate upload: {filename}",
                metadata={
                    "filename": filename,
                    "duplicate_reason": duplicate_detection["reason"],
                    "duplicate_signals": duplicate_detection["signals"],
                },
            )
            return {
                "success": True,
                "duplicate_detected": True,
                "duplicate_reason": duplicate_detection["reason"],
                "duplicate_signals": duplicate_detection["signals"],
                "project_id": project_id,
                "filename": filename,
                "classification": classification,
                "ai_insights": ai_insights,
                "metadata": metadata,
            }

        versioned_subject, report_version = self._build_versioned_subject(
            project_id,
            filename,
            existing_reports=existing_reports,
        )

        created_report = self.report_repository.create_report(
            project_id=project_id,
            report_source=classification["category"],
            email_subject=versioned_subject,
        )

        upload_persist = self._persist_upload_interpretation(
            project_id=project_id,
            report_id=str(created_report.get("id")),
            filename=filename,
            text_preview=text_preview,
            extracted_text=extracted_text,
            classification=classification,
            metadata=metadata,
            ai_insights=ai_insights,
        )
        interpretation = (
            upload_persist.get("interpretation") if upload_persist else None
        )
        quality_issue_id = (
            upload_persist.get("quality_issue_id") if upload_persist else None
        )
        index_entry = self.index_report(
            project_id=project_id,
            report_id=created_report.get("id"),
            filename=filename,
            classification=classification,
            metadata=metadata,
            ai_insights=ai_insights,
        )

        WorkspaceActivityRepository.create_activity(
            project_id=project_id,
            activity_type="REPORT_UPLOAD",
            title="Weekly report uploaded",
            description=f"Uploaded file: {filename}",
            metadata={
                "filename": filename,
                "versioned_subject": versioned_subject,
                "report_version": report_version,
                "ocr_text_length": len(extracted_text),
                "report_id": created_report.get("id"),
                "classification": classification["category"],
                "classification_confidence": classification["confidence"],
                "metadata": metadata,
            },
        )
        WorkspaceActivityRepository.create_activity(
            project_id=project_id,
            activity_type="AI_ANALYSIS",
            title="AI interpretation created",
            description="Initial AI interpretation generated from OCR/text extraction pipeline",
            metadata={
                "report_id": created_report.get("id"),
                "ai_interpretation_id": interpretation.get("id") if interpretation else None,
            },
        )

        return {
            "success": True,
            "duplicate_detected": False,
            "project_id": project_id,
            "filename": filename,
            "versioned_subject": versioned_subject,
            "report_version": report_version,
            "report_id": created_report.get("id"),
            "ai_interpretation_id": interpretation.get("id") if interpretation else None,
            "quality_issue_id": quality_issue_id,
            "ocr_text_length": len(extracted_text),
            "ocr_preview": text_preview,
            "classification": classification,
            "ai_insights": ai_insights,
            "metadata": metadata,
            "index": {
                "report_id": index_entry.get("report_id"),
                "indexed_at": index_entry.get("indexed_at"),
                "tokens_count": len(index_entry.get("tokens", [])),
            },
        }

    def start_bulk_upload_job(self, project_id: str, total_files: int) -> str:
        job_id = f"bulk-{uuid4()}"
        self.bulk_upload_jobs[job_id] = {
            "job_id": job_id,
            "project_id": project_id,
            "total_files": total_files,
            "processed_files": 0,
            "successful_uploads": 0,
            "failed_uploads": 0,
            "progress_percent": 0,
            "status": "IN_PROGRESS",
            "results": [],
            "started_at": datetime.now(UTC).isoformat(),
            "finished_at": None,
        }
        return job_id

    def run_bulk_upload_job(
        self,
        job_id: str,
        project_id: str,
        uploads: list[dict],
    ) -> None:
        total_files = len(uploads)
        results: list[dict] = []
        for index, upload in enumerate(uploads, start=1):
            filename = str(upload.get("filename") or "").strip()
            file_path = str(upload.get("file_path") or "").strip()
            if not filename or not file_path:
                result = {
                    "success": False,
                    "project_id": project_id,
                    "filename": filename or "unknown",
                    "error_code": "INVALID_UPLOAD_ENTRY",
                    "error_message": "Bulk upload entry must include filename and file_path",
                }
                results.append(result)
                self._update_bulk_progress(job_id=job_id, total_files=total_files, processed_files=index, latest_result=result)
                continue

            try:
                result = self.process_uploaded_report(
                    project_id=project_id,
                    filename=filename,
                    file_path=file_path,
                )
            except Exception:
                result = {
                    "success": False,
                    "project_id": project_id,
                    "filename": filename,
                    "error_code": "REPORT_PROCESSING_FAILED",
                    "error_message": "Unexpected error while processing uploaded report",
                }
            results.append(result)
            self._update_bulk_progress(job_id=job_id, total_files=total_files, processed_files=index, latest_result=result)

        successful = [item for item in results if item.get("success")]
        failed = [item for item in results if not item.get("success")]
        job = self.bulk_upload_jobs[job_id]
        job["status"] = "COMPLETED"
        job["finished_at"] = datetime.now(UTC).isoformat()
        job["successful_uploads"] = len(successful)
        job["failed_uploads"] = len(failed)
        job["results"] = results

    def process_bulk_uploaded_reports(self, project_id: str, uploads: list[dict]) -> dict:
        job_id = self.start_bulk_upload_job(project_id, len(uploads))
        self.run_bulk_upload_job(job_id, project_id, uploads)
        job = self.bulk_upload_jobs[job_id]
        return {
            "job_id": job_id,
            "project_id": project_id,
            "total_files": len(uploads),
            "successful_uploads": job.get("successful_uploads", 0),
            "failed_uploads": job.get("failed_uploads", 0),
            "progress_percent": job.get("progress_percent", 0),
            "status": job.get("status"),
            "results": job.get("results", []),
        }

    def get_bulk_upload_progress(self, project_id: str, job_id: str) -> dict | None:
        job = self.bulk_upload_jobs.get(job_id)
        if not job:
            return None
        if job.get("project_id") != project_id:
            return None
        return job

    def _update_bulk_progress(
        self,
        *,
        job_id: str,
        total_files: int,
        processed_files: int,
        latest_result: dict,
    ) -> None:
        job = self.bulk_upload_jobs.get(job_id)
        if not job:
            return
        progress_percent = int((processed_files / total_files) * 100) if total_files > 0 else 0
        job["processed_files"] = processed_files
        job["progress_percent"] = progress_percent
        if latest_result.get("success"):
            job["successful_uploads"] = int(job.get("successful_uploads", 0)) + 1
        else:
            job["failed_uploads"] = int(job.get("failed_uploads", 0)) + 1
        job_results = job.get("results", [])
        job_results.append(latest_result)
        job["results"] = job_results

    def _extract_text_for_ocr(self, file_path: str) -> str:
        extracted_text = ReportTextExtractionService.extract_text(file_path)
        if extracted_text.strip():
            return extracted_text

        # OCR fallback placeholder for non-PDF or scanned documents.
        extension = Path(file_path).suffix.lower().lstrip(".") or "unknown"
        return f"[OCR_FALLBACK:{extension}] Unable to extract machine text from source document"

    def _classify_report(self, filename: str, extracted_text: str) -> dict:
        full_text = f"{filename.lower()} {extracted_text.lower()}"
        rules = [
            (
                "SAFETY",
                ["safety", "hazard", "incident", "injury", "risk", "בטיחות", "סיכון"],
                "Escalate safety findings and assign immediate mitigation actions",
            ),
            (
                "DELAY",
                ["delay", "late", "blocked", "slippage", "עיכוב", "איחור"],
                "Review schedule impact and define timeline recovery plan",
            ),
            (
                "BUDGET",
                ["budget", "cost", "overrun", "invoice", "תקציב", "עלות"],
                "Validate budget variance and trigger financial follow-up",
            ),
            (
                "QUALITY",
                ["quality", "defect", "rework", "inspection", "איכות", "ליקוי"],
                "Track quality defects and prioritize remediation workflow",
            ),
        ]

        for category, keywords, recommended_action in rules:
            matches = [keyword for keyword in keywords if keyword in full_text]
            if matches:
                confidence = min(0.95, 0.55 + (0.1 * len(matches)))
                return {
                    "category": category,
                    "confidence": round(confidence, 2),
                    "signals": matches[:5],
                    "recommended_action": recommended_action,
                }

        return {
            "category": "GENERAL",
            "confidence": 0.45,
            "signals": [],
            "recommended_action": "Route to operations manager for manual classification",
        }

    def _build_versioned_subject(
        self,
        project_id: str,
        filename: str,
        existing_reports: list | None = None,
    ) -> tuple[str, int]:
        base_name = filename.strip()
        if existing_reports is None:
            existing_reports = (
                self.report_repository
                .get_reports_by_project(project_id)
            )
        max_version = 0

        for report in existing_reports:
            subject = str(report.get("email_subject") or "").strip()
            parsed_base, parsed_version = self._parse_versioned_subject(subject)
            if parsed_base.casefold() != base_name.casefold():
                continue
            max_version = max(max_version, parsed_version)

        next_version = max_version + 1
        return f"{base_name} (v{next_version})", next_version

    def _parse_versioned_subject(self, subject: str) -> tuple[str, int]:
        pattern = r"^(?P<base>.*?)(?:\s+\(v(?P<version>\d+)\))?$"
        match = re.match(pattern, subject.strip())
        if not match:
            return subject.strip(), 1

        base = (match.group("base") or "").strip()
        version_group = match.group("version")
        if not version_group:
            return base, 1

        try:
            return base, max(1, int(version_group))
        except ValueError:
            return base, 1

    def _detect_duplicate_report(
        self,
        project_id: str,
        filename: str,
        text_preview: str,
        existing_reports: list | None = None,
    ) -> dict:
        signals: list[str] = []
        if existing_reports is None:
            existing_reports = (
                self.report_repository
                .get_reports_by_project(project_id)
            )
        normalized_filename = filename.strip().casefold()

        for report in existing_reports:
            subject = str(report.get("email_subject") or "").strip()
            parsed_base, _ = self._parse_versioned_subject(subject)
            if parsed_base.casefold() == normalized_filename:
                signals.append("same_filename_lineage")
                break

        if text_preview and text_preview != "No textual content detected":
            existing_previews = self._get_existing_interpretation_previews(project_id)
            for preview in existing_previews:
                if preview.strip() == text_preview.strip():
                    signals.append("matching_text_preview")
                    break

        if signals:
            return {
                "is_duplicate": True,
                "reason": "existing_report_match",
                "signals": signals,
            }

        return {
            "is_duplicate": False,
            "reason": None,
            "signals": [],
        }

    def _get_existing_interpretation_previews(self, project_id: str) -> list[str]:
        try:
            response = (
                supabase.table("ai_interpretations")
                .select("business_impact")
                .eq("project_id", project_id)
                .limit(100)
                .execute()
            )
        except Exception:
            return []

        previews: list[str] = []
        for row in response.data or []:
            preview = row.get("business_impact")
            if isinstance(preview, str) and preview.strip():
                previews.append(preview)
        return previews

    def _get_interpretations_by_report_ids(
        self,
        report_ids: list[str],
    ) -> dict[str, dict]:
        if not report_ids:
            return {}

        try:
            findings_response = (
                supabase.table("findings")
                .select("id, report_id, metadata, created_at")
                .in_("report_id", report_ids)
                .order("created_at", desc=True)
                .execute()
            )
        except Exception:
            return {}

        findings_by_report: dict[str, dict] = {}
        finding_ids: list[str] = []
        for row in findings_response.data or []:
            report_id = row.get("report_id")
            finding_id = row.get("id")
            if not report_id or not finding_id:
                continue

            report_id_str = str(report_id)
            if report_id_str in findings_by_report:
                continue

            findings_by_report[report_id_str] = row
            finding_ids.append(str(finding_id))

        if not finding_ids:
            return {}

        try:
            response = (
                supabase.table("ai_interpretations")
                .select(
                    "finding_id, business_impact, recommended_action, "
                    "tenant_risk, review_status"
                )
                .in_("finding_id", finding_ids)
                .execute()
            )
        except Exception:
            return {}

        interpretations_by_finding = {
            str(row["finding_id"]): row
            for row in response.data or []
            if row.get("finding_id")
        }

        interpretations: dict[str, dict] = {}
        for report_id, finding in findings_by_report.items():
            interpretation = interpretations_by_finding.get(str(finding["id"]))
            if not interpretation:
                continue

            interpretations[report_id] = {
                **interpretation,
                "metadata": finding.get("metadata") or {},
            }

        return interpretations

    def _persist_upload_interpretation(
        self,
        *,
        project_id: str,
        report_id: str,
        filename: str,
        text_preview: str,
        extracted_text: str,
        classification: dict,
        metadata: dict,
        ai_insights: dict,
    ) -> dict | None:
        severity_by_category = {
            "SAFETY": "high",
            "DELAY": "medium",
            "BUDGET": "medium",
            "QUALITY": "medium",
            "GENERAL": "medium",
        }
        category = classification.get("category", "GENERAL")

        finding_response = (
            supabase.table("findings")
            .insert(
                {
                    "report_id": report_id,
                    "project_id": project_id,
                    "finding_type": category,
                    "severity": severity_by_category.get(category, "medium"),
                    "title": filename,
                    "summary": text_preview,
                    "source_text": extracted_text[:5000],
                    "metadata": metadata,
                }
            )
            .execute()
        )
        created_finding = finding_response.data[0] if finding_response.data else None
        if not created_finding:
            return None

        materialization = (
            self.upload_finding_materialization.materialize_from_upload_finding(
                project_id=project_id,
                report_id=report_id,
                finding=created_finding,
            )
        )
        if materialization and materialization.issue_id:
            self._link_finding_to_quality_issue(
                finding_id=str(created_finding.get("id")),
                issue_id=materialization.issue_id,
                metadata=created_finding.get("metadata") or metadata,
            )

        interpretation_response = (
            supabase.table("ai_interpretations")
            .insert(
                {
                    "finding_id": created_finding.get("id"),
                    "project_id": project_id,
                    "model_name": "upload-pipeline",
                    "business_impact": text_preview,
                    "tenant_risk": "MEDIUM",
                    "recommended_action": classification["recommended_action"],
                    "raw_response": json.dumps(
                        {
                            "metadata": metadata,
                            "ai_insights": ai_insights,
                            "classification": classification,
                        },
                        ensure_ascii=False,
                    ),
                    "review_status": "PENDING",
                }
            )
            .execute()
        )

        interpretation = (
            interpretation_response.data[0]
            if interpretation_response.data
            else None
        )

        return {
            "interpretation": interpretation,
            "quality_issue_id": (
                materialization.issue_id if materialization else None
            ),
        }

    def _link_finding_to_quality_issue(
        self,
        *,
        finding_id: str,
        issue_id: str,
        metadata: dict,
    ) -> None:
        merged_metadata = {
            **(metadata or {}),
            "quality_issue_id": issue_id,
            "qc_materialized": True,
        }
        try:
            supabase.table("findings").update(
                {"metadata": merged_metadata}
            ).eq("id", finding_id).execute()
        except Exception:
            return

    def list_project_uploaded_reports(self, project_id: str) -> dict:
        reports = self.report_repository.get_reports_by_project(project_id)
        report_ids = [
            str(report.get("id"))
            for report in reports
            if report.get("id")
        ]
        interpretations = self._get_interpretations_by_report_ids(report_ids)
        entries: list[dict] = []

        for report in reports:
            report_id = report.get("id")
            if not report_id:
                continue

            report_id_str = str(report_id)
            interpretation = interpretations.get(report_id_str, {})
            metadata = interpretation.get("metadata") or {}
            text_preview = (interpretation.get("business_impact") or "").strip()

            entries.append(
                {
                    "id": report_id_str,
                    "title": report.get("email_subject") or "דוח ללא שם",
                    "report_source": report.get("report_source") or "UNKNOWN",
                    "created_at": report.get("created_at"),
                    "text_preview": text_preview or None,
                    "recommended_action": interpretation.get("recommended_action"),
                    "tenant_risk": interpretation.get("tenant_risk"),
                    "review_status": interpretation.get("review_status"),
                    "original_filename": metadata.get("file_name"),
                    "has_original_file": False,
                }
            )

        entries.sort(
            key=lambda item: item.get("created_at") or "",
            reverse=True,
        )

        return {
            "project_id": project_id,
            "reports": entries,
            "total_reports": len(entries),
        }

    def get_project_report_timeline(self, project_id: str) -> dict:
        reports = self.report_repository.get_reports_by_project(project_id)
        activities = WorkspaceActivityRepository.get_project_activity(project_id)
        report_activity_types = {
            "REPORT_UPLOAD",
            "AI_ANALYSIS",
            "DUPLICATE_REPORT",
            "CORRUPTED_REPORT",
        }

        events: list[dict] = []
        for report in reports:
            report_id = report.get("id")
            subject = report.get("email_subject", "Unnamed report")
            source = report.get("report_source", "UNKNOWN")
            created_at = report.get("created_at") or datetime.now(UTC).isoformat()
            events.append(
                {
                    "id": f"report-{report_id or subject}",
                    "event_type": "REPORT_CREATED",
                    "title": "Report ingested",
                    "description": f"{subject} ({source})",
                    "created_at": created_at,
                    "metadata": {
                        "report_id": report_id,
                        "report_source": source,
                        "subject": subject,
                    },
                }
            )

        for activity in activities:
            activity_type = activity.get("activity_type")
            if activity_type not in report_activity_types:
                continue
            events.append(
                {
                    "id": f"activity-{activity.get('id', activity.get('created_at', 'unknown'))}",
                    "event_type": activity_type,
                    "title": activity.get("title", "Report activity"),
                    "description": activity.get("description"),
                    "created_at": activity.get("created_at") or datetime.now(UTC).isoformat(),
                    "metadata": activity.get("metadata") or {},
                }
            )

        events.sort(key=lambda item: item["created_at"], reverse=True)
        return {
            "project_id": project_id,
            "events": events,
            "total_events": len(events),
        }

    def get_project_report_ai_insights(self, project_id: str, limit: int = 20) -> dict:
        try:
            reports = (
                supabase.table("weekly_reports")
                .select("id, email_subject, report_source, created_at")
                .eq("project_id", project_id)
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            ).data or []
        except Exception:
            reports = []

        try:
            interpretations = (
                supabase.table("ai_interpretations")
                .select("id, business_impact, tenant_risk, recommended_action, review_status, created_at")
                .eq("project_id", project_id)
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            ).data or []
        except Exception:
            interpretations = []

        insights: list[dict] = []
        for row in interpretations:
            preview = (row.get("business_impact") or "").strip()
            synthetic_classification = self._classify_report("historical-report", preview)
            insights.append(
                {
                    "id": row.get("id"),
                    "created_at": row.get("created_at") or datetime.now(UTC).isoformat(),
                    "risk_level": row.get("tenant_risk", "MEDIUM"),
                    "review_status": row.get("review_status", "PENDING"),
                    "recommended_action": row.get("recommended_action"),
                    "classification": synthetic_classification["category"],
                    "confidence": synthetic_classification["confidence"],
                    "signals": synthetic_classification["signals"],
                    "summary": preview[:160] if preview else "No impact summary available",
                }
            )

        category_counts: dict[str, int] = {}
        for insight in insights:
            category = insight["classification"]
            category_counts[category] = category_counts.get(category, 0) + 1

        return {
            "project_id": project_id,
            "total_reports": len(reports),
            "total_insights": len(insights),
            "category_breakdown": category_counts,
            "insights": insights,
        }

    def add_report_attachment(
        self,
        project_id: str,
        report_id: str,
        filename: str,
        uploaded_by: str,
    ) -> dict:
        validation = self.validate_attachment_payload(
            report_id=report_id,
            filename=filename,
            uploaded_by=uploaded_by,
        )
        if not validation["is_valid"]:
            return {
                "success": False,
                "error_code": validation["error_code"],
                "error_message": validation["error_message"],
            }

        created_at = datetime.now(UTC).isoformat()
        attachment = {
            "id": f"{report_id}-{len(self.report_attachments.get(report_id, [])) + 1}",
            "project_id": project_id,
            "report_id": report_id,
            "filename": filename.strip(),
            "uploaded_by": uploaded_by.strip(),
            "created_at": created_at,
        }
        self.report_attachments.setdefault(report_id, []).append(attachment)
        self._safe_create_activity(
            project_id=project_id,
            activity_type="REPORT_ATTACHMENT_ADDED",
            title="Report attachment added",
            description=f"Attachment {filename} linked to report {report_id}",
            metadata={"report_id": report_id, "attachment_id": attachment["id"]},
        )
        return attachment

    def validate_attachment_payload(self, report_id: str, filename: str, uploaded_by: str) -> dict:
        if not report_id.strip():
            return {
                "is_valid": False,
                "error_code": "INVALID_REPORT_ID",
                "error_message": "Report id is required",
            }

        normalized_filename = filename.strip()
        if not normalized_filename:
            return {
                "is_valid": False,
                "error_code": "INVALID_FILENAME",
                "error_message": "Filename is required",
            }
        if len(normalized_filename) > 255:
            return {
                "is_valid": False,
                "error_code": "INVALID_FILENAME",
                "error_message": "Filename is too long",
            }
        if "/" in normalized_filename or "\\" in normalized_filename:
            return {
                "is_valid": False,
                "error_code": "INVALID_FILENAME",
                "error_message": "Filename cannot include path separators",
            }

        allowed_extensions = {"pdf", "doc", "docx", "xls", "xlsx", "csv", "txt", "png", "jpg", "jpeg"}
        extension = Path(normalized_filename).suffix.lower().lstrip(".")
        if extension not in allowed_extensions:
            return {
                "is_valid": False,
                "error_code": "UNSUPPORTED_ATTACHMENT_TYPE",
                "error_message": "Attachment type is not supported",
            }

        if not uploaded_by.strip():
            return {
                "is_valid": False,
                "error_code": "INVALID_UPLOADER",
                "error_message": "uploaded_by is required",
            }

        return {
            "is_valid": True,
            "error_code": None,
            "error_message": None,
        }

    def _scan_for_malware(self, file_path: str, filename: str) -> dict:
        path = Path(file_path)
        if not path.exists():
            return {
                "is_clean": False,
                "error_code": "MALWARE_SCAN_FAILED",
                "error_message": "File not found for malware scanning",
                "signals": ["file_missing"],
            }

        try:
            content = path.read_bytes()
        except Exception:
            return {
                "is_clean": False,
                "error_code": "MALWARE_SCAN_FAILED",
                "error_message": "File could not be read for malware scanning",
                "signals": ["read_error"],
            }

        # Local placeholder scanner: block known signatures and suspicious script patterns.
        # This keeps the flow deterministic until a real AV provider is integrated.
        eicar_signature = b"EICAR-STANDARD-ANTIVIRUS-TEST-FILE"
        suspicious_byte_signatures = [
            b"powershell -enc",
            b"cmd.exe /c",
            b"wscript.shell",
            b"CreateObject(",
            b"<script>alert(",
        ]
        lowered = content.lower()
        filename_lower = filename.lower()
        signals: list[str] = []

        if eicar_signature in content.upper():
            signals.append("eicar_signature")

        for signature in suspicious_byte_signatures:
            if signature.lower() in lowered:
                signals.append(f"signature:{signature.decode(errors='ignore')}")

        dangerous_extension = Path(filename_lower).suffix.lower().lstrip(".") in {"exe", "bat", "cmd", "ps1", "js", "vbs"}
        if dangerous_extension:
            signals.append("dangerous_extension")

        if signals:
            return {
                "is_clean": False,
                "error_code": "MALWARE_DETECTED",
                "error_message": "Uploaded file failed malware scanning",
                "signals": sorted(set(signals)),
            }

        return {
            "is_clean": True,
            "error_code": None,
            "error_message": None,
            "signals": [],
        }

    def list_report_attachments(self, report_id: str) -> list[dict]:
        return self.report_attachments.get(report_id, [])

    def delete_report_attachment(self, project_id: str, report_id: str, attachment_id: str) -> bool:
        attachments = self.report_attachments.get(report_id, [])
        remaining = [item for item in attachments if item["id"] != attachment_id]
        if len(remaining) == len(attachments):
            return False
        self.report_attachments[report_id] = remaining
        self._safe_create_activity(
            project_id=project_id,
            activity_type="REPORT_ATTACHMENT_REMOVED",
            title="Report attachment removed",
            description=f"Attachment {attachment_id} removed from report {report_id}",
            metadata={"report_id": report_id, "attachment_id": attachment_id},
        )
        return True

    def update_report_tags(self, project_id: str, report_id: str, tags: list[str]) -> dict:
        normalized_tags = sorted(
            {
                tag.strip().lower()
                for tag in tags
                if isinstance(tag, str) and tag.strip()
            }
        )
        self.report_tags[report_id] = normalized_tags
        self._safe_create_activity(
            project_id=project_id,
            activity_type="REPORT_TAGS_UPDATED",
            title="Report tags updated",
            description=f"Updated {len(normalized_tags)} tags for report {report_id}",
            metadata={"report_id": report_id, "tags": normalized_tags},
        )
        return {"project_id": project_id, "report_id": report_id, "tags": normalized_tags}

    def list_report_tags(self, report_id: str) -> list[str]:
        return self.report_tags.get(report_id, [])

    def search_reports_by_tag(self, project_id: str, tag: str) -> dict:
        normalized_tag = tag.strip().lower()
        if not normalized_tag:
            return {"project_id": project_id, "tag": normalized_tag, "report_ids": []}

        matched_report_ids = sorted(
            [
                report_id
                for report_id, tags in self.report_tags.items()
                if normalized_tag in tags
            ]
        )
        return {
            "project_id": project_id,
            "tag": normalized_tag,
            "report_ids": matched_report_ids,
            "total_reports": len(matched_report_ids),
        }

    def search_reports(
        self,
        project_id: str,
        query: str | None = None,
        *,
        tag: str | None = None,
        classification: str | None = None,
        limit: int = 20,
    ) -> dict:
        normalized_query = (query or "").strip().lower()
        normalized_tag = (tag or "").strip().lower()
        normalized_classification = (classification or "").strip().upper()
        safe_limit = max(1, min(limit, 100))

        query_terms = [
            token
            for token in re.split(r"[^a-zA-Z0-9_\-]+", normalized_query)
            if token and len(token) > 1
        ]

        entries = [
            value
            for value in self.report_index.values()
            if value.get("project_id") == project_id
        ]
        results: list[dict] = []

        for entry in entries:
            entry_classification = str(entry.get("classification") or "").upper()
            entry_tags = [
                str(item).strip().lower()
                for item in entry.get("tags", [])
                if str(item).strip()
            ]

            if normalized_tag and normalized_tag not in entry_tags:
                continue
            if normalized_classification and entry_classification != normalized_classification:
                continue

            token_set = set(entry.get("tokens", []))
            exact_matches = sorted([term for term in query_terms if term in token_set])
            partial_matches = sorted(
                [
                    term
                    for term in query_terms
                    if term not in token_set and any(term in indexed for indexed in token_set)
                ]
            )

            score = 0
            if normalized_query:
                score += len(exact_matches) * 10
                score += len(partial_matches) * 4
                filename = str(entry.get("filename") or "").lower()
                if normalized_query in filename:
                    score += 5
                if normalized_query and normalized_query in " ".join(sorted(token_set)):
                    score += 3
                if exact_matches or partial_matches:
                    score += 1
            else:
                # Filter-only queries should still return useful sorted results.
                score = 1

            if normalized_query and score == 0:
                continue

            score += self._recency_score(entry.get("indexed_at"))

            results.append(
                {
                    "report_id": entry.get("report_id"),
                    "filename": entry.get("filename"),
                    "classification": entry.get("classification"),
                    "tags": entry.get("tags", []),
                    "indexed_at": entry.get("indexed_at"),
                    "score": score,
                    "matched_terms": sorted(set(exact_matches + partial_matches)),
                    "exact_matches": exact_matches,
                    "partial_matches": partial_matches,
                }
            )

        results.sort(key=lambda item: (item.get("score", 0), item.get("indexed_at", "")), reverse=True)
        trimmed_results = results[:safe_limit]

        return {
            "project_id": project_id,
            "query": normalized_query,
            "tag": normalized_tag or None,
            "classification": normalized_classification or None,
            "total_matches": len(trimmed_results),
            "report_ids": [item["report_id"] for item in trimmed_results if item.get("report_id")],
            "results": trimmed_results,
        }

    def _recency_score(self, indexed_at: str | None) -> int:
        if not indexed_at:
            return 0
        try:
            normalized = indexed_at.replace("Z", "+00:00")
            indexed_dt = datetime.fromisoformat(normalized)
            if indexed_dt.tzinfo is None:
                indexed_dt = indexed_dt.replace(tzinfo=UTC)
            age_days = max(0.0, (datetime.now(UTC) - indexed_dt.astimezone(UTC)).total_seconds() / 86400)
        except (ValueError, TypeError):
            return 0

        if age_days <= 7:
            return 5
        if age_days <= 30:
            return 3
        if age_days <= 90:
            return 1
        return 0

    def index_report(
        self,
        *,
        project_id: str,
        report_id: str,
        filename: str,
        classification: dict,
        metadata: dict,
        ai_insights: dict,
    ) -> dict:
        tags = self.report_tags.get(report_id, [])
        tokens = self._build_index_tokens(
            filename=filename,
            classification=classification,
            metadata=metadata,
            ai_insights=ai_insights,
            tags=tags,
        )
        indexed_at = datetime.now(UTC).isoformat()
        entry = {
            "project_id": project_id,
            "report_id": report_id,
            "filename": filename,
            "classification": classification.get("category"),
            "tags": tags,
            "tokens": tokens,
            "indexed_at": indexed_at,
        }
        self.report_index[report_id] = entry
        self._safe_create_activity(
            project_id=project_id,
            activity_type="REPORT_INDEXED",
            title="Report indexed",
            description=f"Indexed report {report_id}",
            metadata={"report_id": report_id, "tokens_count": len(tokens)},
        )
        return entry

    def get_report_index_entry(self, report_id: str) -> dict | None:
        return self.report_index.get(report_id)

    def list_project_index_entries(self, project_id: str) -> dict:
        entries = [
            value
            for value in self.report_index.values()
            if value.get("project_id") == project_id
        ]
        entries.sort(key=lambda item: item.get("indexed_at", ""), reverse=True)
        return {
            "project_id": project_id,
            "total_indexed_reports": len(entries),
            "entries": entries,
        }

    def _validate_file_integrity(self, file_path: str, filename: str) -> dict:
        path = Path(file_path)
        if not path.exists():
            return {
                "is_valid": False,
                "error_code": "FILE_NOT_FOUND",
                "error_message": "Uploaded file was not found on disk",
            }

        try:
            content = path.read_bytes()
        except Exception:
            return {
                "is_valid": False,
                "error_code": "FILE_READ_ERROR",
                "error_message": "Uploaded file could not be read",
            }

        if not content:
            return {
                "is_valid": False,
                "error_code": "EMPTY_FILE",
                "error_message": "Uploaded file is empty",
            }

        extension = Path(filename).suffix.lower()
        if extension == ".pdf":
            has_pdf_header = content.startswith(b"%PDF")
            has_pdf_footer = b"%%EOF" in content[-2048:]
            if not has_pdf_header or not has_pdf_footer:
                return {
                    "is_valid": False,
                    "error_code": "CORRUPTED_PDF",
                    "error_message": "PDF file appears corrupted or incomplete",
                }

        return {
            "is_valid": True,
            "error_code": None,
            "error_message": None,
        }

    def _validate_upload_policy(self, filename: str, file_path: str) -> dict:
        extension = Path(filename).suffix.lower().lstrip(".")
        if extension not in self.ALLOWED_REPORT_EXTENSIONS:
            return {
                "is_valid": False,
                "error_code": "UNSUPPORTED_FILE_TYPE",
                "error_message": "Uploaded report type is not supported",
            }

        try:
            file_size_bytes = Path(file_path).stat().st_size
        except Exception:
            file_size_bytes = 0

        if file_size_bytes > self.MAX_REPORT_FILE_SIZE_BYTES:
            return {
                "is_valid": False,
                "error_code": "FILE_TOO_LARGE",
                "error_message": "Uploaded report exceeds the file size limit",
            }

        return {
            "is_valid": True,
            "error_code": None,
            "error_message": None,
        }

    def _build_ai_insights(self, extracted_text: str, classification: dict) -> dict:
        normalized = extracted_text.lower()
        urgency_keywords = ["urgent", "immediate", "critical", "delay", "risk", "סיכון", "דחוף"]
        urgency_score = min(100, sum(20 for word in urgency_keywords if word in normalized))

        sentiment = "neutral"
        if urgency_score >= 60:
            sentiment = "negative"
        elif "resolved" in normalized or "completed" in normalized:
            sentiment = "positive"

        return {
            "summary": extracted_text[:180] if extracted_text else "No extractable text found",
            "urgency_score": urgency_score,
            "sentiment": sentiment,
            "classification": classification["category"],
            "signals": classification.get("signals", []),
        }

    def _extract_report_metadata(self, filename: str, file_path: str, extracted_text: str) -> dict:
        file_name = filename.strip()
        file_extension = Path(filename).suffix.lower().lstrip(".") or "unknown"
        file_size_bytes = Path(file_path).stat().st_size if Path(file_path).exists() else 0

        report_week = None
        week_match = re.search(r"(?:week|wk)[\s\-_]*(\d{1,2})", file_name, flags=re.IGNORECASE)
        if week_match:
            try:
                report_week = int(week_match.group(1))
            except ValueError:
                report_week = None

        reported_at = None
        date_patterns = [
            r"(\d{4}-\d{2}-\d{2})",
            r"(\d{2}/\d{2}/\d{4})",
        ]
        for pattern in date_patterns:
            match = re.search(pattern, f"{file_name} {extracted_text[:2000]}")
            if match:
                reported_at = match.group(1)
                break

        word_count = len([token for token in re.split(r"\s+", extracted_text.strip()) if token]) if extracted_text else 0

        return {
            "file_name": file_name,
            "file_extension": file_extension,
            "file_size_bytes": file_size_bytes,
            "report_week": report_week,
            "reported_at": reported_at,
            "word_count": word_count,
            "contains_ocr_fallback": extracted_text.startswith("[OCR_FALLBACK:"),
        }

    def _build_index_tokens(
        self,
        *,
        filename: str,
        classification: dict,
        metadata: dict,
        ai_insights: dict,
        tags: list[str],
    ) -> list[str]:
        raw_chunks = [
            filename,
            classification.get("category", ""),
            " ".join(classification.get("signals", [])),
            " ".join(tags),
            str(metadata.get("file_extension", "")),
            str(metadata.get("report_week", "")),
            str(ai_insights.get("sentiment", "")),
            str(ai_insights.get("summary", ""))[:120],
        ]
        tokens: set[str] = set()
        for chunk in raw_chunks:
            for token in re.split(r"[^a-zA-Z0-9_\-]+", str(chunk).lower()):
                normalized = token.strip()
                if normalized and len(normalized) > 1:
                    tokens.add(normalized)
        return sorted(tokens)

    def _safe_create_activity(
        self,
        *,
        project_id: str,
        activity_type: str,
        title: str,
        description: str,
        metadata: dict,
    ) -> None:
        try:
            WorkspaceActivityRepository.create_activity(
                project_id=project_id,
                activity_type=activity_type,
                title=title,
                description=description,
                metadata=metadata,
            )
        except Exception:
            # Activity logging must not block report processing flows.
            return