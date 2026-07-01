"""Gate R1 — SSE / live portfolio (COMPETITIVE-LAYER-TASKS.md)."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import app.main as main_module
from app.auth.jwt_service import JWTService
from app.schemas.quality_issue import IssueVisibility
from app.services.portfolio_live_service import (
    PORTFOLIO_LIVE_SSE_EVENT,
    PortfolioLiveService,
)
from app.services.quality_issue_service import QualityIssueService
from tests.quality_issues_test_support import (
    FakeFieldVisitReportRepository,
    FakeProjectRepository,
    InMemoryQualityIssueEventRepository,
    InMemoryQualityIssueRepository,
    qc_create_request,
    qc_published_create_request,
)
from tests.test_field_visit_reports import _headers
from tests.test_supervisor_project_scope import FakeProfileRepository
import app.dependencies as deps

REPO_ROOT = Path(__file__).resolve().parents[1]


def _read_app_source() -> str:
    """Concatenates app/main.py with every app/routers/*.py and
    app/dependencies.py. Since the 2026-07 architecture-modularization
    refactor, main.py is a thin entrypoint (imports + middleware +
    include_router() calls) - route bodies and singleton wiring live in
    app/routers/*.py and app/dependencies.py. Gate tests that assert a
    given route path/snippet is "wired into the app" need to search the
    whole assembled surface, not main.py alone."""
    parts = [(REPO_ROOT / "app" / "main.py").read_text(encoding="utf-8")]
    parts.append((REPO_ROOT / "app" / "dependencies.py").read_text(encoding="utf-8"))
    for router_file in sorted((REPO_ROOT / "app" / "routers").glob("*.py")):
        if router_file.name == "__init__.py":
            continue
        parts.append(router_file.read_text(encoding="utf-8"))
    return "\n".join(parts)
ORG_ID = "org-r1"
PROJECT_ID = "proj-r1"


def _token(*, role: str = "DEVELOPER") -> str:
    return JWTService().issue_access_token(
        user_id="user-r1",
        org_id=ORG_ID,
        role=role,
        token_id=f"token-r1-{role.lower()}",
    )


def _auth_headers(*, role: str = "DEVELOPER") -> dict[str, str]:
    return _headers(_token(role=role), ORG_ID)


@pytest.fixture
def live_stack(
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[TestClient, QualityIssueService, InMemoryQualityIssueRepository]:
    issues = InMemoryQualityIssueRepository()
    events = InMemoryQualityIssueEventRepository()
    projects = FakeProjectRepository(
        projects={
            PROJECT_ID: {
                "id": PROJECT_ID,
                "organization_id": ORG_ID,
                "project_name": "מגדלי R1",
            }
        }
    )
    service = QualityIssueService(
        issue_repository=issues,
        event_repository=events,
        project_repository=projects,
        report_repository=FakeFieldVisitReportRepository(),
        profile_repository=FakeProfileRepository(profiles={}),
    )
    monkeypatch.setattr(deps, "quality_issue_service", service)
    monkeypatch.setattr(
        deps,
        "portfolio_live_service",
        PortfolioLiveService(quality_issue_service=service),
    )
    return TestClient(main_module.app), service, issues


def _seed_open_issues(issues: InMemoryQualityIssueRepository) -> None:
    issues.create(
        organization_id=ORG_ID,
        project_id=PROJECT_ID,
        request=qc_published_create_request(
            title="פתוח",
            severity="HIGH",
            materialization_key="r1-open",
        ),
    )
    issues.create(
        organization_id=ORG_ID,
        project_id=PROJECT_ID,
        request=qc_published_create_request(
            title="קריטי",
            severity="CRITICAL",
            materialization_key="r1-critical",
        ),
    )
    issues.create(
        organization_id=ORG_ID,
        project_id=PROJECT_ID,
        request=qc_create_request(
            title="טיוטה",
            severity="HIGH",
            materialization_key="r1-draft",
            visibility=IssueVisibility.DRAFT.value,
        ),
    )
    issues.create(
        organization_id=ORG_ID,
        project_id=PROJECT_ID,
        request=qc_published_create_request(
            title="סגור",
            severity="MEDIUM",
            materialization_key="r1-closed",
        ),
        status="CLOSED",
    )


def test_main_registers_r1_routes() -> None:
    main_source = _read_app_source()
    service_source = (
        REPO_ROOT / "app/services/portfolio_live_service.py"
    ).read_text(encoding="utf-8")

    assert "/portfolio/events" in main_source
    assert "/portfolio/live-snapshot" in main_source
    assert "PortfolioLiveService" in main_source
    assert "text/event-stream" in main_source
    assert PORTFOLIO_LIVE_SSE_EVENT in service_source


def test_live_snapshot_counts_published_open_only(
    live_stack: tuple[
        TestClient,
        QualityIssueService,
        InMemoryQualityIssueRepository,
    ],
) -> None:
    client, _, issues = live_stack
    _seed_open_issues(issues)

    response = client.get(
        "/portfolio/live-snapshot",
        headers=_auth_headers(role="DEVELOPER"),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["organization_id"] == ORG_ID
    assert body["total_open"] == 2
    assert body["total_open_critical"] == 1
    assert body["updated_at"]


def test_live_snapshot_requires_permission(
    live_stack: tuple[
        TestClient,
        QualityIssueService,
        InMemoryQualityIssueRepository,
    ],
) -> None:
    client, _, _ = live_stack

    response = client.get(
        "/portfolio/live-snapshot",
        headers=_auth_headers(role="CONTRACTOR"),
    )

    assert response.status_code == 403


def test_live_snapshot_service_matches_quality_summary(
    live_stack: tuple[
        TestClient,
        QualityIssueService,
        InMemoryQualityIssueRepository,
    ],
) -> None:
    _, service, issues = live_stack
    _seed_open_issues(issues)

    summary = service.get_portfolio_quality_summary(
        organization_id=ORG_ID,
        actor_role="DEVELOPER",
    )
    snapshot = service.get_portfolio_live_snapshot(
        organization_id=ORG_ID,
        actor_role="DEVELOPER",
    )

    assert snapshot.organization_id == summary.organization_id
    assert snapshot.total_open == summary.total_open
    assert snapshot.total_open_critical == summary.total_open_critical


def test_stream_events_emits_snapshot_payload(
    live_stack: tuple[
        TestClient,
        QualityIssueService,
        InMemoryQualityIssueRepository,
    ],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, service, issues = live_stack
    _seed_open_issues(issues)
    monkeypatch.setattr(
        "app.services.portfolio_live_service.PORTFOLIO_LIVE_INTERVAL_SECONDS",
        0,
    )

    async def _read_first_chunk() -> str:
        live_service = PortfolioLiveService(quality_issue_service=service)
        stream = live_service.stream_events(
            organization_id=ORG_ID,
            actor_role="DEVELOPER",
        )
        return await asyncio.wait_for(stream.__anext__(), timeout=1)

    chunk = asyncio.run(_read_first_chunk())

    assert f"event: {PORTFOLIO_LIVE_SSE_EVENT}" in chunk
    assert '"total_open": 2' in chunk or '"total_open":2' in chunk
    assert '"total_open_critical": 1' in chunk or '"total_open_critical":1' in chunk
