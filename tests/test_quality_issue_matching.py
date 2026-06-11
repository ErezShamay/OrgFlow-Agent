from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.schemas.quality_issue import (
    FindingMatchInput,
    QualityIssueMatchCandidate,
    QualityIssueSeverity,
    QualityIssueStatus,
    build_match_key,
    parse_quality_issue_row,
)
from app.services.quality_issue_matching_service import (
    QualityIssueMatchingService,
    match_key_for_finding,
    match_key_for_issue,
    rank_match_candidates,
)
from tests.quality_issues_test_support import (
    InMemoryQualityIssueRepository,
    qc_create_request,
    qc_now_iso,
)


def _issue_row(
    *,
    issue_id: str,
    location: str | None = "דירה 3",
    trade: str | None = "אינסטלציה",
    group_key: str | None = "bath",
    severity: str = "MEDIUM",
    status: str = "OPEN",
    catalog_issue_id: str | None = None,
    last_seen_at: str | None = None,
    title: str = "נזילה",
) -> dict:
    return {
        "id": issue_id,
        "organization_id": "org-1",
        "project_id": "proj-1",
        "title": title,
        "severity": severity,
        "status": status,
        "location": location,
        "trade": trade,
        "group_key": group_key,
        "catalog_issue_id": catalog_issue_id,
        "first_seen_report_id": "report-1",
        "first_seen_at": qc_now_iso(),
        "last_seen_report_id": "report-1",
        "last_seen_at": last_seen_at or qc_now_iso(),
        "recurrence_count": 0,
        "photo_ids": [],
        "materialization_key": f"report-1:{issue_id}",
        "created_at": qc_now_iso(),
        "updated_at": qc_now_iso(),
    }


@pytest.fixture
def matching_service() -> QualityIssueMatchingService:
    return QualityIssueMatchingService(
        issue_repository=InMemoryQualityIssueRepository(),
    )


def test_match_key_helpers_align_with_build_match_key() -> None:
    finding = FindingMatchInput(
        location="  דירה  3  ",
        trade="אינסטלציה",
        group_key="BATH",
    )
    issue = _issue_row(issue_id="issue-1")

    expected = build_match_key(
        location="  דירה  3  ",
        trade="אינסטלציה",
        group_key="BATH",
    )
    assert match_key_for_finding(finding) == expected
    assert match_key_for_issue(issue) == expected
    assert match_key_for_issue(parse_quality_issue_row(issue)) == expected


def test_find_matches_returns_exact_match_only(
    matching_service: QualityIssueMatchingService,
) -> None:
    open_issues = [
        _issue_row(issue_id="issue-1"),
        _issue_row(
            issue_id="issue-2",
            location="דירה 4",
            trade="אינסטלציה",
            group_key="bath",
        ),
    ]
    finding = FindingMatchInput(
        location="דירה 3",
        trade="אינסטלציה",
        group_key="bath",
    )

    matches = matching_service.find_matches(
        finding=finding,
        open_issues=open_issues,
    )

    assert len(matches) == 1
    assert matches[0].issue.id == "issue-1"
    assert matches[0].score == 1.0
    assert matches[0].match_key == "דירה 3|אינסטלציה|bath"


def test_find_matches_normalizes_finding_fields(
    matching_service: QualityIssueMatchingService,
) -> None:
    open_issues = [_issue_row(issue_id="issue-1")]
    finding = FindingMatchInput(
        location="  דירה   3 ",
        trade=" אינסטלציה ",
        group_key=" BATH ",
    )

    matches = matching_service.find_matches(
        finding=finding,
        open_issues=open_issues,
    )

    assert len(matches) == 1
    assert matches[0].issue.id == "issue-1"


def test_find_matches_ranks_by_severity_then_catalog_then_recency(
    matching_service: QualityIssueMatchingService,
) -> None:
    older = datetime(2026, 6, 1, 12, 0, tzinfo=UTC).isoformat()
    newer = datetime(2026, 6, 8, 12, 0, tzinfo=UTC).isoformat()
    open_issues = [
        _issue_row(
            issue_id="issue-low",
            severity="LOW",
            last_seen_at=newer,
            title="נמוך",
        ),
        _issue_row(
            issue_id="issue-critical",
            severity="CRITICAL",
            last_seen_at=older,
            title="קריטי",
        ),
        _issue_row(
            issue_id="issue-catalog",
            severity="HIGH",
            catalog_issue_id="STR-001",
            last_seen_at=older,
            title="קטלוג",
        ),
        _issue_row(
            issue_id="issue-recent",
            severity="HIGH",
            last_seen_at=newer,
            title="עדכני",
        ),
    ]
    finding = FindingMatchInput(
        location="דירה 3",
        trade="אינסטלציה",
        group_key="bath",
        catalog_issue_id="STR-001",
    )

    matches = matching_service.find_matches(
        finding=finding,
        open_issues=open_issues,
    )

    assert [match.issue.id for match in matches] == [
        "issue-critical",
        "issue-catalog",
        "issue-recent",
        "issue-low",
    ]


def test_find_matches_respects_limit(
    matching_service: QualityIssueMatchingService,
) -> None:
    open_issues = [
        _issue_row(issue_id=f"issue-{index}", title=f"ליקוי {index}")
        for index in range(3)
    ]
    finding = FindingMatchInput(
        location="דירה 3",
        trade="אינסטלציה",
        group_key="bath",
    )

    matches = matching_service.find_matches(
        finding=finding,
        open_issues=open_issues,
        limit=2,
    )

    assert len(matches) == 2


def test_find_matches_for_project_uses_open_issues_only(
    matching_service: QualityIssueMatchingService,
) -> None:
    repo = matching_service.issue_repository
    assert isinstance(repo, InMemoryQualityIssueRepository)

    repo.create(
        organization_id="org-1",
        project_id="proj-1",
        request=qc_create_request(
            location="דירה 3",
            trade="אינסטלציה",
            group_key="bath",
            materialization_key="report-1:line-open",
        ),
        status=QualityIssueStatus.OPEN.value,
    )
    repo.create(
        organization_id="org-1",
        project_id="proj-1",
        request=qc_create_request(
            title="סגור",
            location="דירה 3",
            trade="אינסטלציה",
            group_key="bath",
            materialization_key="report-1:line-closed",
        ),
        status=QualityIssueStatus.CLOSED.value,
    )
    repo.create(
        organization_id="org-1",
        project_id="proj-2",
        request=qc_create_request(
            title="פרויקט אחר",
            location="דירה 3",
            trade="אינסטלציה",
            group_key="bath",
            materialization_key="report-2:line-other",
        ),
        status=QualityIssueStatus.OPEN.value,
    )

    finding = FindingMatchInput(
        location="דירה 3",
        trade="אינסטלציה",
        group_key="bath",
    )
    matches = matching_service.find_matches_for_project(
        organization_id="org-1",
        project_id="proj-1",
        finding=finding,
    )

    assert len(matches) == 1
    assert matches[0].issue.status == QualityIssueStatus.OPEN


def test_find_matches_returns_empty_when_no_match_key_overlap(
    matching_service: QualityIssueMatchingService,
) -> None:
    open_issues = [
        _issue_row(
            issue_id="issue-1",
            location="דירה 3",
            trade="טיח",
            group_key="bath",
        )
    ]
    finding = FindingMatchInput(
        location="דירה 3",
        trade="אינסטלציה",
        group_key="bath",
    )

    matches = matching_service.find_matches(
        finding=finding,
        open_issues=open_issues,
    )

    assert matches == []


def test_rank_match_candidates_is_stable_for_equal_scores() -> None:
    issue_a = parse_quality_issue_row(
        _issue_row(issue_id="issue-a", title="א", severity="HIGH")
    )
    issue_b = parse_quality_issue_row(
        _issue_row(issue_id="issue-b", title="ב", severity="HIGH")
    )
    candidates = [
        QualityIssueMatchCandidate(
            issue=issue_b,
            match_key="דירה 3|אינסטלציה|bath",
            score=1.0,
        ),
        QualityIssueMatchCandidate(
            issue=issue_a,
            match_key="דירה 3|אינסטלציה|bath",
            score=1.0,
        ),
    ]

    ranked = rank_match_candidates(candidates)

    assert [candidate.issue.id for candidate in ranked] == ["issue-a", "issue-b"]
