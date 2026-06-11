from app.services.profile_service import ProfileService


class _FakeProfileRepository:
    def __init__(self, profile: dict | None) -> None:
        self.profile = profile
        self.supports_org_column = True

    def get_profile_by_id(self, profile_id: str) -> dict | None:
        return self.profile

    def supports_organization_column(self) -> bool:
        return self.supports_org_column


class _FakeOrganizationRepository:
    def get_all_organizations(self):
        return [
            {
                "id": "org-1",
                "organization_name": "קובי אורון ניהול פרויקטים בע״מ",
            },
            {
                "id": "org-demo",
                "organization_name": "חברה להדגמה",
            },
        ]

    def get_first_organization(self):
        return self.get_all_organizations()[0]


def test_platform_admin_without_org_uses_first_accessible_organization():
    service = ProfileService(
        profile_repository=_FakeProfileRepository({
            "id": "platform-1",
            "email": "erez.shamay.elayoai@gmail.com",
            "role": "PLATFORM_ADMIN",
        }),
        organization_repository=_FakeOrganizationRepository(),
    )

    org_id = service.ensure_organization_id("platform-1")

    assert org_id == "org-1"
