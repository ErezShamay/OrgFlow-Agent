from app.repositories.profile_repository import (
    ProfileRepository
)


class ProfileService:

    def __init__(self):

        self.repository = (
            ProfileRepository()
        )

    def get_profile(
        self,
        profile_id: str,
    ):

        return (
            self.repository
            .get_profile_by_id(
                profile_id
            )
        )

    # ==========================================
    # ROLE HELPERS
    # ==========================================

    def is_admin(
        self,
        profile_id: str,
    ):

        profile = (
            self.get_profile(
                profile_id
            )
        )

        if not profile:

            return False

        return (
            profile["role"]
            == "ADMIN"
        )

    def is_manager(
        self,
        profile_id: str,
    ):

        profile = (
            self.get_profile(
                profile_id
            )
        )

        if not profile:

            return False

        return (
            profile["role"]
            in [
                "ADMIN",
                "MANAGER",
            ]
        )