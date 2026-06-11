from __future__ import annotations

import pytest

from app.repositories.quality_issue_repository import (
    OPEN_ISSUE_STATUSES,
    QualityIssueEventRepository,
    QualityIssueRepository,
    matches_issue_list_filters,
)
from app.schemas.quality_issue import (
    QualityIssueListQuery,
    QualityIssueSeverity,
    QualityIssueStatus,
)
from tests.quality_issues_test_support import (
    InMemoryQualityIssueEventRepository,
    InMemoryQualityIssueRepository,
    qc_create_request,
    qc_now,
)


def _now() -> datetime:
    return qc_now()


def _create_request(**overrides: object):
    return qc_create_request(**overrides)


@pytest.fixture
def issue_repo() -> InMemoryQualityIssueRepository:
    return InMemoryQualityIssueRepository()


@pytest.fixture
def event_repo() -> InMemoryQualityIssueEventRepository:
    return InMemoryQualityIssueEventRepository()


def test_open_issue_statuses_exclude_closed() -> None:
    assert QualityIssueStatus.CLOSED.value not in OPEN_ISSUE_STATUSES
    assert QualityIssueStatus.OPEN.value in OPEN_ISSUE_STATUSES


def test_matches_issue_list_filters_by_status_and_search() -> None:
    record = {
        "status": "OPEN",
        "severity": "HIGH",
        "trade": "אינסטלציה",
        "title": "נזילה בכיור",
        "description": "",
        "location": "דירה 3",
    }
    assert matches_issue_list_filters(
        record,
        statuses=["OPEN"],
        search="כיור",
    )
    assert not matches_issue_list_filters(record, statuses=["CLOSED"])
    assert not matches_issue_list_filters(record, trade="חשמל")


def test_create_and_get_by_materialization_key(issue_repo: InMemoryQualityIssueRepository) -> None:
    created = issue_repo.create(
        organization_id="org-1",
        project_id="proj-1",
        request=_create_request(),
    )
    fetched = issue_repo.get_by_materialization_key(
        organization_id="org-1",
        materialization_key="report-1:line-1",
    )
    assert fetched is not None
    assert fetched["id"] == created["id"]


def test_get_for_organization_enforces_tenant(issue_repo: InMemoryQualityIssueRepository) -> None:
    created = issue_repo.create(
        organization_id="org-1",
        project_id="proj-1",
        request=_create_request(),
    )
    assert (
        issue_repo.get_for_organization(
            issue_id=created["id"],
            organization_id="org-1",
        )
        is not None
    )
    assert (
        issue_repo.get_for_organization(
            issue_id=created["id"],
            organization_id="org-2",
        )
        is None
    )


def test_list_by_project_filters_status_and_paginates(
    issue_repo: InMemoryQualityIssueRepository,
) -> None:
    issue_repo.create(
        organization_id="org-1",
        project_id="proj-1",
        request=_create_request(
            title="פתוח",
            materialization_key="report-1:line-1",
        ),
        status=QualityIssueStatus.OPEN.value,
    )
    issue_repo.create(
        organization_id="org-1",
        project_id="proj-1",
        request=_create_request(
            title="סגור",
            materialization_key="report-1:line-2",
        ),
        status=QualityIssueStatus.CLOSED.value,
    )

    open_only = issue_repo.list_by_project(
        organization_id="org-1",
        project_id="proj-1",
        query=QualityIssueListQuery(status=[QualityIssueStatus.OPEN]),
    )
    assert len(open_only) == 1
    assert open_only[0]["status"] == "OPEN"

    paged = issue_repo.list_by_project(
        organization_id="org-1",
        project_id="proj-1",
        query=QualityIssueListQuery(limit=1, offset=0),
    )
    assert len(paged) == 1
    assert issue_repo.count_by_project(
        organization_id="org-1",
        project_id="proj-1",
    ) == 2


def test_list_open_by_project_excludes_closed(
    issue_repo: InMemoryQualityIssueRepository,
) -> None:
    issue_repo.create(
        organization_id="org-1",
        project_id="proj-1",
        request=_create_request(materialization_key="k1"),
        status=QualityIssueStatus.OPEN.value,
    )
    issue_repo.create(
        organization_id="org-1",
        project_id="proj-1",
        request=_create_request(
            title="סגור",
            materialization_key="k2",
        ),
        status=QualityIssueStatus.CLOSED.value,
    )

    open_issues = issue_repo.list_open_by_project(
        organization_id="org-1",
        project_id="proj-1",
    )
    assert len(open_issues) == 1
    assert open_issues[0]["status"] == "OPEN"


def test_update_issue(issue_repo: InMemoryQualityIssueRepository) -> None:
    created = issue_repo.create(
        organization_id="org-1",
        project_id="proj-1",
        request=_create_request(),
    )
    updated = issue_repo.update(
        created["id"],
        {"status": QualityIssueStatus.CLOSED.value},
    )
    assert updated is not None
    assert updated["status"] == "CLOSED"


def test_update_issue_can_clear_closed_at(
    issue_repo: InMemoryQualityIssueRepository,
) -> None:
    created = issue_repo.create(
        organization_id="org-1",
        project_id="proj-1",
        request=_create_request(),
    )
    issue_repo.update(
        created["id"],
        {
            "status": QualityIssueStatus.CLOSED.value,
            "closed_at": _now().isoformat(),
            "closed_by": "supervisor-1",
        },
    )
    updated = issue_repo.update(
        created["id"],
        {
            "status": QualityIssueStatus.REOPENED.value,
            "closed_at": None,
            "closed_by": None,
        },
    )
    assert updated is not None
    assert updated["closed_at"] is None
    assert updated["closed_by"] is None


def test_event_repository_append_and_list(
    event_repo: InMemoryQualityIssueEventRepository,
) -> None:
    event_repo.create(
        issue_id="issue-1",
        event_type="DETECTED",
        report_id="report-1",
        payload={"title": "נזילה"},
    )
    event_repo.create(
        issue_id="issue-1",
        event_type="VERIFIED_CLOSED",
        report_id="report-2",
        actor_id="supervisor-1",
        payload={"to_status": "CLOSED"},
    )

    by_issue = event_repo.list_by_issue_id("issue-1")
    by_report = event_repo.list_by_report_id("report-2")

    assert len(by_issue) == 2
    assert len(by_report) == 1
    assert by_report[0]["event_type"] == "VERIFIED_CLOSED"


def test_repository_classes_expose_table_names() -> None:
    assert QualityIssueRepository.TABLE == "quality_issues"
    assert QualityIssueEventRepository.TABLE == "quality_issue_events"


def test_list_by_organization_returns_org_scoped_records(
    issue_repo: InMemoryQualityIssueRepository,
) -> None:
    issue_repo.create(
        organization_id="org-1",
        project_id="proj-1",
        request=_create_request(materialization_key="org1"),
    )
    issue_repo.create(
        organization_id="org-2",
        project_id="proj-2",
        request=_create_request(materialization_key="org2"),
    )

    org_one = issue_repo.list_by_organization(organization_id="org-1")
    assert len(org_one) == 1
    assert org_one[0]["organization_id"] == "org-1"
