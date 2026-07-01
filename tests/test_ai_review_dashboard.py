from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

import app.main as main_module
from app.auth.jwt_service import JWTService
from app.main import app
from app.services.ai_review_service import (
    AIReviewService,
)
from app.services.tenant_scope_service import (
    TenantScopeService,
)
import app.dependencies as deps


def _auth_headers():
    token = JWTService().issue_access_token(
        user_id="user-1",
        org_id="org-1",
        role="MANAGER",
        token_id="review-dashboard-tests",
    )
    return {"Authorization": f"Bearer {token}", "X-Organization-ID": "org-1"}


def test_ai_review_dashboard_service_aggregates_status_and_overdue():
    service = AIReviewService.__new__(AIReviewService)

    old_pending = (
        datetime
        .now(UTC) - timedelta(hours=60)
    ).isoformat()

    recent_pending = (
        datetime
        .now(UTC) - timedelta(hours=4)
    ).isoformat()

    class FakeRepository:
        def get_pending_reviews(self):
            return [
                {"id": "r-1", "review_status": "PENDING", "created_at": old_pending},
                {"id": "r-2", "review_status": "PENDING", "created_at": recent_pending},
            ]

        def get_reviews_by_status(self, review_status: str):
            if review_status == "APPROVED":
                return [
                    {"id": "r-3", "review_status": "APPROVED", "created_at": recent_pending},
                ]
            if review_status == "REJECTED":
                return [
                    {"id": "r-4", "review_status": "REJECTED", "created_at": recent_pending},
                ]
            return []

        def get_recent_reviews(self, limit: int = 20):
            return [
                {"id": "r-4", "review_status": "REJECTED", "created_at": recent_pending},
                {"id": "r-3", "review_status": "APPROVED", "created_at": recent_pending},
            ][:limit]

        def count_reviews(self):
            return 4

    service.repository = FakeRepository()

    payload = service.get_review_dashboard(recent_limit=2)

    assert payload["total_reviews"] == 4
    assert payload["pending_reviews"] == 2
    assert payload["approved_reviews"] == 1
    assert payload["rejected_reviews"] == 1
    assert payload["pending_overdue_reviews"] == 1
    assert len(payload["recent_reviews"]) == 2


def test_ai_review_dashboard_service_scopes_counts_to_organization(monkeypatch):
    service = AIReviewService.__new__(AIReviewService)

    class FakeRepository:
        def get_reviews_by_project(self, project_id: str):
            if project_id == "project-a":
                return [
                    {"id": "r-1", "review_status": "PENDING", "created_at": "2026-01-01"},
                    {"id": "r-2", "review_status": "APPROVED", "created_at": "2026-01-02"},
                ]
            return []

    class FakeProjectRepository:
        def get_projects_by_organization(self, organization_id: str):
            if organization_id == "org-client":
                return [{"id": "project-a"}]
            return []

    service.repository = FakeRepository()
    service.tenant_scope = TenantScopeService()
    service.tenant_scope.project_repository = (
        FakeProjectRepository()
    )

    payload = service.get_review_dashboard(
        recent_limit=5,
        organization_id="org-client",
    )

    assert payload["total_reviews"] == 2
    assert payload["pending_reviews"] == 1
    assert payload["approved_reviews"] == 1
    assert payload["rejected_reviews"] == 0


def test_get_pending_reviews_scopes_to_organization(monkeypatch):
    service = AIReviewService.__new__(AIReviewService)

    class FakeRepository:
        def get_pending_reviews(self):
            return [
                {"id": "orphan", "review_status": "PENDING"},
            ]

        def get_reviews_by_project(self, project_id: str):
            if project_id == "project-a":
                return [
                    {
                        "id": "r-1",
                        "review_status": "PENDING",
                        "finding_id": "f-1",
                    },
                    {
                        "id": "r-2",
                        "review_status": "APPROVED",
                        "finding_id": "f-2",
                    },
                ]
            return []

    class FakeProjectRepository:
        def get_projects_by_organization(self, organization_id: str):
            if organization_id == "org-client":
                return [{"id": "project-a"}]
            return []

    service.repository = FakeRepository()
    service.tenant_scope = TenantScopeService()
    service.tenant_scope.project_repository = (
        FakeProjectRepository()
    )
    service.tenant_scope.resolve_project_id_for_finding = (
        lambda finding_id: (
            "project-a"
            if finding_id in {"f-1", "f-2"}
            else None
        )
    )

    scoped = service.get_pending_reviews(
        organization_id="org-client",
    )
    global_pending = service.get_pending_reviews()

    assert [review["id"] for review in scoped] == ["r-1"]
    assert [review["id"] for review in global_pending] == ["orphan"]


def test_pending_reviews_endpoint_scopes_to_authenticated_org(monkeypatch):
    class FakeReviewService:
        def get_pending_reviews(
            self,
            organization_id: str | None = None,
        ):
            assert organization_id == "org-1"
            return [{"id": "r-1", "review_status": "PENDING"}]

    monkeypatch.setattr(deps, "ai_review_service", FakeReviewService())
    client = TestClient(app)

    response = client.get(
        "/reviews/pending",
        headers=_auth_headers(),
    )

    assert response.status_code == 200
    assert response.json() == [{"id": "r-1", "review_status": "PENDING"}]


def test_ai_review_dashboard_endpoint_returns_payload(monkeypatch):
    class FakeReviewService:
        def get_review_dashboard(
            self,
            recent_limit: int = 20,
            *,
            organization_id: str | None = None,
        ):
            return {
                "total_reviews": 3,
                "pending_reviews": 1,
                "approved_reviews": 2,
                "rejected_reviews": 0,
                "pending_overdue_reviews": 0,
                "recent_reviews": [{"id": "ai-1"}],
                "recent_limit_used": recent_limit,
            }

    monkeypatch.setattr(deps, "ai_review_service", FakeReviewService())
    client = TestClient(app)

    response = client.get(
        "/reviews/dashboard",
        params={"limit": 5},
        headers=_auth_headers(),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["total_reviews"] == 3
    assert payload["pending_reviews"] == 1
    assert payload["recent_limit_used"] == 5


def test_assign_reviewer_endpoint_returns_assignment(monkeypatch):
    class FakeReviewService:
        def assign_reviewer(self, interpretation_id: str, reviewer_id: str):
            return {
                "id": interpretation_id,
                "assigned_reviewer": reviewer_id,
            }

    monkeypatch.setattr(deps, "ai_review_service", FakeReviewService())
    client = TestClient(app)

    response = client.post(
        "/reviews/ai-1/assign",
        json={"reviewer_id": "reviewer-2"},
        headers=_auth_headers(),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == "ai-1"
    assert payload["assigned_reviewer"] == "reviewer-2"


def test_assign_reviewer_endpoint_returns_404(monkeypatch):
    class FakeReviewService:
        def assign_reviewer(self, interpretation_id: str, reviewer_id: str):
            return None

    monkeypatch.setattr(deps, "ai_review_service", FakeReviewService())
    client = TestClient(app)

    response = client.post(
        "/reviews/missing/assign",
        json={"reviewer_id": "reviewer-2"},
        headers=_auth_headers(),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Review not found"


def test_ai_review_sla_service_tracks_breaches():
    service = AIReviewService.__new__(AIReviewService)

    old_pending = (
        datetime
        .now(UTC) - timedelta(hours=72)
    ).isoformat()

    fresh_pending = (
        datetime
        .now(UTC) - timedelta(hours=2)
    ).isoformat()

    class FakeRepository:
        def get_pending_reviews(self):
            return [
                {"id": "ai-1", "review_status": "PENDING", "created_at": old_pending},
                {"id": "ai-2", "review_status": "PENDING", "created_at": fresh_pending},
            ]

    service.repository = FakeRepository()

    payload = service.get_review_sla_tracking(target_hours=48)

    assert payload["total_pending_reviews"] == 2
    assert payload["within_sla_reviews"] == 1
    assert payload["breached_reviews"] == 1
    assert payload["breach_rate"] == 50.0
    assert payload["breached_review_ids"] == ["ai-1"]


def test_ai_review_sla_endpoint_returns_payload(monkeypatch):
    class FakeReviewService:
        def get_review_sla_tracking(self, target_hours: int = 48):
            return {
                "target_hours": target_hours,
                "total_pending_reviews": 2,
                "within_sla_reviews": 1,
                "breached_reviews": 1,
                "breach_rate": 50.0,
                "breached_review_ids": ["ai-1"],
            }

    monkeypatch.setattr(deps, "ai_review_service", FakeReviewService())
    client = TestClient(app)

    response = client.get(
        "/reviews/sla",
        params={"target_hours": 24},
        headers=_auth_headers(),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["target_hours"] == 24
    assert payload["breached_reviews"] == 1


def test_ai_review_confidence_service_returns_score():
    service = AIReviewService.__new__(AIReviewService)

    class FakeRepository:
        def get_review_by_id(self, interpretation_id: str):
            return {
                "id": interpretation_id,
                "model_name": "gpt-5.5",
                "recommended_action": "Review the schedule impact and prepare mitigation plan",
                "business_impact": "Potential delay can affect downstream milestones and revenue targets",
                "raw_response": '{"business_impact":"Delay","recommended_action":"Mitigation"}',
            }

    service.repository = FakeRepository()

    payload = service.get_review_confidence("ai-1")

    assert payload is not None
    assert payload["interpretation_id"] == "ai-1"
    assert payload["confidence_score"] >= 70
    assert payload["confidence_level"] in {"HIGH", "VERY_HIGH"}
    assert payload["factors"]["has_structured_raw_response"] is True


def test_ai_review_confidence_endpoint_returns_payload(monkeypatch):
    class FakeReviewService:
        def get_review_confidence(self, interpretation_id: str):
            return {
                "interpretation_id": interpretation_id,
                "confidence_score": 76,
                "confidence_level": "HIGH",
                "factors": {"model_name": "gpt-5.5"},
            }

    monkeypatch.setattr(deps, "ai_review_service", FakeReviewService())
    client = TestClient(app)

    response = client.get(
        "/reviews/ai-1/confidence",
        headers=_auth_headers(),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["confidence_score"] == 76
    assert payload["confidence_level"] == "HIGH"


def test_ai_review_confidence_endpoint_returns_404(monkeypatch):
    class FakeReviewService:
        def get_review_confidence(self, interpretation_id: str):
            return None

    monkeypatch.setattr(deps, "ai_review_service", FakeReviewService())
    client = TestClient(app)

    response = client.get(
        "/reviews/missing/confidence",
        headers=_auth_headers(),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Review not found"


def test_human_override_endpoint_returns_payload(monkeypatch):
    class FakeReviewService:
        def apply_human_override(
            self,
            interpretation_id: str,
            overridden_by: str,
            override_reason: str,
        ):
            return {
                "id": interpretation_id,
                "review_status": "OVERRIDDEN",
                "overridden_by": overridden_by,
                "override_reason": override_reason,
            }

    monkeypatch.setattr(deps, "ai_review_service", FakeReviewService())
    client = TestClient(app)

    response = client.post(
        "/reviews/ai-1/override",
        json={
            "overridden_by": "team-lead",
            "override_reason": "Manual investigation disproved AI finding",
        },
        headers=_auth_headers(),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["review_status"] == "OVERRIDDEN"
    assert payload["overridden_by"] == "team-lead"


def test_human_override_endpoint_returns_404(monkeypatch):
    class FakeReviewService:
        def apply_human_override(
            self,
            interpretation_id: str,
            overridden_by: str,
            override_reason: str,
        ):
            return None

    monkeypatch.setattr(deps, "ai_review_service", FakeReviewService())
    client = TestClient(app)

    response = client.post(
        "/reviews/missing/override",
        json={
            "overridden_by": "team-lead",
            "override_reason": "No review record",
        },
        headers=_auth_headers(),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Review not found"


def test_review_analytics_service_aggregates_metrics():
    service = AIReviewService.__new__(AIReviewService)

    class FakeRepository:
        def get_all_reviews(self):
            return [
                {
                    "id": "ai-1",
                    "review_status": "APPROVED",
                    "reviewed_by": "rev-a",
                    "model_name": "gpt-5.5",
                    "created_at": "2026-01-01T00:00:00+00:00",
                    "reviewed_at": "2026-01-01T04:00:00+00:00",
                },
                {
                    "id": "ai-2",
                    "review_status": "PENDING",
                    "assigned_reviewer": "rev-b",
                    "model_name": "gpt-5.5",
                    "created_at": "2026-01-02T00:00:00+00:00",
                },
                {
                    "id": "ai-3",
                    "review_status": "OVERRIDDEN",
                    "reviewed_by": "rev-a",
                    "model_name": "claude",
                    "created_at": "2026-01-03T00:00:00+00:00",
                    "reviewed_at": "2026-01-03T03:00:00+00:00",
                },
            ]

        def get_review_by_id(self, interpretation_id: str):
            by_id = {
                "ai-1": {
                    "id": "ai-1",
                    "model_name": "gpt-5.5",
                    "recommended_action": "Detailed action plan for high-risk finding",
                    "business_impact": "Material impact on delivery and budget",
                    "raw_response": '{"a":1}',
                },
                "ai-2": {
                    "id": "ai-2",
                    "model_name": "gpt-5.5",
                    "recommended_action": "Short note",
                    "business_impact": "Minor issue",
                    "raw_response": "plain",
                },
                "ai-3": {
                    "id": "ai-3",
                    "model_name": "claude",
                    "recommended_action": "",
                    "business_impact": "",
                    "raw_response": "",
                },
            }
            return by_id.get(interpretation_id)

    service.repository = FakeRepository()
    payload = service.get_review_analytics()

    assert payload["total_reviews"] == 3
    assert payload["status_breakdown"]["APPROVED"] == 1
    assert payload["status_breakdown"]["PENDING"] == 1
    assert payload["reviewer_breakdown"]["rev-a"] == 2
    assert payload["model_breakdown"]["gpt-5.5"] == 2
    assert payload["completed_review_cycles"] == 2
    assert payload["avg_approval_cycle_hours"] == 3.5


def test_review_analytics_endpoint_returns_payload(monkeypatch):
    class FakeReviewService:
        def get_review_analytics(self):
            return {
                "total_reviews": 6,
                "status_breakdown": {"PENDING": 2, "APPROVED": 4},
                "reviewer_breakdown": {"rev-a": 4},
                "model_breakdown": {"gpt-5.5": 6},
                "confidence_bucket_breakdown": {"low": 1, "medium": 1, "high": 4},
                "avg_approval_cycle_hours": 2.25,
                "completed_review_cycles": 4,
            }

    monkeypatch.setattr(deps, "ai_review_service", FakeReviewService())
    client = TestClient(app)

    response = client.get(
        "/reviews/analytics",
        headers=_auth_headers(),
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["total_reviews"] == 6
    assert payload["avg_approval_cycle_hours"] == 2.25


def test_review_explainability_service_returns_factors():
    service = AIReviewService.__new__(AIReviewService)

    class FakeRepository:
        def get_review_by_id(self, interpretation_id: str):
            return {
                "id": interpretation_id,
                "model_name": "gpt-5.5",
                "review_status": "PENDING",
                "business_impact": "Milestone slippage expected",
                "tenant_risk": "Medium",
                "recommended_action": "Escalate and recover timeline",
                "raw_response": '{"signals":["delay"],"confidence":0.82}',
            }

    service.repository = FakeRepository()

    payload = service.get_review_explainability("ai-5")

    assert payload is not None
    assert payload["interpretation_id"] == "ai-5"
    assert payload["model_name"] == "gpt-5.5"
    assert len(payload["explanation_factors"]) >= 3
    assert payload["explanation_version"] == "v1"


def test_review_explainability_endpoint_returns_payload(monkeypatch):
    class FakeReviewService:
        def get_review_explainability(self, interpretation_id: str):
            return {
                "interpretation_id": interpretation_id,
                "model_name": "gpt-5.5",
                "review_status": "PENDING",
                "explanation_factors": [{"factor": "business_impact"}],
                "explanation_version": "v1",
            }

    monkeypatch.setattr(deps, "ai_review_service", FakeReviewService())
    client = TestClient(app)

    response = client.get(
        "/reviews/ai-10/explainability",
        headers=_auth_headers(),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["interpretation_id"] == "ai-10"
    assert payload["explanation_version"] == "v1"


def test_review_explainability_endpoint_returns_404(monkeypatch):
    class FakeReviewService:
        def get_review_explainability(self, interpretation_id: str):
            return None

    monkeypatch.setattr(deps, "ai_review_service", FakeReviewService())
    client = TestClient(app)

    response = client.get(
        "/reviews/missing/explainability",
        headers=_auth_headers(),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Review not found"


def test_review_audit_logs_service_returns_events():
    service = AIReviewService.__new__(AIReviewService)

    class FakeRepository:
        def get_review_by_id(self, interpretation_id: str):
            return {
                "id": interpretation_id,
                "review_status": "APPROVED",
            }

    class FakeAuditRepository:
        def list_review_audit_logs(self, interpretation_id: str):
            return [
                {
                    "prompt": "REVIEW_ASSIGNED",
                    "response": "{'actor':'reviewer-1'}",
                    "created_at": "2026-01-01T00:00:00Z",
                },
                {
                    "prompt": "REVIEW_APPROVED",
                    "response": "{'actor':'reviewer-1'}",
                    "created_at": "2026-01-01T01:00:00Z",
                },
            ]

    service.repository = FakeRepository()
    service.audit_repository = FakeAuditRepository()

    payload = service.get_review_audit_logs("ai-20")

    assert payload is not None
    assert payload["interpretation_id"] == "ai-20"
    assert payload["total_events"] == 2
    assert payload["events"][0]["event_type"] == "REVIEW_ASSIGNED"


def test_review_audit_logs_endpoint_returns_payload(monkeypatch):
    class FakeReviewService:
        def get_review_audit_logs(self, interpretation_id: str):
            return {
                "interpretation_id": interpretation_id,
                "review_status": "APPROVED",
                "total_events": 1,
                "events": [{"event_type": "REVIEW_APPROVED"}],
            }

    monkeypatch.setattr(deps, "ai_review_service", FakeReviewService())
    client = TestClient(app)

    response = client.get(
        "/reviews/ai-21/audit-logs",
        headers=_auth_headers(),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["interpretation_id"] == "ai-21"
    assert payload["total_events"] == 1


def test_review_audit_logs_endpoint_returns_404(monkeypatch):
    class FakeReviewService:
        def get_review_audit_logs(self, interpretation_id: str):
            return None

    monkeypatch.setattr(deps, "ai_review_service", FakeReviewService())
    client = TestClient(app)

    response = client.get(
        "/reviews/missing/audit-logs",
        headers=_auth_headers(),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Review not found"


def test_review_escalation_logic_creates_action_when_required():
    service = AIReviewService.__new__(AIReviewService)

    class FakeReviewRepository:
        def get_review_by_id(self, interpretation_id: str):
            return {
                "id": interpretation_id,
                "review_status": "OVERRIDDEN",
                "recommended_action": "Escalate finding",
                "business_impact": "High impact",
                "created_at": "2026-01-01T00:00:00+00:00",
            }

    class FakeOperationalRepository:
        def get_open_action_by_interpretation_id(self, interpretation_id: str):
            return None

        def create_action(self, action):
            return {
                "id": "act-99",
                "interpretation_id": action.interpretation_id,
                "action_type": action.action_type,
                "status": action.status,
            }

    class FakeAuditRepository:
        def create_review_audit_log(self, interpretation_id: str, event_type: str, actor=None, details=None):
            return None

    service.repository = FakeReviewRepository()
    service.operational_repository = FakeOperationalRepository()
    service.audit_repository = FakeAuditRepository()

    def fake_confidence(_interpretation_id: str):
        return {"confidence_score": 42}

    service.get_review_confidence = fake_confidence

    payload = service.run_review_escalation_logic("ai-200")

    assert payload is not None
    assert payload["should_escalate"] is True
    assert "LOW_CONFIDENCE" in payload["reasons"]
    assert payload["created_action"]["id"] == "act-99"


def test_review_escalation_logic_skips_when_open_action_exists():
    service = AIReviewService.__new__(AIReviewService)

    class FakeReviewRepository:
        def get_review_by_id(self, interpretation_id: str):
            return {
                "id": interpretation_id,
                "review_status": "OVERRIDDEN",
                "recommended_action": "Escalate finding",
                "business_impact": "High impact",
                "created_at": "2026-01-01T00:00:00+00:00",
            }

    class FakeOperationalRepository:
        def get_open_action_by_interpretation_id(self, interpretation_id: str):
            return {"id": "act-existing", "status": "OPEN"}

        def create_action(self, action):
            raise AssertionError("Should not create duplicate action")

    service.repository = FakeReviewRepository()
    service.operational_repository = FakeOperationalRepository()
    service.audit_repository = None
    service.get_review_confidence = lambda _id: {"confidence_score": 30}

    payload = service.run_review_escalation_logic("ai-201")

    assert payload["should_escalate"] is True
    assert payload["created_action"] is None
    assert payload["existing_open_action"]["id"] == "act-existing"


def test_review_escalation_endpoint_returns_payload(monkeypatch):
    class FakeReviewService:
        def run_review_escalation_logic(self, interpretation_id: str, force: bool = False):
            return {
                "interpretation_id": interpretation_id,
                "should_escalate": True,
                "reasons": ["LOW_CONFIDENCE"],
                "created_action": {"id": "act-1"},
            }

    monkeypatch.setattr(deps, "ai_review_service", FakeReviewService())
    client = TestClient(app)

    response = client.post(
        "/reviews/ai-222/escalate",
        params={"force": "true"},
        headers=_auth_headers(),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["interpretation_id"] == "ai-222"
    assert payload["should_escalate"] is True


def test_review_escalation_endpoint_returns_404(monkeypatch):
    class FakeReviewService:
        def run_review_escalation_logic(self, interpretation_id: str, force: bool = False):
            return None

    monkeypatch.setattr(deps, "ai_review_service", FakeReviewService())
    client = TestClient(app)

    response = client.post(
        "/reviews/missing/escalate",
        headers=_auth_headers(),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Review not found"


def test_recommendation_review_endpoint_returns_payload(monkeypatch):
    class FakeReviewService:
        def review_ai_recommendation(
            self,
            interpretation_id: str,
            decision: str,
            reviewed_by: str,
            review_notes: str | None = None,
        ):
            return {
                "id": interpretation_id,
                "recommendation_review_status": decision.upper(),
                "recommendation_reviewed_by": reviewed_by,
                "recommendation_review_notes": review_notes,
            }

    monkeypatch.setattr(deps, "ai_review_service", FakeReviewService())
    client = TestClient(app)

    response = client.post(
        "/reviews/ai-333/recommendation/review",
        json={
            "reviewed_by": "rev-1",
            "decision": "approved",
            "review_notes": "Looks actionable",
        },
        headers=_auth_headers(),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["recommendation_review_status"] == "APPROVED"
    assert payload["recommendation_reviewed_by"] == "rev-1"


def test_recommendation_review_endpoint_rejects_invalid_decision(monkeypatch):
    class FakeReviewService:
        def review_ai_recommendation(
            self,
            interpretation_id: str,
            decision: str,
            reviewed_by: str,
            review_notes: str | None = None,
        ):
            raise ValueError("decision must be APPROVED or REJECTED")

    monkeypatch.setattr(deps, "ai_review_service", FakeReviewService())
    client = TestClient(app)

    response = client.post(
        "/reviews/ai-333/recommendation/review",
        json={
            "reviewed_by": "rev-1",
            "decision": "hold",
        },
        headers=_auth_headers(),
    )

    assert response.status_code == 422
    assert "decision must be APPROVED or REJECTED" in response.json()["detail"]


def test_review_comments_endpoints(monkeypatch):
    class FakeReviewService:
        def add_review_comment(self, interpretation_id: str, author: str, comment: str):
            return {
                "interpretation_id": interpretation_id,
                "author": author,
                "comment": comment,
            }

        def list_review_comments(self, interpretation_id: str):
            return {
                "interpretation_id": interpretation_id,
                "total_comments": 1,
                "comments": [
                    {
                        "author": "dana",
                        "comment": "Need verification",
                        "created_at": "2026-01-01T00:00:00Z",
                    }
                ],
            }

    monkeypatch.setattr(deps, "ai_review_service", FakeReviewService())
    client = TestClient(app)

    create_response = client.post(
        "/reviews/ai-500/comments",
        json={"author": "dana", "comment": "Need verification"},
        headers=_auth_headers(),
    )
    assert create_response.status_code == 200
    assert create_response.json()["author"] == "dana"

    list_response = client.get(
        "/reviews/ai-500/comments",
        headers=_auth_headers(),
    )
    assert list_response.status_code == 200
    assert list_response.json()["total_comments"] == 1


def test_review_comments_endpoints_return_404(monkeypatch):
    class FakeReviewService:
        def add_review_comment(self, interpretation_id: str, author: str, comment: str):
            return None

        def list_review_comments(self, interpretation_id: str):
            return None

    monkeypatch.setattr(deps, "ai_review_service", FakeReviewService())
    client = TestClient(app)

    create_response = client.post(
        "/reviews/missing/comments",
        json={"author": "dana", "comment": "Need verification"},
        headers=_auth_headers(),
    )
    assert create_response.status_code == 404

    list_response = client.get(
        "/reviews/missing/comments",
        headers=_auth_headers(),
    )
    assert list_response.status_code == 404


def test_review_notifications_endpoints(monkeypatch):
    class FakeReviewService:
        def send_review_notification(
            self,
            interpretation_id: str,
            recipient_id: str,
            message: str,
            channel: str = "IN_APP",
        ):
            return {
                "interpretation_id": interpretation_id,
                "recipient_id": recipient_id,
                "message": message,
                "channel": channel,
            }

        def list_review_notifications(self, interpretation_id: str):
            return {
                "interpretation_id": interpretation_id,
                "total_notifications": 1,
                "notifications": [
                    {"recipient_id": "user-1", "channel": "IN_APP", "message": "Review updated"}
                ],
            }

    monkeypatch.setattr(deps, "ai_review_service", FakeReviewService())
    client = TestClient(app)

    send_response = client.post(
        "/reviews/ai-700/notifications",
        json={"recipient_id": "user-1", "message": "Review updated", "channel": "IN_APP"},
        headers=_auth_headers(),
    )
    assert send_response.status_code == 200
    assert send_response.json()["recipient_id"] == "user-1"

    list_response = client.get(
        "/reviews/ai-700/notifications",
        headers=_auth_headers(),
    )
    assert list_response.status_code == 200
    assert list_response.json()["total_notifications"] == 1


def test_manual_approval_workflow_endpoint(monkeypatch):
    class FakeReviewService:
        def create_manual_approval_workflow(
            self,
            interpretation_id: str,
            requested_by: str,
            notes: str | None = None,
        ):
            return {
                "id": 123,
                "workflow_type": "REVIEW_MANUAL_APPROVAL",
                "payload": {
                    "interpretation_id": interpretation_id,
                    "requested_by": requested_by,
                    "notes": notes,
                },
                "status": "PENDING",
            }

    monkeypatch.setattr(deps, "ai_review_service", FakeReviewService())
    client = TestClient(app)

    response = client.post(
        "/reviews/ai-701/manual-approval",
        json={"requested_by": "manager-1", "notes": "Requires governance sign-off"},
        headers=_auth_headers(),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["workflow_type"] == "REVIEW_MANUAL_APPROVAL"
    assert payload["status"] == "PENDING"


def test_approve_review_endpoint_returns_payload(monkeypatch):
    class FakeReviewService:
        def approve_review(self, interpretation_id: str, reviewed_by: str, review_notes: str):
            return {
                "approved_interpretation": {
                    "id": interpretation_id,
                    "review_status": "APPROVED",
                },
                "created_action": {
                    "id": "act-1",
                    "title": "Follow up with contractor",
                },
            }

    class FakeNotificationService:
        def create_notification(self, **kwargs):
            return kwargs

    monkeypatch.setattr(deps, "ai_review_service", FakeReviewService())
    monkeypatch.setattr(deps, "notification_service", FakeNotificationService())
    client = TestClient(app)

    response = client.post(
        "/reviews/ai-900/approve",
        json={"reviewed_by": "manager-1", "review_notes": "Approved"},
        headers=_auth_headers(),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["created_action"]["id"] == "act-1"


def test_reject_review_endpoint_returns_payload(monkeypatch):
    class FakeReviewService:
        def reject_review(self, interpretation_id: str, reviewed_by: str, review_notes: str | None):
            return {
                "id": interpretation_id,
                "review_status": "REJECTED",
            }

    monkeypatch.setattr(deps, "ai_review_service", FakeReviewService())
    client = TestClient(app)

    response = client.post(
        "/reviews/ai-900/reject",
        json={"reviewed_by": "manager-1", "review_notes": "Rejected"},
        headers=_auth_headers(),
    )

    assert response.status_code == 200
    assert response.json()["review_status"] == "REJECTED"
