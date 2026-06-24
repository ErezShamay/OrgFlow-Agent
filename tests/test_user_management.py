from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.auth.password_policy import (
    PASSWORD_MIN_LENGTH,
    get_password_policy,
    validate_password,
)
from app.exceptions.exceptions import (
    ConflictError,
    ForbiddenError,
    ValidationError,
)
from app.services.user_management_service import UserManagementService


def test_password_policy_requires_standard_rules():
    policy = get_password_policy()

    assert policy["min_length"] == PASSWORD_MIN_LENGTH
    assert len(policy["rules"]) == 5


def test_validate_password_rejects_weak_password():
    errors = validate_password("abc")

    assert errors
    assert any("8" in error for error in errors)


def test_validate_password_accepts_strong_password():
    errors = validate_password("Secure1!")

    assert errors == []


def test_invite_user_rejects_duplicate_client_admin():
    service = UserManagementService(
        profile_repository=MagicMock(
            list_profiles_by_organization=MagicMock(return_value=[]),
            count_profiles_with_role=MagicMock(return_value=1),
        )
    )

    with pytest.raises(ConflictError):
        service.invite_user(
            organization_id="org-1",
            email="admin2@example.com",
            full_name="Second Admin",
            role="ADMIN",
            invited_by="platform-admin-1",
            inviter_role="PLATFORM_ADMIN",
        )


def test_allowed_roles_for_admin_include_contractor():
    roles = UserManagementService._allowed_roles_for_inviter("ADMIN")

    assert "CONTRACTOR" in roles
    assert "DEVELOPER" in roles


def test_invite_user_rejects_invalid_email():
    service = UserManagementService(
        profile_repository=MagicMock(
            list_profiles_by_organization=MagicMock(return_value=[]),
        )
    )

    with pytest.raises(ValidationError):
        service.invite_user(
            organization_id="org-1",
            email="not-an-email",
            full_name="Test User",
            role="VIEWER",
            invited_by="admin-1",
            inviter_role="ADMIN",
        )


def test_invite_user_rejects_invalid_role():
    service = UserManagementService(
        profile_repository=MagicMock(
            list_profiles_by_organization=MagicMock(return_value=[]),
        )
    )

    with pytest.raises(ValidationError):
        service.invite_user(
            organization_id="org-1",
            email="user@example.com",
            full_name="Test User",
            role="SUPERUSER",
            invited_by="admin-1",
            inviter_role="ADMIN",
        )


def test_invite_user_rejects_duplicate_email():
    service = UserManagementService(
        profile_repository=MagicMock(
            list_profiles_by_organization=MagicMock(
                return_value=[{"email": "user@example.com"}]
            ),
        )
    )

    with pytest.raises(ConflictError):
        service.invite_user(
            organization_id="org-1",
            email="user@example.com",
            full_name="Test User",
            role="VIEWER",
            invited_by="admin-1",
            inviter_role="ADMIN",
        )


def test_delete_user_blocks_self_delete():
    service = UserManagementService(
        profile_repository=MagicMock(
            get_profile_by_id=MagicMock(
                return_value={
                    "id": "admin-1",
                    "organization_id": "org-1",
                }
            ),
        )
    )

    with pytest.raises(ForbiddenError):
        service.delete_user(
            organization_id="org-1",
            profile_id="admin-1",
            actor_user_id="admin-1",
            actor_role="ADMIN",
        )


def test_resend_invite_blocks_active_user():
    service = UserManagementService(
        profile_repository=MagicMock(
            get_profile_by_id=MagicMock(
                return_value={
                    "id": "user-1",
                    "email": "user@example.com",
                    "full_name": "Test User",
                    "role": "VIEWER",
                    "organization_id": "org-1",
                }
            ),
        )
    )
    service._get_auth_user = MagicMock(
        return_value={"last_sign_in_at": "2026-01-01T00:00:00Z"}
    )

    with pytest.raises(ValidationError):
        service.resend_invite(
            organization_id="org-1",
            profile_id="user-1",
            actor_user_id="admin-1",
        )


def test_resolve_account_status_pending_without_sign_in():
    service = UserManagementService()
    service._get_auth_user = MagicMock(
        return_value={"last_sign_in_at": None}
    )

    assert service._resolve_account_status("user-1") == "pending"


def test_resolve_account_status_active_after_sign_in():
    service = UserManagementService()
    service._get_auth_user = MagicMock(
        return_value={"last_sign_in_at": "2026-01-01T00:00:00Z"}
    )

    assert service._resolve_account_status("user-1") == "active"


def test_list_users_requires_organization_for_non_global_scope():
    service = UserManagementService()

    with pytest.raises(ValidationError):
        service.list_users("")


def test_update_user_rejects_platform_admin_role():
    service = UserManagementService(
        profile_repository=MagicMock(
            get_profile_by_id=MagicMock(
                return_value={
                    "id": "user-1",
                    "role": "VIEWER",
                    "organization_id": "org-1",
                }
            ),
        )
    )

    with pytest.raises(ForbiddenError):
        service.update_user(
            organization_id="org-1",
            profile_id="user-1",
            actor_user_id="admin-1",
            actor_role="PLATFORM_ADMIN",
            role="PLATFORM_ADMIN",
        )


def test_set_password_validates_policy():
    service = UserManagementService(
        profile_repository=MagicMock(
            get_profile_by_id=MagicMock(
                return_value={
                    "id": "user-1",
                    "email": "user@example.com",
                    "organization_id": "org-1",
                }
            ),
        )
    )

    with pytest.raises(ValidationError):
        service.set_password(
            organization_id="org-1",
            profile_id="user-1",
            password="weak",
            actor_user_id="admin-1",
        )


def test_set_password_confirms_email_in_supabase():
    auth_admin = MagicMock()
    service = UserManagementService(
        profile_repository=MagicMock(
            get_profile_by_id=MagicMock(
                return_value={
                    "id": "user-1",
                    "email": "user@example.com",
                    "organization_id": "org-1",
                }
            ),
        )
    )
    service.auth_client = MagicMock(auth=MagicMock(admin=auth_admin))

    service.set_password(
        organization_id="org-1",
        profile_id="user-1",
        password="Secure1!",
        actor_user_id="admin-1",
    )

    auth_admin.update_user_by_id.assert_called_once_with(
        "user-1",
        {
            "password": "Secure1!",
            "email_confirm": True,
        },
    )

