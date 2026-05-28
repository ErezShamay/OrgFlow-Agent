from fastapi.testclient import TestClient

import app.main as main_module
from app.auth.jwt_service import JWTService
from app.main import app


class FakeProjectRepository:
    def __init__(self):
        self.projects = {
            "p1": {"id": "p1", "project_name": "Alpha Tower"},
        }

    def get_project_by_id(self, project_id: str):
        return self.projects.get(project_id)


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


def _auth_headers():
    token = JWTService().issue_access_token(
        user_id="user-1",
        org_id="org-1",
        role="MANAGER",
        token_id="reports-tests",
    )
    return {"Authorization": f"Bearer {token}", "X-Organization-ID": "org-1"}


def test_reports_ocr_pipeline_upload(monkeypatch):
    monkeypatch.setattr(main_module, "project_repository", FakeProjectRepository())
    monkeypatch.setattr(main_module, "report_processing_service", FakeReportProcessingService())
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
    monkeypatch.setattr(main_module, "project_repository", FakeProjectRepository())
    monkeypatch.setattr(main_module, "report_processing_service", FakeReportProcessingService())
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
    monkeypatch.setattr(main_module, "project_repository", FakeProjectRepository())
    monkeypatch.setattr(main_module, "report_processing_service", FakeCorruptedReportProcessingService())
    client = TestClient(app)

    response = client.post(
        "/reports/upload",
        data={"project_id": "p1"},
        files={"file": ("bad.pdf", b"broken", "application/pdf")},
        headers=_auth_headers(),
    )

    assert response.status_code == 422
    assert response.json()["detail"]["error_code"] == "CORRUPTED_PDF"


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


def test_report_index_entry_missing_returns_404(monkeypatch):
    monkeypatch.setattr(main_module, "project_repository", FakeProjectRepository())
    monkeypatch.setattr(main_module, "report_processing_service", FakeReportProcessingService())
    client = TestClient(app)

    response = client.get("/projects/p1/reports/missing/index", headers=_auth_headers())
    assert response.status_code == 404
    assert response.json()["detail"] == "Report index not found"
