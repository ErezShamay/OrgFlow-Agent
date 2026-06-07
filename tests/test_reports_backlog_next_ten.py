from fastapi.testclient import TestClient

import app.main as main_module
from app.auth.jwt_service import JWTService
from app.main import app


class FakeProjectRepository:
    def __init__(self):
        self.projects = {
            "p1": {
                "id": "p1",
                "project_name": "Alpha Tower",
                "organization_id": "org-1",
            },
        }

    def get_project_by_id(self, project_id: str):
        return self.projects.get(project_id)


class FakeWeeklyReportRepository:
    def get_reports_by_project(self, project_id: str):
        if project_id != "p1":
            return []

        return [
            {
                "id": "wr-1",
                "email_subject": "weekly-report.pdf (v2)",
                "report_source": "DELAY",
                "created_at": "2026-01-01T00:00:00+00:00",
            }
        ]


class FakeReportProcessingService:
    def __init__(self):
        self._attachments = {"r1": []}
        self._tags = {"r1": []}
        self._index = {
            "r1": {
                "project_id": "p1",
                "report_id": "r1",
                "filename": "weekly-report.pdf",
                "classification": "DELAY",
                "tags": [],
                "tokens": ["delay", "weekly", "pdf"],
                "indexed_at": "2026-01-01T00:00:00Z",
            }
        }

    def process_uploaded_report(self, project_id: str, filename: str, file_path: str):
        return {
            "success": True,
            "duplicate_detected": False,
            "project_id": project_id,
            "filename": filename,
            "versioned_subject": "weekly-report.pdf (v2)",
            "report_version": 2,
            "report_id": "r1",
            "ai_interpretation_id": "ai1",
            "ocr_text_length": 42,
            "ocr_preview": "extracted text",
            "classification": {
                "category": "DELAY",
                "confidence": 0.8,
                "signals": ["delay"],
                "recommended_action": "Review schedule impact and define timeline recovery plan",
            },
            "ai_insights": {
                "summary": "Delay identified in execution sequence",
                "urgency_score": 60,
                "sentiment": "negative",
                "classification": "DELAY",
                "signals": ["delay"],
            },
            "metadata": {
                "file_name": filename,
                "file_extension": "pdf",
                "file_size_bytes": 1234,
                "report_week": 12,
                "reported_at": "2026-01-01",
                "word_count": 50,
                "contains_ocr_fallback": False,
            },
            "index": {"report_id": "r1", "indexed_at": "2026-01-01T00:00:00Z", "tokens_count": 3},
        }

    def process_bulk_uploaded_reports(self, project_id: str, uploads: list[dict]):
        job_id = "bulk-job-1"
        results = [
            self.process_uploaded_report(
                project_id=project_id,
                filename=item["filename"],
                file_path=item["file_path"],
            )
            for item in uploads
        ]
        successful = [item for item in results if item.get("success")]
        failed = [item for item in results if not item.get("success")]
        return {
            "job_id": job_id,
            "project_id": project_id,
            "total_files": len(uploads),
            "successful_uploads": len(successful),
            "failed_uploads": len(failed),
            "progress_percent": 100 if uploads else 0,
            "results": results,
        }

    def get_bulk_upload_progress(self, project_id: str, job_id: str):
        if project_id != "p1" or job_id != "bulk-job-1":
            return None
        return {
            "job_id": job_id,
            "project_id": project_id,
            "total_files": 2,
            "processed_files": 2,
            "successful_uploads": 2,
            "failed_uploads": 0,
            "progress_percent": 100,
            "status": "COMPLETED",
            "results": [
                {"success": True, "filename": "weekly-report-1.pdf"},
                {"success": True, "filename": "weekly-report-2.pdf"},
            ],
        }

    def get_project_report_timeline(self, project_id: str):
        return {
            "project_id": project_id,
            "events": [
                {
                    "id": "report-r1",
                    "event_type": "REPORT_CREATED",
                    "title": "Report ingested",
                    "description": "weekly-report.pdf (v2) (DELAY)",
                    "created_at": "2026-01-01T00:00:00Z",
                    "metadata": {"report_id": "r1"},
                },
                {
                    "id": "activity-a1",
                    "event_type": "AI_ANALYSIS",
                    "title": "AI interpretation created",
                    "description": "Initial AI interpretation generated",
                    "created_at": "2026-01-01T00:00:01Z",
                    "metadata": {},
                },
            ],
            "total_events": 2,
        }

    def get_project_report_ai_insights(self, project_id: str, limit: int = 20):
        return {
            "project_id": project_id,
            "total_reports": 2,
            "total_insights": 1,
            "category_breakdown": {"DELAY": 1},
            "insights": [
                {
                    "id": "ai1",
                    "created_at": "2026-01-01T00:00:00Z",
                    "risk_level": "MEDIUM",
                    "review_status": "PENDING",
                    "recommended_action": "Review schedule impact and define timeline recovery plan",
                    "classification": "DELAY",
                    "confidence": 0.8,
                    "signals": ["delay"],
                    "summary": "Execution delay detected",
                }
            ],
            "limit": limit,
        }

    def add_report_attachment(self, project_id: str, report_id: str, filename: str, uploaded_by: str):
        if filename.endswith(".exe"):
            return {
                "success": False,
                "error_code": "UNSUPPORTED_ATTACHMENT_TYPE",
                "error_message": "Attachment type is not supported",
            }
        attachment = {
            "id": "att-1",
            "project_id": project_id,
            "report_id": report_id,
            "filename": filename,
            "uploaded_by": uploaded_by,
            "created_at": "2026-01-01T00:00:00Z",
        }
        self._attachments.setdefault(report_id, []).append(attachment)
        return attachment

    def list_report_attachments(self, report_id: str):
        return self._attachments.get(report_id, [])

    def delete_report_attachment(self, project_id: str, report_id: str, attachment_id: str):
        attachments = self._attachments.get(report_id, [])
        for item in attachments:
            if item["id"] == attachment_id:
                self._attachments[report_id] = [entry for entry in attachments if entry["id"] != attachment_id]
                return True
        return False

    def update_report_tags(self, project_id: str, report_id: str, tags: list[str]):
        normalized = sorted({tag.strip().lower() for tag in tags if tag.strip()})
        self._tags[report_id] = normalized
        return {"project_id": project_id, "report_id": report_id, "tags": normalized}

    def list_report_tags(self, report_id: str):
        return self._tags.get(report_id, [])

    def search_reports_by_tag(self, project_id: str, tag: str):
        normalized = tag.strip().lower()
        report_ids = sorted([report_id for report_id, tags in self._tags.items() if normalized in tags])
        return {"project_id": project_id, "tag": normalized, "report_ids": report_ids, "total_reports": len(report_ids)}

    def search_reports(
        self,
        project_id: str,
        query: str | None = None,
        *,
        tag: str | None = None,
        classification: str | None = None,
        limit: int = 20,
    ):
        normalized_query = (query or "").strip().lower()
        normalized_tag = (tag or "").strip().lower()
        normalized_classification = (classification or "").strip().upper()
        entries = [value for value in self._index.values() if value["project_id"] == project_id]
        results = []
        for entry in entries:
            if normalized_tag and normalized_tag not in entry.get("tags", []):
                continue
            if normalized_classification and entry.get("classification", "").upper() != normalized_classification:
                continue
            tokens = set(entry.get("tokens", []))
            matched_terms = [term for term in normalized_query.split() if term in tokens]
            if normalized_query and not matched_terms:
                continue
            results.append(
                {
                    "report_id": entry["report_id"],
                    "filename": entry.get("filename"),
                    "classification": entry.get("classification"),
                    "tags": entry.get("tags", []),
                    "indexed_at": entry.get("indexed_at"),
                    "score": len(matched_terms) * 10 if normalized_query else 1,
                    "matched_terms": matched_terms,
                }
            )
        return {
            "project_id": project_id,
            "query": normalized_query,
            "tag": normalized_tag or None,
            "classification": normalized_classification or None,
            "total_matches": len(results[:limit]),
            "report_ids": [row["report_id"] for row in results[:limit]],
            "results": results[:limit],
        }

    def list_project_index_entries(self, project_id: str):
        entries = [value for value in self._index.values() if value["project_id"] == project_id]
        return {"project_id": project_id, "total_indexed_reports": len(entries), "entries": entries}

    def get_report_index_entry(self, report_id: str):
        return self._index.get(report_id)


class FakeCorruptedReportProcessingService:
    def process_uploaded_report(self, project_id: str, filename: str, file_path: str):
        return {
            "success": False,
            "project_id": project_id,
            "filename": filename,
            "error_code": "CORRUPTED_PDF",
            "error_message": "PDF file appears corrupted or incomplete",
        }

    def process_bulk_uploaded_reports(self, project_id: str, uploads: list[dict]):
        return {
            "job_id": "bulk-job-corrupted",
            "project_id": project_id,
            "total_files": len(uploads),
            "successful_uploads": 0,
            "failed_uploads": len(uploads),
            "progress_percent": 100 if uploads else 0,
            "results": [
                {
                    "success": False,
                    "project_id": project_id,
                    "filename": item["filename"],
                    "error_code": "CORRUPTED_PDF",
                    "error_message": "PDF file appears corrupted or incomplete",
                }
                for item in uploads
            ],
        }

    def get_bulk_upload_progress(self, project_id: str, job_id: str):
        return None


class FakeMalwareReportProcessingService:
    def process_uploaded_report(self, project_id: str, filename: str, file_path: str):
        return {
            "success": False,
            "project_id": project_id,
            "filename": filename,
            "error_code": "MALWARE_DETECTED",
            "error_message": "Uploaded file failed malware scanning",
        }


def _auth_headers():
    token = JWTService().issue_access_token(
        user_id="user-1",
        org_id="org-1",
        role="MANAGER",
        token_id="reports-tests",
    )
    return {"Authorization": f"Bearer {token}", "X-Organization-ID": "org-1"}


def _patch_report_dependencies(monkeypatch, report_processing_service):
    project_repository = FakeProjectRepository()
    monkeypatch.setattr(main_module, "project_repository", project_repository)
    monkeypatch.setattr(
        main_module.tenant_scope_service,
        "project_repository",
        project_repository,
    )
    monkeypatch.setattr(
        main_module,
        "report_processing_service",
        report_processing_service,
    )


def test_list_project_uploaded_reports(monkeypatch):
    project_repository = FakeProjectRepository()
    monkeypatch.setattr(main_module, "project_repository", project_repository)
    monkeypatch.setattr(
        main_module.tenant_scope_service,
        "project_repository",
        project_repository,
    )
    monkeypatch.setattr(
        main_module.report_processing_service,
        "report_repository",
        FakeWeeklyReportRepository(),
    )
    client = TestClient(app)

    response = client.get(
        "/projects/p1/reports/uploads",
        headers=_auth_headers(),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["project_id"] == "p1"
    assert payload["total_reports"] == 1
    assert payload["reports"][0]["title"] == "weekly-report.pdf (v2)"
    assert payload["reports"][0]["report_source"] == "DELAY"


def test_reports_ocr_pipeline_upload(monkeypatch):
    _patch_report_dependencies(monkeypatch, FakeReportProcessingService())
    client = TestClient(app)

    response = client.post(
        "/reports/upload",
        data={"project_id": "p1"},
        files={"file": ("weekly-report.pdf", b"fake-pdf-bytes", "application/pdf")},
        headers=_auth_headers(),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["duplicate_detected"] is False
    assert payload["project_id"] == "p1"
    assert payload["filename"] == "weekly-report.pdf"
    assert payload["report_version"] == 2
    assert payload["versioned_subject"] == "weekly-report.pdf (v2)"
    assert payload["ocr_text_length"] == 42
    assert payload["classification"]["category"] == "DELAY"
    assert payload["ai_insights"]["urgency_score"] == 60
    assert payload["metadata"]["file_extension"] == "pdf"
    assert payload["index"]["tokens_count"] == 3


def test_reports_ocr_pipeline_upload_project_not_found(monkeypatch):
    _patch_report_dependencies(monkeypatch, FakeReportProcessingService())
    client = TestClient(app)

    response = client.post(
        "/reports/upload",
        data={"project_id": "missing-project"},
        files={"file": ("weekly-report.pdf", b"fake-pdf-bytes", "application/pdf")},
        headers=_auth_headers(),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Project not found"


def test_reports_upload_corrupted_file_returns_422(monkeypatch):
    _patch_report_dependencies(monkeypatch, FakeCorruptedReportProcessingService())
    client = TestClient(app)

    response = client.post(
        "/reports/upload",
        data={"project_id": "p1"},
        files={"file": ("bad.pdf", b"broken", "application/pdf")},
        headers=_auth_headers(),
    )

    assert response.status_code == 422
    assert response.json()["detail"]["error_code"] == "CORRUPTED_PDF"


def test_reports_upload_malware_file_returns_422(monkeypatch):
    _patch_report_dependencies(monkeypatch, FakeMalwareReportProcessingService())
    client = TestClient(app)

    response = client.post(
        "/reports/upload",
        data={"project_id": "p1"},
        files={"file": ("infected.pdf", b"malicious-bytes", "application/pdf")},
        headers=_auth_headers(),
    )

    assert response.status_code == 422
    assert response.json()["detail"]["error_code"] == "MALWARE_DETECTED"


def test_reports_bulk_upload(monkeypatch):
    monkeypatch.setattr(main_module, "project_repository", FakeProjectRepository())
    monkeypatch.setattr(main_module, "report_processing_service", FakeReportProcessingService())
    client = TestClient(app)

    response = client.post(
        "/reports/upload/bulk",
        data={"project_id": "p1"},
        files=[
            ("files", ("weekly-report-1.pdf", b"fake-pdf-bytes-1", "application/pdf")),
            ("files", ("weekly-report-2.pdf", b"fake-pdf-bytes-2", "application/pdf")),
        ],
        headers=_auth_headers(),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["project_id"] == "p1"
    assert payload["job_id"] == "bulk-job-1"
    assert payload["total_files"] == 2
    assert payload["successful_uploads"] == 2
    assert payload["failed_uploads"] == 0
    assert payload["progress_percent"] == 100
    assert len(payload["results"]) == 2


def test_reports_bulk_upload_project_not_found(monkeypatch):
    monkeypatch.setattr(main_module, "project_repository", FakeProjectRepository())
    monkeypatch.setattr(main_module, "report_processing_service", FakeReportProcessingService())
    client = TestClient(app)

    response = client.post(
        "/reports/upload/bulk",
        data={"project_id": "missing-project"},
        files=[("files", ("weekly-report.pdf", b"fake-pdf-bytes", "application/pdf"))],
        headers=_auth_headers(),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Project not found"


def test_reports_bulk_upload_progress(monkeypatch):
    monkeypatch.setattr(main_module, "project_repository", FakeProjectRepository())
    monkeypatch.setattr(main_module, "report_processing_service", FakeReportProcessingService())
    client = TestClient(app)

    response = client.get(
        "/projects/p1/reports/upload-jobs/bulk-job-1",
        headers=_auth_headers(),
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "COMPLETED"
    assert payload["progress_percent"] == 100


def test_reports_bulk_upload_progress_missing_job(monkeypatch):
    monkeypatch.setattr(main_module, "project_repository", FakeProjectRepository())
    monkeypatch.setattr(main_module, "report_processing_service", FakeReportProcessingService())
    client = TestClient(app)

    response = client.get(
        "/projects/p1/reports/upload-jobs/missing",
        headers=_auth_headers(),
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Bulk upload job not found"


def test_report_timeline(monkeypatch):
    monkeypatch.setattr(main_module, "project_repository", FakeProjectRepository())
    monkeypatch.setattr(main_module, "report_processing_service", FakeReportProcessingService())
    client = TestClient(app)

    response = client.get("/projects/p1/reports/timeline", headers=_auth_headers())
    assert response.status_code == 200
    payload = response.json()
    assert payload["project_id"] == "p1"
    assert payload["total_events"] == 2
    assert payload["events"][0]["event_type"] in {"REPORT_CREATED", "AI_ANALYSIS"}


def test_report_timeline_project_not_found(monkeypatch):
    monkeypatch.setattr(main_module, "project_repository", FakeProjectRepository())
    monkeypatch.setattr(main_module, "report_processing_service", FakeReportProcessingService())
    client = TestClient(app)

    response = client.get("/projects/missing/reports/timeline", headers=_auth_headers())
    assert response.status_code == 404
    assert response.json()["detail"] == "Project not found"


def test_report_ai_insights(monkeypatch):
    monkeypatch.setattr(main_module, "project_repository", FakeProjectRepository())
    monkeypatch.setattr(main_module, "report_processing_service", FakeReportProcessingService())
    client = TestClient(app)

    response = client.get("/projects/p1/reports/ai-insights", headers=_auth_headers())
    assert response.status_code == 200
    payload = response.json()
    assert payload["project_id"] == "p1"
    assert payload["total_insights"] == 1
    assert payload["insights"][0]["classification"] == "DELAY"


def test_report_ai_insights_project_not_found(monkeypatch):
    monkeypatch.setattr(main_module, "project_repository", FakeProjectRepository())
    monkeypatch.setattr(main_module, "report_processing_service", FakeReportProcessingService())
    client = TestClient(app)

    response = client.get("/projects/missing/reports/ai-insights", headers=_auth_headers())
    assert response.status_code == 404
    assert response.json()["detail"] == "Project not found"


def test_report_attachments_management(monkeypatch):
    monkeypatch.setattr(main_module, "project_repository", FakeProjectRepository())
    monkeypatch.setattr(main_module, "report_processing_service", FakeReportProcessingService())
    client = TestClient(app)

    create_response = client.post(
        "/projects/p1/reports/attachments",
        json={"report_id": "r1", "filename": "annex.xlsx", "uploaded_by": "dana"},
        headers=_auth_headers(),
    )
    assert create_response.status_code == 200
    assert create_response.json()["report_id"] == "r1"

    list_response = client.get("/projects/p1/reports/r1/attachments", headers=_auth_headers())
    assert list_response.status_code == 200
    assert len(list_response.json()["attachments"]) == 1

    delete_response = client.delete("/projects/p1/reports/r1/attachments/att-1", headers=_auth_headers())
    assert delete_response.status_code == 200
    assert delete_response.json()["deleted"] is True


def test_report_attachment_delete_missing_returns_404(monkeypatch):
    monkeypatch.setattr(main_module, "project_repository", FakeProjectRepository())
    monkeypatch.setattr(main_module, "report_processing_service", FakeReportProcessingService())
    client = TestClient(app)

    response = client.delete("/projects/p1/reports/r1/attachments/missing", headers=_auth_headers())
    assert response.status_code == 404
    assert response.json()["detail"] == "Attachment not found"


def test_report_attachment_validation_returns_422(monkeypatch):
    monkeypatch.setattr(main_module, "project_repository", FakeProjectRepository())
    monkeypatch.setattr(main_module, "report_processing_service", FakeReportProcessingService())
    client = TestClient(app)

    response = client.post(
        "/projects/p1/reports/attachments",
        json={"report_id": "r1", "filename": "payload.exe", "uploaded_by": "dana"},
        headers=_auth_headers(),
    )
    assert response.status_code == 422
    assert response.json()["detail"]["error_code"] == "UNSUPPORTED_ATTACHMENT_TYPE"


def test_report_tagging_flow(monkeypatch):
    monkeypatch.setattr(main_module, "project_repository", FakeProjectRepository())
    monkeypatch.setattr(main_module, "report_processing_service", FakeReportProcessingService())
    client = TestClient(app)

    update_response = client.patch(
        "/projects/p1/reports/r1/tags",
        json={"tags": ["Delay", "Safety", "delay"]},
        headers=_auth_headers(),
    )
    assert update_response.status_code == 200
    assert update_response.json()["tags"] == ["delay", "safety"]

    list_response = client.get("/projects/p1/reports/r1/tags", headers=_auth_headers())
    assert list_response.status_code == 200
    assert list_response.json()["tags"] == ["delay", "safety"]

    search_response = client.get(
        "/projects/p1/reports/search",
        params={"tag": "safety"},
        headers=_auth_headers(),
    )
    assert search_response.status_code == 200
    assert search_response.json()["report_ids"] == ["r1"]


def test_report_indexing_endpoints(monkeypatch):
    monkeypatch.setattr(main_module, "project_repository", FakeProjectRepository())
    monkeypatch.setattr(main_module, "report_processing_service", FakeReportProcessingService())
    client = TestClient(app)

    list_response = client.get("/projects/p1/reports/index", headers=_auth_headers())
    assert list_response.status_code == 200
    assert list_response.json()["total_indexed_reports"] == 1

    get_response = client.get("/projects/p1/reports/r1/index", headers=_auth_headers())
    assert get_response.status_code == 200
    assert get_response.json()["report_id"] == "r1"


def test_report_search_engine_endpoint(monkeypatch):
    monkeypatch.setattr(main_module, "project_repository", FakeProjectRepository())
    service = FakeReportProcessingService()
    service._tags["r1"] = ["delay", "safety"]
    service._index["r1"]["tags"] = ["delay", "safety"]
    monkeypatch.setattr(main_module, "report_processing_service", service)
    client = TestClient(app)

    response = client.get(
        "/projects/p1/reports/search",
        params={"q": "delay", "classification": "delay", "tag": "safety"},
        headers=_auth_headers(),
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["total_matches"] == 1
    assert payload["report_ids"] == ["r1"]
    assert payload["results"][0]["matched_terms"] == ["delay"]


def test_report_index_entry_missing_returns_404(monkeypatch):
    monkeypatch.setattr(main_module, "project_repository", FakeProjectRepository())
    monkeypatch.setattr(main_module, "report_processing_service", FakeReportProcessingService())
    client = TestClient(app)

    response = client.get("/projects/p1/reports/missing/index", headers=_auth_headers())
    assert response.status_code == 404
    assert response.json()["detail"] == "Report index not found"
