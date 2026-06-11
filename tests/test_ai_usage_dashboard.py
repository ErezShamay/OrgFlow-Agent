from datetime import datetime, timezone

from app.services.ai_usage_dashboard_service import AIUsageDashboardService


class _FakeAILogRepository:
    def list_for_usage_summary(self, *, since=None, limit=20000):
        return [
            {
                "organization_id": "org-1",
                "project_id": None,
                "prompt_name": "finding_enrichment",
                "model_name": "gpt-4o-mini",
                "prompt_tokens": 1000,
                "completion_tokens": 500,
                "cache_hit": False,
                "success": True,
                "created_at": "2026-06-01T10:00:00+00:00",
            },
            {
                "organization_id": "org-2",
                "project_id": None,
                "prompt_name": "finding_enrichment",
                "model_name": "gpt-4o-mini",
                "prompt_tokens": 200,
                "completion_tokens": 100,
                "cache_hit": True,
                "success": True,
                "created_at": "2026-06-02T10:00:00+00:00",
            },
            {
                "organization_id": None,
                "project_id": "project-3",
                "prompt_name": "operational_summary",
                "model_name": "gpt-4o-mini",
                "prompt_tokens": 300,
                "completion_tokens": 150,
                "cache_hit": False,
                "success": True,
                "created_at": "2026-06-03T10:00:00+00:00",
            },
        ]


class _FakeOrganizationRepository:
    def get_all_organizations(self):
        return [
            {
                "id": "org-1",
                "organization_name": "קובי אורון ניהול פרויקטים בע״מ",
                "contact_email": "kobi@example.com",
            },
            {
                "id": "org-2",
                "organization_name": "חברה להדגמה",
                "contact_email": "demo@example.com",
            },
            {
                "id": "org-3",
                "organization_name": "לקוח ללא שימוש",
                "contact_email": "idle@example.com",
            },
        ]


class _FakeProjectRepository:
    def get_all_projects(self):
        return [
            {
                "id": "project-3",
                "organization_id": "org-3",
            },
        ]


def test_platform_ai_usage_dashboard_aggregates_per_organization():
    service = AIUsageDashboardService(
        ai_log_repository=_FakeAILogRepository(),
        organization_repository=_FakeOrganizationRepository(),
        project_repository=_FakeProjectRepository(),
    )

    dashboard = service.get_platform_dashboard(period_days=30)

    assert dashboard.period_days == 30
    assert dashboard.totals.total_calls == 3
    assert dashboard.totals.active_organizations == 3
    assert dashboard.totals.total_tokens == 2250
    assert "כלול במחיר הבסיסי" in dashboard.pricing_disclaimer

    by_id = {
        item.organization_id: item
        for item in dashboard.organizations
    }

    assert by_id["org-1"].total_tokens == 1500
    assert by_id["org-1"].estimated_cost_usd == 0.00045
    assert by_id["org-2"].cache_hits == 1
    assert by_id["org-3"].total_tokens == 450
    assert by_id["org-3"].usage_by_prompt[0].prompt_name == (
        "operational_summary"
    )


def test_platform_ai_usage_dashboard_sorts_by_cost_desc():
    service = AIUsageDashboardService(
        ai_log_repository=_FakeAILogRepository(),
        organization_repository=_FakeOrganizationRepository(),
        project_repository=_FakeProjectRepository(),
    )

    dashboard = service.get_platform_dashboard()

    assert dashboard.organizations[0].organization_id == "org-1"
    assert dashboard.organizations[-1].organization_id == "org-2"


def test_parse_timestamp_handles_iso_strings():
    parsed = AIUsageDashboardService._parse_timestamp(
        "2026-06-01T10:00:00+00:00"
    )

    assert parsed == datetime(2026, 6, 1, 10, 0, tzinfo=timezone.utc)
