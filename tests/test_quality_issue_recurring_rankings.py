"""Roadmap 6.2 - recurring issue and contractor rankings."""

from __future__ import annotations

from app.schemas.quality_issue import QualityIssueUpdateRequest
from app.services.quality_issue_recurring_rankings import (
    UNKNOWN_CONTRACTOR_LABEL,
    build_contractor_recurring_rankings,
    build_recurring_issue_rankings,
    is_recurring_issue,
    normalize_contractor_name,
)
from app.services.quality_issue_service import QualityIssueService
from tests.quality_issues_test_support import (
    FakeProjectRepository,
    InMemoryQualityIssueEventRepository,
    InMemoryQualityIssueRepository,
    qc_create_request,
)


def test_is_recurring_issue_requires_positive_recurrence_count() -> None:
    assert is_recurring_issue({"recurrence_count": 0}) is False
    assert is_recurring_issue({"recurrence_count": 1}) is True
    assert is_recurring_issue({}) is False


def test_normalize_contractor_name_uses_fallback_for_blank() -> None:
    assert normalize_contractor_name(None) == UNKNOWN_CONTRACTOR_LABEL
    assert normalize_contractor_name("  ") == UNKNOWN_CONTRACTOR_LABEL
    assert normalize_contractor_name("קבלנות כהן") == "קבלנות כהן"


def test_build_recurring_issue_rankings_sorts_by_recurrence_and_severity() -> None:
    projects = [
        {
            "id": "proj-1",
            "project_name": "האורנים 7",
            "contractor_name": "קבלנות כהן",
        }
    ]
    issues = [
        {
            "id": "issue-1",
            "title": "טיח חוזר",
            "trade": "טיח",
            "location": "קומה 3",
            "recurrence_count": 1,
            "project_id": "proj-1",
            "status": "REOPENED",
            "severity": "HIGH",
        },
        {
            "id": "issue-2",
            "title": "נזילה חוזרת",
            "trade": "אינסטלציה",
            "recurrence_count": 3,
            "project_id": "proj-1",
            "status": "OPEN",
            "severity": "CRITICAL",
        },
        {
            "id": "issue-3",
            "title": "לא חוזר",
            "recurrence_count": 0,
            "project_id": "proj-1",
            "status": "OPEN",
            "severity": "LOW",
        },
    ]

    entries = build_recurring_issue_rankings(issues, projects=projects)

    assert [entry.issue_id for entry in entries] == ["issue-2", "issue-1"]
    assert entries[0].recurrence_count == 3
    assert entries[0].project_name == "האורנים 7"
    assert entries[0].contractor_name == "קבלנות כהן"


def test_build_contractor_recurring_rankings_groups_by_contractor() -> None:
    projects = [
        {
            "id": "proj-1",
            "project_name": "א",
            "contractor_name": "קבלנות כהן",
        },
        {
            "id": "proj-2",
            "project_name": "ב",
            "contractor_name": "קבלנות לוי",
        },
        {
            "id": "proj-3",
            "project_name": "ג",
            "contractor_name": "קבלנות כהן",
        },
    ]
    issues = [
        {
            "id": "issue-1",
            "project_id": "proj-1",
            "recurrence_count": 2,
        },
        {
            "id": "issue-2",
            "project_id": "proj-2",
            "recurrence_count": 1,
        },
        {
            "id": "issue-3",
            "project_id": "proj-3",
            "recurrence_count": 1,
        },
        {
            "id": "issue-4",
            "project_id": "proj-3",
            "recurrence_count": 0,
        },
    ]

    entries = build_contractor_recurring_rankings(issues, projects=projects)

    assert [entry.contractor_name for entry in entries] == [
        "קבלנות כהן",
        "קבלנות לוי",
    ]
    assert entries[0].recurring_issue_count == 2
    assert entries[0].total_recurrence_count == 3
    assert entries[0].project_count == 2
    assert entries[1].recurring_issue_count == 1


def test_service_portfolio_recurring_rankings_filters_project() -> None:
    projects = {
        "proj-1": {
            "id": "proj-1",
            "organization_id": "org-1",
            "project_name": "א",
            "contractor_name": "קבלנות כהן",
        },
        "proj-2": {
            "id": "proj-2",
            "organization_id": "org-1",
            "project_name": "ב",
            "contractor_name": "קבלנות לוי",
        },
    }
    service = QualityIssueService(
        issue_repository=InMemoryQualityIssueRepository(),
        event_repository=InMemoryQualityIssueEventRepository(),
        project_repository=FakeProjectRepository(projects=projects),
    )

    recurring = service.create_issue(
        organization_id="org-1",
        project_id="proj-1",
        request=qc_create_request(
            title="חוזר א",
            trade="טיח",
            materialization_key="rec-1",
        ),
        actor_role="SUPERVISOR",
    )
    service.update_issue(
        organization_id="org-1",
        issue_id=recurring["id"],
        request=QualityIssueUpdateRequest(
            status="CLOSED",
            last_seen_report_id="report-1",
        ),
        actor_role="SUPERVISOR",
        actor_id="supervisor-1",
    )
    service.update_issue(
        organization_id="org-1",
        issue_id=recurring["id"],
        request=QualityIssueUpdateRequest(
            status="REOPENED",
            last_seen_report_id="report-2",
        ),
        actor_role="SUPERVISOR",
        actor_id="supervisor-1",
    )

    service.create_issue(
        organization_id="org-1",
        project_id="proj-2",
        request=qc_create_request(
            title="לא חוזר",
            materialization_key="rec-2",
        ),
        actor_role="SUPERVISOR",
    )

    org_rankings = service.get_portfolio_recurring_rankings(
        organization_id="org-1",
        actor_role="DEVELOPER",
    )
    assert org_rankings.total_recurring == 1
    assert len(org_rankings.issues) == 1
    assert org_rankings.issues[0].recurrence_count == 1
    assert org_rankings.contractors[0].contractor_name == "קבלנות כהן"

    project_rankings = service.get_portfolio_recurring_rankings(
        organization_id="org-1",
        actor_role="DEVELOPER",
        project_id="proj-2",
    )
    assert project_rankings.project_id == "proj-2"
    assert project_rankings.total_recurring == 0
    assert project_rankings.issues == []
    assert project_rankings.contractors == []
