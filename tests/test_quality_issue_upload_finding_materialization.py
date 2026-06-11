from __future__ import annotations

from app.schemas.quality_issue import (
    QualityIssueEventType,
    QualityIssueStatus,
    build_upload_finding_materialization_key,
)
from app.services.quality_issue_upload_finding_service import (
    QualityIssueUploadFindingService,
)
from tests.quality_issues_test_support import (
    InMemoryQualityIssueEventRepository,
    InMemoryQualityIssueRepository,
    qc_now_iso,
)


class FakeProjectRepository:
    def __init__(self, organization_id: str = "org-1") -> None:
        self.organization_id = organization_id

    def get_project_by_id(self, project_id: str) -> dict | None:
        return {
            "id": project_id,
            "organization_id": self.organization_id,
        }


def _upload_finding_service(
    *,
    issues: InMemoryQualityIssueRepository | None = None,
    events: InMemoryQualityIssueEventRepository | None = None,
    organization_id: str = "org-1",
) -> QualityIssueUploadFindingService:
    return QualityIssueUploadFindingService(
        issue_repository=issues or InMemoryQualityIssueRepository(),
        event_repository=events or InMemoryQualityIssueEventRepository(),
        project_repository=FakeProjectRepository(organization_id=organization_id),
    )


def test_build_upload_finding_materialization_key() -> None:
    assert build_upload_finding_materialization_key("report-1", "finding-2") == (
        "upload:report-1:finding-2"
    )


def test_materialize_from_upload_finding_creates_quality_issue() -> None:
    issues = InMemoryQualityIssueRepository()
    events = InMemoryQualityIssueEventRepository()
    service = _upload_finding_service(issues=issues, events=events)

    result = service.materialize_from_upload_finding(
        project_id="project-1",
        report_id="weekly-report-1",
        finding={
            "id": "finding-1",
            "summary": "ליקוי איטום בגג",
            "title": "weekly.pdf",
            "finding_type": "QUALITY",
            "severity": "medium",
            "created_at": qc_now_iso(),
        },
    )

    assert result is not None
    assert result.created is True
    assert result.skipped is False
    assert result.issue_id == "issue-1"
    assert result.materialization_key == "upload:weekly-report-1:finding-1"

    issue = issues.get_by_id("issue-1")
    assert issue is not None
    assert issue["project_id"] == "project-1"
    assert issue["status"] == QualityIssueStatus.OPEN.value
    assert issue["materialization_key"] == result.materialization_key
    assert issue["first_seen_line_id"] == "finding-1"

    detected = events.list_by_issue_id("issue-1")
    assert len(detected) == 1
    assert detected[0]["event_type"] == QualityIssueEventType.DETECTED.value
    assert detected[0]["payload"]["source"] == "ai_upload"
    assert detected[0]["payload"]["finding_id"] == "finding-1"


def test_materialize_from_upload_finding_is_idempotent() -> None:
    issues = InMemoryQualityIssueRepository()
    service = _upload_finding_service(issues=issues)
    finding = {
        "id": "finding-1",
        "summary": "ליקוי חשמל",
        "finding_type": "SAFETY",
        "severity": "high",
    }

    first = service.materialize_from_upload_finding(
        project_id="project-1",
        report_id="weekly-report-1",
        finding=finding,
    )
    second = service.materialize_from_upload_finding(
        project_id="project-1",
        report_id="weekly-report-1",
        finding=finding,
    )

    assert first is not None and first.created is True
    assert second is not None and second.skipped is True
    assert second.issue_id == first.issue_id
    assert len(issues.records) == 1


def test_materialize_from_upload_finding_skips_empty_content() -> None:
    service = _upload_finding_service()

    result = service.materialize_from_upload_finding(
        project_id="project-1",
        report_id="weekly-report-1",
        finding={"id": "finding-1", "summary": "   ", "title": "   "},
    )

    assert result is None
