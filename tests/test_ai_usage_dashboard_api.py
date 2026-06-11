from __future__ import annotations

from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.auth.jwt_service import JWTService
from app.main import app
from app.schemas.ai_usage import (
    OrganizationAIUsageSummary,
    PlatformAIUsageDashboard,
    PlatformAIUsageTotals,
)
from app.services.ai_usage_dashboard_service import (
    AIUsageDashboardService,
)


def _token(
    *,
    user_id: str = "admin-1",
    org_id: str = "org-1",
    role: str = "PLATFORM_ADMIN",
) -> str:
    return JWTService().issue_access_token(
        user_id=user_id,
        org_id=org_id,
        role=role,
        token_id="t-ai-usage",
    )


def _headers(token: str, org_id: str = "org-1") -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "X-Organization-ID": org_id,
    }


class FakeAIUsageDashboardService(AIUsageDashboardService):
    def get_platform_dashboard(self, *, period_days: int = 90):
        return PlatformAIUsageDashboard(
            period_days=period_days,
            generated_at=datetime(2026, 6, 11, tzinfo=timezone.utc),
            pricing_disclaimer="כלול במחיר הבסיסי",
            totals=PlatformAIUsageTotals(
                total_calls=2,
                active_organizations=1,
                estimated_cost_usd=0.01,
            ),
            organizations=[
                OrganizationAIUsageSummary(
                    organization_id="org-1",
                    organization_name="חברה להדגמה",
                    total_calls=2,
                    estimated_cost_usd=0.01,
                )
            ],
        )


def test_platform_admin_can_read_ai_usage_dashboard(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.main.ai_usage_dashboard_service",
        FakeAIUsageDashboardService(),
    )

    client = TestClient(app)
    response = client.get(
        "/admin/ai-usage?period_days=30",
        headers=_headers(_token()),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["period_days"] == 30
    assert payload["organizations"][0]["organization_name"] == "חברה להדגמה"


def test_org_admin_cannot_read_ai_usage_dashboard(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.main.ai_usage_dashboard_service",
        FakeAIUsageDashboardService(),
    )

    client = TestClient(app)
    response = client.get(
        "/admin/ai-usage",
        headers=_headers(
            _token(role="ADMIN", user_id="client-admin"),
        ),
    )

    assert response.status_code == 403
