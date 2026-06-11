from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.schemas.quality_issue import (
    QualityIssue,
    QualityIssueCreateRequest,
    QualityIssueDetailResponse,
    QualityIssueEvent,
    QualityIssueEventCreateRequest,
    QualityIssueEventType,
    QualityIssueListQuery,
    QualityIssueListResponse,
    QualityIssueOpenListResponse,
    QualityIssueStatus,
    QualityIssueStatusUpdateRequest,
    QualityIssueUpdateRequest,
    parse_quality_issue_event_row,
    parse_quality_issue_row,
    validate_status_update,
)


def _now() -> datetime:
    return datetime(2026, 6, 9, 12, 0, tzinfo=UTC)


def test_create_request_defaults_last_seen_from_first() -> None:
    now = _now()
    request = QualityIssueCreateRequest(
        title="נזילה",
        first_seen_report_id="report-1",
        first_seen_line_id="line-1",
        first_seen_at=now,
        materialization_key="report-1:line-1",
    )
    assert request.last_seen_report_id == "report-1"
    assert request.last_seen_line_id == "line-1"
    assert request.last_seen_at == now


def test_update_request_requires_at_least_one_field() -> None:
    with pytest.raises(ValidationError):
        QualityIssueUpdateRequest()


def test_update_request_accepts_partial_fields() -> None:
    request = QualityIssueUpdateRequest(status=QualityIssueStatus.CLOSED)
    assert request.status == QualityIssueStatus.CLOSED


def test_status_update_request_for_verification() -> None:
    request = QualityIssueStatusUpdateRequest(
        status=QualityIssueStatus.CLOSED,
        report_id="report-2",
        notes="תוקן",
    )
    assert request.status == QualityIssueStatus.CLOSED
    assert request.report_id == "report-2"


def test_list_query_defaults() -> None:
    query = QualityIssueListQuery()
    assert query.limit == 50
    assert query.offset == 0


def test_event_create_request_validates_payload() -> None:
    request = QualityIssueEventCreateRequest(
        event_type=QualityIssueEventType.DETECTED,
        report_id="report-1",
        payload={
            "materialization_key": "report-1:line-1",
            "severity": "HIGH",
            "title": "סדק",
        },
    )
    assert request.event_type == QualityIssueEventType.DETECTED


def test_event_create_request_rejects_missing_report_for_detected() -> None:
    with pytest.raises(ValidationError):
        QualityIssueEventCreateRequest(
            event_type=QualityIssueEventType.DETECTED,
            payload={
                "materialization_key": "r:l",
                "severity": "HIGH",
                "title": "x",
            },
        )


def test_parse_quality_issue_row_normalizes_photo_ids() -> None:
    now = _now()
    issue = parse_quality_issue_row(
        {
            "id": "issue-1",
            "organization_id": "org-1",
            "project_id": "proj-1",
            "title": "נזילה",
            "severity": "HIGH",
            "status": "OPEN",
            "first_seen_report_id": "report-1",
            "first_seen_at": now,
            "last_seen_report_id": "report-1",
            "last_seen_at": now,
            "materialization_key": "report-1:line-1",
            "photo_ids": None,
        }
    )
    assert issue.photo_ids == []


def test_parse_quality_issue_event_row() -> None:
    event = parse_quality_issue_event_row(
        {
            "id": "event-1",
            "issue_id": "issue-1",
            "event_type": "DETECTED",
            "report_id": "report-1",
            "payload": None,
        }
    )
    assert event.event_type == QualityIssueEventType.DETECTED
    assert event.payload == {}


def test_list_and_detail_response_models() -> None:
    now = _now()
    issue = QualityIssue(
        id="issue-1",
        organization_id="org-1",
        project_id="proj-1",
        title="נזילה",
        first_seen_report_id="report-1",
        first_seen_at=now,
        last_seen_report_id="report-1",
        last_seen_at=now,
        materialization_key="report-1:line-1",
    )
    event = QualityIssueEvent(
        id="event-1",
        issue_id="issue-1",
        event_type=QualityIssueEventType.DETECTED,
        report_id="report-1",
    )

    list_response = QualityIssueListResponse(
        project_id="proj-1",
        total=1,
        limit=50,
        offset=0,
        items=[issue],
    )
    detail_response = QualityIssueDetailResponse(
        issue=issue,
        events=[event],
    )

    assert list_response.total == 1
    assert len(detail_response.events) == 1

    open_response = QualityIssueOpenListResponse(
        project_id="proj-1",
        total=1,
        items=[issue],
    )
    assert open_response.total == 1
    assert open_response.items[0].id == "issue-1"


def test_validate_status_update_accepts_valid_transition() -> None:
    validate_status_update(
        current_status=QualityIssueStatus.OPEN,
        target_status=QualityIssueStatus.IN_REMEDIATION,
    )


def test_validate_status_update_rejects_invalid_transition() -> None:
    with pytest.raises(ValueError, match="Invalid status transition"):
        validate_status_update(
            current_status=QualityIssueStatus.CLOSED,
            target_status=QualityIssueStatus.OPEN,
        )
