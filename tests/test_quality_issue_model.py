from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.schemas.quality_issue import (
    DEFAULT_QUALITY_ISSUE_SEVERITY,
    DEFAULT_QUALITY_ISSUE_STATUS,
    QualityIssue,
    QualityIssueSeverity,
    QualityIssueStatus,
    build_match_key,
    build_materialization_key,
    derive_issue_title,
    finding_row_qualifies_for_materialization,
    is_valid_status_transition,
    normalize_catalog_severity,
    resolve_issue_severity,
)


def test_severity_enum_values_and_rank() -> None:
    assert list(QualityIssueSeverity) == [
        QualityIssueSeverity.CRITICAL,
        QualityIssueSeverity.HIGH,
        QualityIssueSeverity.MEDIUM,
        QualityIssueSeverity.LOW,
    ]
    assert QualityIssueSeverity.CRITICAL.rank == 4
    assert QualityIssueSeverity.LOW.rank == 1
    assert QualityIssueSeverity.CRITICAL.label_he == "קריטי"


def test_status_enum_values_and_labels() -> None:
    assert QualityIssueStatus.OPEN.label_he == "פתוח"
    assert QualityIssueStatus.CLOSED.is_terminal is True
    assert QualityIssueStatus.OPEN.is_terminal is False


def test_normalize_catalog_severity_maps_catalog_values() -> None:
    assert normalize_catalog_severity("Critical") == QualityIssueSeverity.CRITICAL
    assert normalize_catalog_severity("high") == QualityIssueSeverity.HIGH
    assert normalize_catalog_severity(" Medium ") == QualityIssueSeverity.MEDIUM
    assert normalize_catalog_severity(None) is None
    assert normalize_catalog_severity("unknown") is None


def test_resolve_issue_severity_prefers_catalog_then_row() -> None:
    assert (
        resolve_issue_severity(
            catalog_severity="Critical",
            row_severity="Low",
        )
        == QualityIssueSeverity.CRITICAL
    )
    assert (
        resolve_issue_severity(
            catalog_severity=None,
            row_severity="High",
        )
        == QualityIssueSeverity.HIGH
    )
    assert resolve_issue_severity() == DEFAULT_QUALITY_ISSUE_SEVERITY


@pytest.mark.parametrize(
    ("current", "target", "expected"),
    [
        (QualityIssueStatus.OPEN, QualityIssueStatus.IN_REMEDIATION, True),
        (QualityIssueStatus.OPEN, QualityIssueStatus.CLOSED, True),
        (QualityIssueStatus.OPEN, QualityIssueStatus.PENDING_VERIFICATION, False),
        (
            QualityIssueStatus.IN_REMEDIATION,
            QualityIssueStatus.PENDING_VERIFICATION,
            True,
        ),
        (
            QualityIssueStatus.PENDING_VERIFICATION,
            QualityIssueStatus.CLOSED,
            True,
        ),
        (
            QualityIssueStatus.PENDING_VERIFICATION,
            QualityIssueStatus.OPEN,
            True,
        ),
        (QualityIssueStatus.CLOSED, QualityIssueStatus.REOPENED, True),
        (QualityIssueStatus.CLOSED, QualityIssueStatus.OPEN, False),
        (QualityIssueStatus.REOPENED, QualityIssueStatus.CLOSED, True),
        (QualityIssueStatus.OPEN, QualityIssueStatus.OPEN, True),
    ],
)
def test_status_transitions(
    current: QualityIssueStatus,
    target: QualityIssueStatus,
    expected: bool,
) -> None:
    assert is_valid_status_transition(current, target) is expected


def test_build_materialization_key() -> None:
    assert (
        build_materialization_key("report-1", "line-2")
        == "report-1:line-2"
    )


def test_build_match_key_normalizes_components() -> None:
    assert (
        build_match_key(
            location="  דירה  3  ",
            trade="אינסטלציה",
            group_key="BATH",
        )
        == "דירה 3|אינסטלציה|bath"
    )
    assert build_match_key() == "||"


@pytest.mark.parametrize(
    ("kwargs", "expected"),
    [
        (
            {"catalog_issue_name": "סדק בטון"},
            "סדק בטון",
        ),
        (
            {"description": "נזילה מתחת לכיור"},
            "נזילה מתחת לכיור",
        ),
        (
            {
                "description": "א" * 100,
                "max_description_len": 10,
            },
            "א" * 9 + "…",
        ),
        (
            {"location": "קומה 2", "trade": "חשמל"},
            "קומה 2 - חשמל",
        ),
        ({}, "ליקוי ללא תיאור"),
    ],
)
def test_derive_issue_title(kwargs: dict, expected: str) -> None:
    assert derive_issue_title(**kwargs) == expected


@pytest.mark.parametrize(
    ("kwargs", "expected"),
    [
        ({"description": "סדק"}, True),
        ({"catalog_issue_id": "STR-001"}, True),
        ({"photo_ids": ["photo-1"]}, True),
        ({"description": "   "}, False),
        ({}, False),
    ],
)
def test_finding_row_qualifies_for_materialization(
    kwargs: dict,
    expected: bool,
) -> None:
    assert finding_row_qualifies_for_materialization(**kwargs) is expected


def test_quality_issue_model_accepts_full_payload() -> None:
    now = datetime(2026, 6, 9, 12, 0, tzinfo=UTC)
    issue = QualityIssue(
        id="issue-1",
        organization_id="org-1",
        project_id="proj-1",
        title="נזילה בכיור",
        severity=QualityIssueSeverity.HIGH,
        status=DEFAULT_QUALITY_ISSUE_STATUS,
        first_seen_report_id="report-1",
        first_seen_at=now,
        last_seen_report_id="report-1",
        last_seen_at=now,
        materialization_key="report-1:line-1",
    )

    assert issue.status == QualityIssueStatus.OPEN
    assert issue.recurrence_count == 0
    assert issue.photo_ids == []
