from __future__ import annotations

import pytest

from app.schemas.qc_permissions import (
    QCPersona,
    can_assign_qc_role,
    can_perform_issue_transition,
    has_qc_permission,
    qc_inviteable_roles,
    resolve_qc_permissions,
    resolve_qc_persona,
    visible_issue_statuses_for_role,
)
from app.schemas.quality_issue import QualityIssueStatus


def test_qc_persona_labels() -> None:
    assert QCPersona.SUPERVISOR.label_he == "מפקח"
    assert QCPersona.CONTRACTOR.label_he == "קבלן"
    assert QCPersona.DEVELOPER.label_he == "יזם"


@pytest.mark.parametrize(
    ("role", "expected"),
    [
        ("SUPERVISOR", QCPersona.SUPERVISOR),
        ("contractor", QCPersona.CONTRACTOR),
        ("DEVELOPER", QCPersona.DEVELOPER),
        ("ADMIN", QCPersona.ADMIN),
        ("PLATFORM_ADMIN", QCPersona.ADMIN),
        ("MANAGER", QCPersona.SUPERVISOR),
        ("VIEWER", QCPersona.DEVELOPER),
        ("UNKNOWN", None),
    ],
)
def test_resolve_qc_persona(role: str, expected: QCPersona | None) -> None:
    assert resolve_qc_persona(role) == expected


def test_supervisor_has_issue_write_and_verify() -> None:
    perms = resolve_qc_permissions("SUPERVISOR")
    assert "quality_issues:write" in perms
    assert "quality_issues:verify" in perms
    assert "quality_issues:remediate" not in perms
    assert "users:write" not in perms


def test_contractor_has_remediate_only_write_capability() -> None:
    perms = resolve_qc_permissions("CONTRACTOR")
    assert "quality_issues:remediate" in perms
    assert "quality_issues:write" not in perms
    assert "field_reports:read" not in perms


def test_developer_is_read_only_portfolio() -> None:
    perms = resolve_qc_permissions("DEVELOPER")
    assert "quality_portfolio:read" in perms
    assert "field_reports:read" in perms
    assert "quality_issues:write" not in perms
    assert "field_reports:write" not in perms


def test_admin_has_user_management() -> None:
    perms = resolve_qc_permissions("ADMIN")
    assert "users:read" in perms
    assert "users:write" in perms
    assert "field_reports:admin" in perms


def test_platform_admin_gets_org_permissions() -> None:
    perms = resolve_qc_permissions("PLATFORM_ADMIN")
    assert "organizations:read" in perms
    assert "impersonation:use" in perms


def test_has_qc_permission_helper() -> None:
    assert has_qc_permission("CONTRACTOR", "quality_issues:remediate") is True
    assert has_qc_permission("CONTRACTOR", "quality_issues:verify") is False


def test_visible_issue_statuses_contractor_filtered() -> None:
    visible = visible_issue_statuses_for_role("CONTRACTOR")
    assert visible is not None
    assert QualityIssueStatus.OPEN in visible
    assert QualityIssueStatus.IN_REMEDIATION in visible
    assert QualityIssueStatus.CLOSED not in visible


def test_visible_issue_statuses_supervisor_unfiltered() -> None:
    assert visible_issue_statuses_for_role("SUPERVISOR") is None


@pytest.mark.parametrize(
    ("role", "from_status", "to_status", "expected"),
    [
        ("SUPERVISOR", QualityIssueStatus.OPEN, QualityIssueStatus.CLOSED, True),
        (
            "CONTRACTOR",
            QualityIssueStatus.IN_REMEDIATION,
            QualityIssueStatus.PENDING_VERIFICATION,
            True,
        ),
        (
            "CONTRACTOR",
            QualityIssueStatus.OPEN,
            QualityIssueStatus.CLOSED,
            False,
        ),
        (
            "DEVELOPER",
            QualityIssueStatus.OPEN,
            QualityIssueStatus.CLOSED,
            False,
        ),
        ("ADMIN", QualityIssueStatus.CLOSED, QualityIssueStatus.REOPENED, True),
    ],
)
def test_can_perform_issue_transition(
    role: str,
    from_status: QualityIssueStatus,
    to_status: QualityIssueStatus,
    expected: bool,
) -> None:
    assert can_perform_issue_transition(role, from_status, to_status) is expected


def test_qc_inviteable_roles() -> None:
    assert "CONTRACTOR" in qc_inviteable_roles("ADMIN")
    assert "ADMIN" in qc_inviteable_roles("PLATFORM_ADMIN")
    assert qc_inviteable_roles("SUPERVISOR") == ()


def test_can_assign_qc_role() -> None:
    assert can_assign_qc_role(actor_role="ADMIN", target_role="CONTRACTOR") is True
    assert can_assign_qc_role(actor_role="SUPERVISOR", target_role="CONTRACTOR") is False
