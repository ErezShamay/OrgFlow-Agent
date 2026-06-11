from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.exceptions.exceptions import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    ValidationError,
)
from app.schemas.quality_issue import (
    QualityIssueCreateRequest,
    QualityIssueListQuery,
    QualityIssueSeverity,
    QualityIssueStatus,
    QualityIssueSuggestMatchesRequest,
    QualityIssueUpdateRequest,
)
from app.services.quality_issue_service import QualityIssueService
from tests.quality_issues_test_support import (
    FakeProjectRepository,
    InMemoryQualityIssueEventRepository,
    InMemoryQualityIssueRepository,
    qc_create_request,
    qc_now,
)


def _now() -> datetime:
    return qc_now()


def _create_request(**overrides: object) -> QualityIssueCreateRequest:
    return qc_create_request(**overrides)


@pytest.fixture
def service() -> QualityIssueService:
    return QualityIssueService(
        issue_repository=InMemoryQualityIssueRepository(),
        event_repository=InMemoryQualityIssueEventRepository(),
        project_repository=FakeProjectRepository(),
    )


def test_create_issue_supervisor(service: QualityIssueService) -> None:
    created = service.create_issue(
        organization_id="org-1",
        project_id="proj-1",
        request=_create_request(),
        actor_role="SUPERVISOR",
        actor_id="supervisor-1",
    )

    assert created["status"] == "OPEN"
    assert created["project_id"] == "proj-1"

    events = service.event_repository.list_by_issue_id(created["id"])
    assert len(events) == 1
    assert events[0]["event_type"] == "DETECTED"


def test_create_issue_rejects_duplicate_materialization_key(
    service: QualityIssueService,
) -> None:
    service.create_issue(
        organization_id="org-1",
        project_id="proj-1",
        request=_create_request(),
        actor_role="SUPERVISOR",
    )

    with pytest.raises(ConflictError):
        service.create_issue(
            organization_id="org-1",
            project_id="proj-1",
            request=_create_request(),
            actor_role="SUPERVISOR",
        )


def test_create_issue_requires_write_permission(
    service: QualityIssueService,
) -> None:
    with pytest.raises(ForbiddenError):
        service.create_issue(
            organization_id="org-1",
            project_id="proj-1",
            request=_create_request(),
            actor_role="DEVELOPER",
        )


def test_create_issue_rejects_unknown_project(
    service: QualityIssueService,
) -> None:
    with pytest.raises(NotFoundError):
        service.create_issue(
            organization_id="org-1",
            project_id="missing",
            request=_create_request(),
            actor_role="SUPERVISOR",
        )


def test_list_issues_filters_contractor_visible_statuses(
    service: QualityIssueService,
) -> None:
    service.create_issue(
        organization_id="org-1",
        project_id="proj-1",
        request=_create_request(
            title="פתוח",
            materialization_key="report-1:line-1",
        ),
        actor_role="SUPERVISOR",
    )
    service.create_issue(
        organization_id="org-1",
        project_id="proj-1",
        request=_create_request(
            title="סגור",
            materialization_key="report-1:line-2",
        ),
        actor_role="SUPERVISOR",
    )
    closed = service.issue_repository.list_by_project(
        organization_id="org-1",
        project_id="proj-1",
    )[0]
    service.issue_repository.update(
        closed["id"],
        {"status": QualityIssueStatus.CLOSED.value},
    )

    contractor_list = service.list_issues(
        organization_id="org-1",
        project_id="proj-1",
        actor_role="CONTRACTOR",
    )
    assert contractor_list.total == 1
    assert contractor_list.items[0].status == QualityIssueStatus.OPEN

    supervisor_list = service.list_issues(
        organization_id="org-1",
        project_id="proj-1",
        actor_role="SUPERVISOR",
    )
    assert supervisor_list.total == 2


def test_get_issue_detail_hides_closed_from_contractor(
    service: QualityIssueService,
) -> None:
    created = service.create_issue(
        organization_id="org-1",
        project_id="proj-1",
        request=_create_request(),
        actor_role="SUPERVISOR",
    )
    service.issue_repository.update(
        created["id"],
        {"status": QualityIssueStatus.CLOSED.value},
    )

    with pytest.raises(NotFoundError):
        service.get_issue_detail(
            organization_id="org-1",
            issue_id=created["id"],
            actor_role="CONTRACTOR",
        )


def test_update_issue_status_to_closed_creates_verified_event(
    service: QualityIssueService,
) -> None:
    created = service.create_issue(
        organization_id="org-1",
        project_id="proj-1",
        request=_create_request(),
        actor_role="SUPERVISOR",
    )

    updated = service.update_issue(
        organization_id="org-1",
        issue_id=created["id"],
        request=QualityIssueUpdateRequest(
            status=QualityIssueStatus.CLOSED,
            last_seen_report_id="report-1",
        ),
        actor_role="SUPERVISOR",
        actor_id="supervisor-1",
    )

    assert updated["status"] == "CLOSED"
    assert updated["closed_by"] == "supervisor-1"
    assert updated["closed_at"] is not None

    events = service.event_repository.list_by_issue_id(created["id"])
    assert any(event["event_type"] == "VERIFIED_CLOSED" for event in events)


def test_update_issue_open_to_in_remediation_creates_status_changed_event(
    service: QualityIssueService,
) -> None:
    created = service.create_issue(
        organization_id="org-1",
        project_id="proj-1",
        request=_create_request(),
        actor_role="SUPERVISOR",
    )

    updated = service.update_issue(
        organization_id="org-1",
        issue_id=created["id"],
        request=QualityIssueUpdateRequest(
            status=QualityIssueStatus.IN_REMEDIATION,
        ),
        actor_role="SUPERVISOR",
        actor_id="supervisor-1",
    )

    assert updated["status"] == "IN_REMEDIATION"

    events = service.event_repository.list_by_issue_id(created["id"])
    status_events = [
        event
        for event in events
        if event["event_type"] == "STATUS_CHANGED"
    ]
    assert len(status_events) == 1
    assert status_events[0]["payload"]["from_status"] == "OPEN"
    assert status_events[0]["payload"]["to_status"] == "IN_REMEDIATION"
    assert status_events[0]["actor_id"] == "supervisor-1"


def test_contractor_cannot_mark_open_issue_in_remediation(
    service: QualityIssueService,
) -> None:
    created = service.create_issue(
        organization_id="org-1",
        project_id="proj-1",
        request=_create_request(),
        actor_role="SUPERVISOR",
    )

    with pytest.raises(ForbiddenError):
        service.update_issue(
            organization_id="org-1",
            issue_id=created["id"],
            request=QualityIssueUpdateRequest(
                status=QualityIssueStatus.IN_REMEDIATION,
            ),
            actor_role="CONTRACTOR",
            actor_id="contractor-1",
        )


def test_update_issue_rejects_invalid_transition(
    service: QualityIssueService,
) -> None:
    created = service.create_issue(
        organization_id="org-1",
        project_id="proj-1",
        request=_create_request(),
        actor_role="SUPERVISOR",
    )

    with pytest.raises(ValidationError):
        service.update_issue(
            organization_id="org-1",
            issue_id=created["id"],
            request=QualityIssueUpdateRequest(
                status=QualityIssueStatus.PENDING_VERIFICATION,
            ),
            actor_role="SUPERVISOR",
            actor_id="supervisor-1",
        )


def test_contractor_can_submit_remediation(
    service: QualityIssueService,
) -> None:
    created = service.create_issue(
        organization_id="org-1",
        project_id="proj-1",
        request=_create_request(),
        actor_role="SUPERVISOR",
    )
    service.issue_repository.update(
        created["id"],
        {"status": QualityIssueStatus.IN_REMEDIATION.value},
    )

    updated = service.update_issue(
        organization_id="org-1",
        issue_id=created["id"],
        request=QualityIssueUpdateRequest(
            status=QualityIssueStatus.PENDING_VERIFICATION,
            photo_ids=["photo-1"],
        ),
        actor_role="CONTRACTOR",
        actor_id="contractor-1",
    )

    assert updated["status"] == "PENDING_VERIFICATION"
    events = service.event_repository.list_by_issue_id(created["id"])
    remediation_events = [
        event
        for event in events
        if event["event_type"] == "REMEDIATION_SUBMITTED"
    ]
    assert len(remediation_events) == 1


def test_contractor_remediation_submission_requires_photo(
    service: QualityIssueService,
) -> None:
    created = service.create_issue(
        organization_id="org-1",
        project_id="proj-1",
        request=_create_request(),
        actor_role="SUPERVISOR",
    )
    service.issue_repository.update(
        created["id"],
        {"status": QualityIssueStatus.IN_REMEDIATION.value},
    )

    with pytest.raises(ValidationError, match="נדרשת לפחות"):
        service.update_issue(
            organization_id="org-1",
            issue_id=created["id"],
            request=QualityIssueUpdateRequest(
                status=QualityIssueStatus.PENDING_VERIFICATION,
                notes="  הוחלפה ברז  ",
            ),
            actor_role="CONTRACTOR",
            actor_id="contractor-1",
        )


def test_supervisor_verifies_close_from_pending_verification(
    service: QualityIssueService,
) -> None:
    created = service.create_issue(
        organization_id="org-1",
        project_id="proj-1",
        request=_create_request(),
        actor_role="SUPERVISOR",
    )
    service.issue_repository.update(
        created["id"],
        {"status": QualityIssueStatus.PENDING_VERIFICATION.value},
    )

    updated = service.update_issue(
        organization_id="org-1",
        issue_id=created["id"],
        request=QualityIssueUpdateRequest(
            status=QualityIssueStatus.CLOSED,
            last_seen_report_id="report-2",
        ),
        actor_role="SUPERVISOR",
        actor_id="supervisor-1",
    )

    assert updated["status"] == "CLOSED"
    assert updated["closed_by"] == "supervisor-1"
    assert updated["closed_at"] is not None

    events = service.event_repository.list_by_issue_id(created["id"])
    verified_events = [
        event
        for event in events
        if event["event_type"] == "VERIFIED_CLOSED"
    ]
    assert len(verified_events) == 1
    assert verified_events[0]["payload"]["from_status"] == "PENDING_VERIFICATION"
    assert verified_events[0]["payload"]["to_status"] == "CLOSED"
    assert verified_events[0]["actor_id"] == "supervisor-1"


def test_contractor_cannot_close_issue(service: QualityIssueService) -> None:
    created = service.create_issue(
        organization_id="org-1",
        project_id="proj-1",
        request=_create_request(),
        actor_role="SUPERVISOR",
    )

    with pytest.raises(ForbiddenError):
        service.update_issue(
            organization_id="org-1",
            issue_id=created["id"],
            request=QualityIssueUpdateRequest(
                status=QualityIssueStatus.CLOSED,
                last_seen_report_id="report-1",
            ),
            actor_role="CONTRACTOR",
            actor_id="contractor-1",
        )


def test_reopen_increments_recurrence_count(
    service: QualityIssueService,
) -> None:
    created = service.create_issue(
        organization_id="org-1",
        project_id="proj-1",
        request=_create_request(),
        actor_role="SUPERVISOR",
    )
    service.update_issue(
        organization_id="org-1",
        issue_id=created["id"],
        request=QualityIssueUpdateRequest(
            status=QualityIssueStatus.CLOSED,
            last_seen_report_id="report-1",
        ),
        actor_role="SUPERVISOR",
        actor_id="supervisor-1",
    )

    reopened = service.update_issue(
        organization_id="org-1",
        issue_id=created["id"],
        request=QualityIssueUpdateRequest(
            status=QualityIssueStatus.REOPENED,
            last_seen_report_id="report-2",
        ),
        actor_role="SUPERVISOR",
        actor_id="supervisor-1",
    )

    assert reopened["status"] == "REOPENED"
    assert reopened["recurrence_count"] == 1
    assert reopened["closed_at"] is None

    events = service.event_repository.list_by_issue_id(created["id"])
    reopened_events = [
        event for event in events if event["event_type"] == "REOPENED"
    ]
    assert len(reopened_events) == 1
    assert reopened_events[0]["payload"]["from_status"] == "CLOSED"
    assert reopened_events[0]["payload"]["to_status"] == "REOPENED"
    assert reopened_events[0]["payload"]["recurrence_count"] == 1
    assert reopened_events[0]["actor_id"] == "supervisor-1"


def test_closure_lifecycle_events_sequence(service: QualityIssueService) -> None:
    created = service.create_issue(
        organization_id="org-1",
        project_id="proj-1",
        request=_create_request(),
        actor_role="SUPERVISOR",
    )
    issue_id = created["id"]

    service.update_issue(
        organization_id="org-1",
        issue_id=issue_id,
        request=QualityIssueUpdateRequest(
            status=QualityIssueStatus.IN_REMEDIATION,
        ),
        actor_role="SUPERVISOR",
        actor_id="supervisor-1",
    )

    service.update_issue(
        organization_id="org-1",
        issue_id=issue_id,
        request=QualityIssueUpdateRequest(
            status=QualityIssueStatus.PENDING_VERIFICATION,
            notes="הוחלפה ברז",
            photo_ids=["photo-1"],
        ),
        actor_role="CONTRACTOR",
        actor_id="contractor-1",
    )

    service.update_issue(
        organization_id="org-1",
        issue_id=issue_id,
        request=QualityIssueUpdateRequest(
            status=QualityIssueStatus.CLOSED,
            last_seen_report_id="report-2",
        ),
        actor_role="SUPERVISOR",
        actor_id="supervisor-1",
    )

    service.update_issue(
        organization_id="org-1",
        issue_id=issue_id,
        request=QualityIssueUpdateRequest(
            status=QualityIssueStatus.REOPENED,
            last_seen_report_id="report-3",
        ),
        actor_role="SUPERVISOR",
        actor_id="supervisor-1",
    )

    events = service.event_repository.list_by_issue_id(issue_id)
    event_types = [event["event_type"] for event in events]

    assert "REMEDIATION_SUBMITTED" in event_types
    assert "VERIFIED_CLOSED" in event_types
    assert "REOPENED" in event_types

    remediation = next(
        event
        for event in events
        if event["event_type"] == "REMEDIATION_SUBMITTED"
    )
    assert remediation["payload"]["notes"] == "הוחלפה ברז"
    assert remediation["payload"]["photo_ids"] == ["photo-1"]

    verified = next(
        event for event in events if event["event_type"] == "VERIFIED_CLOSED"
    )
    assert verified["payload"]["from_status"] == "PENDING_VERIFICATION"
    assert verified["payload"]["to_status"] == "CLOSED"

    reopened = next(event for event in events if event["event_type"] == "REOPENED")
    assert reopened["payload"]["recurrence_count"] == 1


def test_list_open_issues(service: QualityIssueService) -> None:
    service.create_issue(
        organization_id="org-1",
        project_id="proj-1",
        request=_create_request(materialization_key="k1"),
        actor_role="SUPERVISOR",
    )
    closed = service.create_issue(
        organization_id="org-1",
        project_id="proj-1",
        request=_create_request(
            title="סגור",
            materialization_key="k2",
        ),
        actor_role="SUPERVISOR",
    )
    service.issue_repository.update(
        closed["id"],
        {"status": QualityIssueStatus.CLOSED.value},
    )

    open_issues = service.list_open_issues(
        organization_id="org-1",
        project_id="proj-1",
        actor_role="SUPERVISOR",
    )
    assert open_issues.total == 1
    assert open_issues.items[0].status == QualityIssueStatus.OPEN


def test_suggest_matches_returns_ranked_open_issues(
    service: QualityIssueService,
) -> None:
    service.create_issue(
        organization_id="org-1",
        project_id="proj-1",
        request=_create_request(
            title="נזילה",
            location="דירה 3",
            trade="אינסטלציה",
            group_key="bath",
            materialization_key="k1",
        ),
        actor_role="SUPERVISOR",
    )
    service.create_issue(
        organization_id="org-1",
        project_id="proj-1",
        request=_create_request(
            title="אחר",
            location="דירה 4",
            trade="אינסטלציה",
            group_key="bath",
            materialization_key="k2",
        ),
        actor_role="SUPERVISOR",
    )

    response = service.suggest_matches(
        organization_id="org-1",
        project_id="proj-1",
        request=QualityIssueSuggestMatchesRequest(
            location="דירה 3",
            trade="אינסטלציה",
            group_key="bath",
        ),
        actor_role="SUPERVISOR",
    )

    assert response.project_id == "proj-1"
    assert response.match_key == "דירה 3|אינסטלציה|bath"
    assert response.total == 1
    assert response.candidates[0].issue.title == "נזילה"


def test_list_issues_respects_query_filters(
    service: QualityIssueService,
) -> None:
    service.create_issue(
        organization_id="org-1",
        project_id="proj-1",
        request=_create_request(
            title="קריטי",
            severity=QualityIssueSeverity.CRITICAL,
            materialization_key="k1",
        ),
        actor_role="SUPERVISOR",
    )
    service.create_issue(
        organization_id="org-1",
        project_id="proj-1",
        request=_create_request(
            title="נמוך",
            severity=QualityIssueSeverity.LOW,
            materialization_key="k2",
        ),
        actor_role="SUPERVISOR",
    )

    response = service.list_issues(
        organization_id="org-1",
        project_id="proj-1",
        query=QualityIssueListQuery(severity=[QualityIssueSeverity.CRITICAL]),
        actor_role="SUPERVISOR",
    )

    assert response.total == 1
    assert response.items[0].severity == QualityIssueSeverity.CRITICAL


def test_portfolio_quality_summary_aggregates_kpis(
    service: QualityIssueService,
) -> None:
    old_seen = datetime(2026, 5, 20, 12, 0, tzinfo=UTC)
    service.create_issue(
        organization_id="org-1",
        project_id="proj-1",
        request=_create_request(
            title="קריטי ישן",
            severity=QualityIssueSeverity.CRITICAL,
            first_seen_at=old_seen,
            materialization_key="k1",
        ),
        actor_role="SUPERVISOR",
    )
    service.create_issue(
        organization_id="org-1",
        project_id="proj-1",
        request=_create_request(
            title="פתוח",
            severity=QualityIssueSeverity.MEDIUM,
            materialization_key="k2",
        ),
        actor_role="SUPERVISOR",
    )
    closed = service.create_issue(
        organization_id="org-1",
        project_id="proj-2",
        request=_create_request(
            title="סגור",
            materialization_key="k3",
        ),
        actor_role="SUPERVISOR",
    )
    service.update_issue(
        organization_id="org-1",
        issue_id=closed["id"],
        request=QualityIssueUpdateRequest(
            status=QualityIssueStatus.CLOSED,
            last_seen_report_id="report-1",
        ),
        actor_role="SUPERVISOR",
        actor_id="supervisor-1",
    )

    summary = service.get_portfolio_quality_summary(
        organization_id="org-1",
        actor_role="SUPERVISOR",
    )

    assert summary.total_open == 2
    assert summary.total_open_critical == 1
    assert summary.critical_open_over_14_days == 1
    assert summary.average_open_days is not None
    assert summary.projects[0].project_id == "proj-1"
    assert summary.projects[0].open_total == 2
    assert summary.projects[0].open_critical == 1
    proj_two = next(
        project for project in summary.projects if project.project_id == "proj-2"
    )
    assert proj_two.open_total == 0


def test_portfolio_quality_summary_requires_permission(
    service: QualityIssueService,
) -> None:
    with pytest.raises(ForbiddenError):
        service.get_portfolio_quality_summary(
            organization_id="org-1",
            actor_role="CONTRACTOR",
        )


def test_portfolio_quality_summary_allows_developer(
    service: QualityIssueService,
) -> None:
    summary = service.get_portfolio_quality_summary(
        organization_id="org-1",
        actor_role="DEVELOPER",
    )
    assert summary.organization_id == "org-1"
    assert summary.total_open == 0
