import os

import pytest
import app.dependencies as deps

os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("ORG_FLOW_LLM_MODE", "mock")


@pytest.fixture(autouse=True)
def freeze_quality_portfolio_now(monkeypatch):
    from tests.quality_issues_test_support import qc_now

    monkeypatch.setattr(
        "app.services.quality_issue_service._utc_now",
        qc_now,
    )


@pytest.fixture(autouse=True)
def patch_supervisor_profile_lookup_for_tests(monkeypatch):
    from tests.test_supervisor_project_scope import FakeProfileRepository

    class PermissiveProfileRepository(FakeProfileRepository):
        def __init__(self) -> None:
            super().__init__({})

        def get_profile_by_id(self, profile_id: str):
            if not profile_id:
                return None
            return {
                "id": profile_id,
                "email": "supervisor@test.com",
            }

    profile_repository = PermissiveProfileRepository()

    import app.main as main_module

    monkeypatch.setattr(
        deps.tenant_scope_service,
        "profile_repository",
        profile_repository,
    )
    monkeypatch.setattr(
        deps.quality_issue_service,
        "profile_repository",
        profile_repository,
    )
