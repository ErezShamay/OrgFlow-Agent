from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.schemas.quality_issue import (
    QualityIssueEvent,
    QualityIssueEventType,
    QualityIssueSeverity,
    QualityIssueStatus,
    preferred_event_type_for_transition,
    validate_event_fields,
    validate_event_payload,
)


def test_event_type_enum_values_and_labels() -> None:
    assert list(QualityIssueEventType) == [
        QualityIssueEventType.DETECTED,
        QualityIssueEventType.LINKED,
        QualityIssueEventType.REMEDIATION_SUBMITTED,
        QualityIssueEventType.VERIFIED_CLOSED,
        QualityIssueEventType.REOPENED,
        QualityIssueEventType.STATUS_CHANGED,
    ]
    assert QualityIssueEventType.DETECTED.label_he == "התגלות"
    assert QualityIssueEventType.VERIFIED_CLOSED.label_he == "אושר ונסגר"


@pytest.mark.parametrize(
    ("from_status", "to_status", "expected"),
    [
        (None, QualityIssueStatus.OPEN, QualityIssueEventType.DETECTED),
        (
            QualityIssueStatus.CLOSED,
            QualityIssueStatus.REOPENED,
            QualityIssueEventType.REOPENED,
        ),
        (
            QualityIssueStatus.IN_REMEDIATION,
            QualityIssueStatus.PENDING_VERIFICATION,
            QualityIssueEventType.REMEDIATION_SUBMITTED,
        ),
        (
            QualityIssueStatus.PENDING_VERIFICATION,
            QualityIssueStatus.CLOSED,
            QualityIssueEventType.VERIFIED_CLOSED,
        ),
        (
            QualityIssueStatus.OPEN,
            QualityIssueStatus.CLOSED,
            QualityIssueEventType.VERIFIED_CLOSED,
        ),
        (
            QualityIssueStatus.OPEN,
            QualityIssueStatus.IN_REMEDIATION,
            QualityIssueEventType.STATUS_CHANGED,
        ),
    ],
)
def test_preferred_event_type_for_transition(
    from_status: QualityIssueStatus | None,
    to_status: QualityIssueStatus,
    expected: QualityIssueEventType,
) -> None:
    assert preferred_event_type_for_transition(from_status, to_status) == expected


def test_validate_detected_payload() -> None:
    payload = validate_event_payload(
        QualityIssueEventType.DETECTED,
        {
            "materialization_key": "report-1:line-1",
            "severity": "HIGH",
            "title": "נזילה",
            "catalog_issue_id": "STR-001",
        },
    )
    assert payload["severity"] == "HIGH"
    assert payload["materialization_key"] == "report-1:line-1"


def test_validate_detected_payload_rejects_missing_required() -> None:
    with pytest.raises(Exception):
        validate_event_payload(QualityIssueEventType.DETECTED, {"title": "x"})


def test_validate_linked_payload_accepts_manual_match_source() -> None:
    payload = validate_event_payload(
        QualityIssueEventType.LINKED,
        {"match_key": "דירה 3|אינסטלציה|bath", "match_source": "manual"},
    )
    assert payload["match_source"] == "manual"


def test_validate_linked_payload_rejects_invalid_match_source() -> None:
    with pytest.raises(Exception):
        validate_event_payload(
            QualityIssueEventType.LINKED,
            {"match_source": "suggested"},
        )


def test_validate_remediation_payload_requires_status_fields() -> None:
    payload = validate_event_payload(
        QualityIssueEventType.REMEDIATION_SUBMITTED,
        {
            "from_status": "IN_REMEDIATION",
            "to_status": "PENDING_VERIFICATION",
            "photo_ids": ["photo-1"],
        },
    )
    assert payload["to_status"] == "PENDING_VERIFICATION"
    assert payload["photo_ids"] == ["photo-1"]


def test_validate_reopened_payload_requires_recurrence_count() -> None:
    with pytest.raises(Exception):
        validate_event_payload(
            QualityIssueEventType.REOPENED,
            {
                "from_status": "CLOSED",
                "to_status": "REOPENED",
            },
        )

    payload = validate_event_payload(
        QualityIssueEventType.REOPENED,
        {
            "from_status": "CLOSED",
            "to_status": "REOPENED",
            "recurrence_count": 1,
            "previous_closed_at": "2026-06-01T10:00:00Z",
        },
    )
    assert payload["recurrence_count"] == 1


def test_validate_verified_closed_payload_requires_closed_target() -> None:
    with pytest.raises(Exception):
        validate_event_payload(
            QualityIssueEventType.VERIFIED_CLOSED,
            {
                "from_status": "OPEN",
                "to_status": "OPEN",
            },
        )

    payload = validate_event_payload(
        QualityIssueEventType.VERIFIED_CLOSED,
        {"from_status": "PENDING_VERIFICATION", "to_status": "CLOSED"},
    )
    assert payload["to_status"] == "CLOSED"


def test_validate_status_changed_rejects_invalid_transition() -> None:
    with pytest.raises(ValueError, match="Invalid status transition"):
        validate_event_payload(
            QualityIssueEventType.STATUS_CHANGED,
            {
                "from_status": "CLOSED",
                "to_status": "OPEN",
            },
        )


def test_validate_event_fields_requires_report_id_for_detected() -> None:
    with pytest.raises(ValueError, match="requires report_id"):
        validate_event_fields(
            event_type=QualityIssueEventType.DETECTED,
            report_id=None,
            payload={
                "materialization_key": "r:l",
                "severity": "MEDIUM",
                "title": "t",
            },
        )


def test_validate_event_fields_requires_actor_for_status_changed() -> None:
    with pytest.raises(ValueError, match="requires actor_id"):
        validate_event_fields(
            event_type=QualityIssueEventType.STATUS_CHANGED,
            actor_id=None,
            payload={
                "from_status": "OPEN",
                "to_status": "IN_REMEDIATION",
            },
        )


def test_validate_event_fields_accepts_complete_detected_event() -> None:
    payload = validate_event_fields(
        event_type=QualityIssueEventType.DETECTED,
        report_id="report-1",
        payload={
            "materialization_key": "report-1:line-1",
            "severity": "LOW",
            "title": "סדק",
        },
    )
    assert payload["title"] == "סדק"


def test_quality_issue_event_model_accepts_full_payload() -> None:
    now = datetime(2026, 6, 9, 14, 0, tzinfo=UTC)
    event = QualityIssueEvent(
        id="event-1",
        issue_id="issue-1",
        event_type=QualityIssueEventType.REOPENED,
        report_id="report-2",
        line_id="line-5",
        payload={
            "from_status": "CLOSED",
            "to_status": "REOPENED",
            "recurrence_count": 2,
        },
        created_at=now,
    )

    assert event.event_type == QualityIssueEventType.REOPENED
    assert event.payload["recurrence_count"] == 2
