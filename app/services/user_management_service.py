from __future__ import annotations

import logging
from typing import Any, Literal

from app.config.settings import settings
from app.db.supabase_client import supabase
from supabase_auth.errors import AuthApiError

from app.exceptions.exceptions import (
    ConfigurationError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
    ValidationError,
)
from app.lib.email_validation import require_valid_email
from app.auth.roles import (
    ORG_ADMIN_ROLE,
    PLATFORM_ADMIN_ROLE,
    RESIDENT_ROLE,
    can_assign_role,
    can_invite_resident,
    is_org_admin,
    is_platform_admin,
    ORG_SCOPED_INVITE_ROLES,
)
from app.auth.password_policy import validate_password
from app.repositories.organization_repository import OrganizationRepository
from app.repositories.profile_repository import ProfileRepository
from app.schemas.user_management import ALL_ORGANIZATIONS_SCOPE
from app.services.user_invite_email_service import UserInviteEmailService

logger = logging.getLogger(__name__)

AccountStatus = Literal["pending", "active"]


class UserManagementService:
    def __init__(
        self,
        profile_repository: ProfileRepository | None = None,
        organization_repository: OrganizationRepository | None = None,
        invite_email_service: UserInviteEmailService | None = None,
    ) -> None:
        self.profile_repository = profile_repository or ProfileRepository()
        self.organization_repository = (
            organization_repository or OrganizationRepository()
        )
        self.invite_email_service = invite_email_service or UserInviteEmailService()
        self.auth_client = supabase

    def list_users(
        self,
        organization_id: str,
        *,
        actor_role: str | None = None,
    ) -> dict:
        if (
            organization_id == ALL_ORGANIZATIONS_SCOPE
            and is_platform_admin(actor_role)
        ):
            return self.list_all_users()

        if not organization_id.strip():
            raise ValidationError(
                message="organization_id is required"
            )
        profiles = self.profile_repository.list_profiles_by_organization(
            organization_id
        )

        users = [
            {
                **profile,
                "account_status": self._resolve_account_status(
                    str(profile.get("id") or "")
                ),
            }
            for profile in profiles
        ]

        return {
            "users": users,
            "total": len(users),
        }

    def list_all_users(self) -> dict:
        profiles = self.profile_repository.list_all_profiles()
        org_names = self._organization_name_lookup()

        users = []
        for profile in profiles:
            org_id = ProfileRepository.extract_organization_id(profile)
            users.append(
                {
                    **profile,
                    "organization_id": org_id or None,
                    "organization_name": (
                        org_names.get(org_id)
                        if org_id
                        else None
                    ),
                    "account_status": self._resolve_account_status(
                        str(profile.get("id") or "")
                    ),
                }
            )

        return {
            "users": users,
            "total": len(users),
        }

    def update_user(
        self,
        *,
        organization_id: str,
        profile_id: str,
        actor_user_id: str,
        actor_role: str,
        full_name: str | None = None,
        role: str | None = None,
    ) -> dict:
        profile = self._get_profile_in_org(
            organization_id=organization_id,
            profile_id=profile_id,
        )

        updates: dict[str, str] = {}

        if full_name is not None:
            normalized_name = full_name.strip()
            if not normalized_name:
                raise ValidationError(message="Full name is required")
            updates["full_name"] = normalized_name

        if role is not None:
            normalized_role = role.strip().upper()
            current_role = str(profile.get("role") or "").strip().upper()

            if normalized_role == PLATFORM_ADMIN_ROLE:
                raise ForbiddenError(
                    message=(
                        "Global admin role cannot be assigned via user management"
                    ),
                )

            if not can_assign_role(
                actor_role=actor_role,
                target_role=normalized_role,
            ):
                raise ValidationError(
                    message="Invalid role for this update",
                )

            if (
                normalized_role == ORG_ADMIN_ROLE
                and current_role != ORG_ADMIN_ROLE
            ):
                existing_admin_count = (
                    self.profile_repository.count_profiles_with_role(
                        organization_id,
                        ORG_ADMIN_ROLE,
                    )
                )
                if existing_admin_count > 0:
                    raise ConflictError(
                        message=(
                            "ללקוח כבר יש מנהל לקוח. "
                            "מותר מנהל לקוח אחד בלבד לכל ארגון."
                        ),
                    )

            updates["role"] = normalized_role

        if not updates:
            raise ValidationError(message="No updates provided")

        updated = self.profile_repository.update_profile(
            profile_id,
            updates,
        )

        if not updated:
            raise NotFoundError(
                message="User not found",
                resource_type="profile",
                resource_id=profile_id,
            )

        logger.info(
            "User updated",
            extra={
                "event": "audit.user_update",
                "actor_user_id": actor_user_id,
                "profile_id": profile_id,
                "organization_id": organization_id,
                "fields": sorted(updates.keys()),
            },
        )

        return {
            "user": {
                **updated,
                "account_status": self._resolve_account_status(profile_id),
            },
        }

    def set_password(
        self,
        *,
        organization_id: str,
        profile_id: str,
        password: str,
        actor_user_id: str,
    ) -> dict:
        profile = self._get_profile_in_org(
            organization_id=organization_id,
            profile_id=profile_id,
        )

        password_errors = validate_password(password)
        if password_errors:
            raise ValidationError(
                message="Password does not meet policy requirements",
                details={"errors": password_errors},
            )

        try:
            self.auth_client.auth.admin.update_user_by_id(
                profile_id,
                {
                    "password": password,
                    "email_confirm": True,
                },
            )
        except AuthApiError as error:
            raise self._auth_admin_error(error) from error
        except Exception as error:
            raise ValidationError(
                message="Failed to set password",
                details={"error": str(error)},
            ) from error

        logger.info(
            "User password set by admin",
            extra={
                "event": "audit.user_password_set",
                "actor_user_id": actor_user_id,
                "profile_id": profile_id,
                "organization_id": organization_id,
                "target_email": profile.get("email"),
            },
        )

        return {
            "profile_id": profile_id,
            "status": "password_updated",
        }

    def invite_user(
        self,
        *,
        organization_id: str,
        email: str,
        full_name: str,
        role: str,
        invited_by: str,
        inviter_role: str,
        _allow_resident: bool = False,
    ) -> dict:
        normalized_email = email.strip().lower()
        normalized_role = role.strip().upper()
        normalized_name = full_name.strip()

        self._validate_email(normalized_email)

        if not can_assign_role(
            actor_role=inviter_role,
            target_role=normalized_role,
        ):
            raise ValidationError(
                message="Invalid role for this invitation",
                details={
                    "allowed_roles": list(
                        self._allowed_roles_for_inviter(
                            inviter_role
                        )
                    ),
                },
            )

        if normalized_role == PLATFORM_ADMIN_ROLE:
            raise ForbiddenError(
                message=(
                    "Global admin accounts cannot be created via invitation"
                ),
            )

        if normalized_role == RESIDENT_ROLE and not _allow_resident:
            raise ValidationError(
                message=(
                    "חשבונות דיירים נוצרים דרך מנהל הדיירים בלבד"
                ),
            )

        if not normalized_name:
            raise ValidationError(message="Full name is required")

        if normalized_role == ORG_ADMIN_ROLE:
            existing_admin_count = (
                self.profile_repository.count_profiles_with_role(
                    organization_id,
                    ORG_ADMIN_ROLE,
                )
            )
            if existing_admin_count > 0:
                raise ConflictError(
                    message=(
                        "ללקוח כבר יש מנהל לקוח. "
                        "מותר מנהל לקוח אחד בלבד לכל ארגון."
                    ),
                    details={
                        "organization_id": organization_id,
                        "existing_admin_count": existing_admin_count,
                    },
                )

        existing_profile = (
            self.profile_repository
            .get_profile_by_email_in_organization(
                organization_id,
                normalized_email,
            )
        )
        if existing_profile:
            raise ConflictError(
                message="A user with this email already exists in the organization",
                details={"email": normalized_email},
            )

        redirect_to = self._password_setup_redirect()
        metadata = {
            "full_name": normalized_name,
            "role": normalized_role,
            "organization_id": organization_id,
        }

        invite_response = self._create_auth_link(
            link_type="invite",
            email=normalized_email,
            redirect_to=redirect_to,
            metadata=metadata,
        )

        user_id = self._extract_user_id(invite_response)
        invite_link = self._extract_action_link(invite_response)

        if not user_id:
            raise ValidationError(message="Failed to create invited user")

        self._confirm_auth_user_email(user_id)

        profile = self.profile_repository.create_profile(
            {
                "id": user_id,
                "email": normalized_email,
                "full_name": normalized_name,
                "role": normalized_role,
                "organization_id": organization_id,
            }
        )

        email_status, email_error = self._deliver_invite_email(
            to_email=normalized_email,
            full_name=normalized_name,
            invite_link=invite_link,
            redirect_to=redirect_to,
            resend=False,
        )

        logger.info(
            "User invited",
            extra={
                "event": "audit.user_invite",
                "invited_by": invited_by,
                "user_id": user_id,
                "organization_id": organization_id,
                "email_status": email_status,
            },
        )

        return {
            "user": profile,
            "profile_id": user_id,
            "invite_link": invite_link,
            "email_status": email_status,
            "email_error": email_error,
        }

    def invite_resident_user(
        self,
        *,
        organization_id: str,
        email: str,
        full_name: str,
        invited_by: str,
        inviter_role: str,
    ) -> dict:
        if not can_invite_resident(inviter_role):
            raise ValidationError(
                message="אין הרשאה להזמין דיירים",
            )

        return self.invite_user(
            organization_id=organization_id,
            email=email,
            full_name=full_name,
            role=RESIDENT_ROLE,
            invited_by=invited_by,
            inviter_role=inviter_role,
            _allow_resident=True,
        )

    def resend_invite(
        self,
        *,
        organization_id: str,
        profile_id: str,
        actor_user_id: str,
    ) -> dict:
        profile = self._get_profile_in_org(
            organization_id=organization_id,
            profile_id=profile_id,
        )
        account_status = self._resolve_account_status(profile_id)

        if account_status == "active":
            raise ValidationError(
                message="User already activated. Use password reset instead."
            )

        email = str(profile.get("email") or "").strip().lower()
        full_name = str(profile.get("full_name") or email).strip()
        redirect_to = self._password_setup_redirect()
        metadata = {
            "full_name": full_name,
            "role": str(profile.get("role") or "VIEWER"),
            "organization_id": organization_id,
        }

        invite_response = self._create_auth_link(
            link_type="invite",
            email=email,
            redirect_to=redirect_to,
            metadata=metadata,
        )
        invite_link = self._extract_action_link(invite_response)

        email_status, email_error = self._deliver_invite_email(
            to_email=email,
            full_name=full_name,
            invite_link=invite_link,
            redirect_to=redirect_to,
            resend=True,
        )

        logger.info(
            "User invite resent",
            extra={
                "event": "audit.user_invite_resend",
                "actor_user_id": actor_user_id,
                "profile_id": profile_id,
                "organization_id": organization_id,
                "email_status": email_status,
            },
        )

        return {
            "profile_id": profile_id,
            "email_status": email_status,
            "email_error": email_error,
        }

    def send_password_reset(
        self,
        *,
        organization_id: str,
        profile_id: str,
        actor_user_id: str,
    ) -> dict:
        profile = self._get_profile_in_org(
            organization_id=organization_id,
            profile_id=profile_id,
        )

        email = str(profile.get("email") or "").strip().lower()
        full_name = str(profile.get("full_name") or email).strip()
        redirect_to = self._password_setup_redirect()

        reset_response = self._create_auth_link(
            link_type="recovery",
            email=email,
            redirect_to=redirect_to,
        )
        reset_link = self._extract_action_link(reset_response)

        email_status = "SKIPPED"
        email_error = None

        if reset_link:
            try:
                self.invite_email_service.send_password_reset(
                    to_email=email,
                    full_name=full_name,
                    reset_link=reset_link,
                )
                email_status = "SENT"
            except Exception as error:
                email_error = str(error)
                logger.warning(
                    "Failed sending password reset email",
                    extra={
                        "event": "audit.user_password_reset_email_failed",
                        "email": email,
                        "error": email_error,
                    },
                )
        else:
            email_error = "Failed to generate password reset link"

        logger.info(
            "Password reset requested",
            extra={
                "event": "audit.user_password_reset",
                "actor_user_id": actor_user_id,
                "profile_id": profile_id,
                "organization_id": organization_id,
                "email_status": email_status,
            },
        )

        return {
            "profile_id": profile_id,
            "email_status": email_status,
            "email_error": email_error,
        }

    def delete_user(
        self,
        *,
        organization_id: str,
        profile_id: str,
        actor_user_id: str,
        actor_role: str,
    ) -> dict:
        if profile_id == actor_user_id:
            raise ForbiddenError(message="You cannot delete your own account")

        profile = self._get_profile_in_org(
            organization_id=organization_id,
            profile_id=profile_id,
        )

        target_role = str(profile.get("role") or "").strip().upper()

        if (
            is_platform_admin(target_role)
            and not is_platform_admin(actor_role)
        ):
            raise ForbiddenError(
                message="Only platform admins can remove platform admins"
            )

        try:
            self.auth_client.auth.admin.delete_user(profile_id)
        except Exception as error:
            logger.warning(
                "Failed deleting auth user",
                extra={
                    "event": "audit.user_delete_auth_failed",
                    "profile_id": profile_id,
                    "error": str(error),
                },
            )

        self.profile_repository.delete_profile(profile_id)

        logger.info(
            "User deleted",
            extra={
                "event": "audit.user_delete",
                "actor_user_id": actor_user_id,
                "profile_id": profile_id,
                "organization_id": organization_id,
            },
        )

        return {
            "status": "deleted",
            "profile_id": profile_id,
        }

    def _get_profile_in_org(
        self,
        *,
        organization_id: str,
        profile_id: str,
    ) -> dict:
        profile = self.profile_repository.get_profile_by_id(profile_id)

        if not profile:
            raise NotFoundError(
                message="User not found",
                resource_type="profile",
                resource_id=profile_id,
            )

        profile_org_id = ProfileRepository.extract_organization_id(
            profile
        )

        if not profile_org_id:
            raise ForbiddenError(
                message="User is not assigned to a customer organization"
            )

        if profile_org_id != organization_id:
            raise ForbiddenError(message="User belongs to a different organization")

        return profile

    def _organization_name_lookup(self) -> dict[str, str]:
        organizations = self.organization_repository.get_all_organizations()
        lookup: dict[str, str] = {}

        for organization in organizations:
            org_id = str(organization.get("id") or "").strip()
            if not org_id:
                continue

            name = str(
                organization.get("organization_name")
                or organization.get("name")
                or organization.get("contact_email")
                or org_id
            ).strip()
            lookup[org_id] = name

        return lookup

    def _resolve_account_status(
        self,
        profile_id: str,
    ) -> AccountStatus:
        if not profile_id:
            return "pending"

        auth_user = self._get_auth_user(profile_id)
        if not auth_user:
            return "pending"

        last_sign_in_at = auth_user.get("last_sign_in_at")
        if last_sign_in_at:
            return "active"

        return "pending"

    def _confirm_auth_user_email(self, profile_id: str) -> None:
        try:
            self.auth_client.auth.admin.update_user_by_id(
                profile_id,
                {"email_confirm": True},
            )
        except AuthApiError as error:
            raise self._auth_admin_error(error) from error
        except Exception as error:
            raise ValidationError(
                message="Failed to confirm user email",
                details={"error": str(error)},
            ) from error

    def _get_auth_user(
        self,
        profile_id: str,
    ) -> dict | None:
        try:
            response = self.auth_client.auth.admin.get_user_by_id(profile_id)
        except Exception:
            return None

        user = getattr(response, "user", None)

        if isinstance(user, dict):
            return user

        if user is not None:
            return {
                "id": getattr(user, "id", None),
                "email": getattr(user, "email", None),
                "last_sign_in_at": getattr(user, "last_sign_in_at", None),
            }

        if isinstance(response, dict):
            nested_user = response.get("user")
            if isinstance(nested_user, dict):
                return nested_user

        return None

    @staticmethod
    def _validate_email(email: str) -> None:
        try:
            require_valid_email(email)
        except ValueError as error:
            raise ValidationError(message="Invalid email address") from error

    @staticmethod
    def _allowed_roles_for_inviter(
        inviter_role: str,
    ) -> tuple[str, ...]:
        from app.auth.roles import inviteable_roles

        return inviteable_roles(inviter_role)

    @staticmethod
    def _validate_role(role: str) -> None:
        if role not in {
            *ORG_SCOPED_INVITE_ROLES,
            "PLATFORM_ADMIN",
        }:
            raise ValidationError(
                message="Invalid role",
            )

    @staticmethod
    def _password_setup_redirect() -> str:
        base = str(settings.FRONTEND_URL).rstrip("/")
        return f"{base}/auth/callback?next=/auth/set-password"

    def _create_auth_link(
        self,
        *,
        link_type: Literal["invite", "recovery"],
        email: str,
        redirect_to: str,
        metadata: dict[str, str] | None = None,
    ) -> Any:
        payload: dict[str, Any] = {
            "type": link_type,
            "email": email,
            "options": {
                "redirect_to": redirect_to,
            },
        }

        if metadata:
            payload["options"]["data"] = metadata

        try:
            return self.auth_client.auth.admin.generate_link(payload)
        except AuthApiError as error:
            raise self._auth_admin_error(error) from error

    @staticmethod
    def _auth_admin_error(error: AuthApiError) -> ConfigurationError:
        message = str(error).strip() or "Supabase auth admin request failed"
        if message.lower() == "user not allowed":
            return ConfigurationError(
                message=(
                    "Supabase rejected the invite: SUPABASE_KEY must be the "
                    "service_role secret (Project Settings → API), not the "
                    "anon/public key."
                ),
                config_key="SUPABASE_KEY",
            )
        return ConfigurationError(
            message=f"Supabase auth admin request failed: {message}",
            config_key="SUPABASE_KEY",
        )

    def _deliver_invite_email(
        self,
        *,
        to_email: str,
        full_name: str,
        invite_link: str | None,
        redirect_to: str,
        resend: bool,
    ) -> tuple[str, str | None]:
        email_status = "SKIPPED"
        email_error = None

        if invite_link:
            try:
                if resend:
                    self.invite_email_service.send_invite_reminder(
                        to_email=to_email,
                        full_name=full_name,
                        invite_link=invite_link,
                    )
                else:
                    self.invite_email_service.send_invite(
                        to_email=to_email,
                        full_name=full_name,
                        invite_link=invite_link,
                    )
                email_status = "SENT"
            except Exception as error:
                email_error = str(error)
                logger.warning(
                    "Failed sending invite email",
                    extra={
                        "event": "audit.user_invite_email_failed",
                        "email": to_email,
                        "error": email_error,
                    },
                )
        else:
            try:
                self.auth_client.auth.admin.invite_user_by_email(
                    to_email,
                    options={"redirect_to": redirect_to},
                )
                email_status = "SENT"
            except Exception as error:
                email_error = str(error)

        return email_status, email_error

    @staticmethod
    def _extract_user_id(response: Any) -> str | None:
        user = getattr(response, "user", None)

        if isinstance(user, dict):
            return str(user.get("id") or "").strip() or None

        if user is not None:
            user_id = getattr(user, "id", None)
            if user_id:
                return str(user_id).strip()

        if isinstance(response, dict):
            nested_user = response.get("user")
            if isinstance(nested_user, dict):
                return str(nested_user.get("id") or "").strip() or None

        return None

    @staticmethod
    def _extract_action_link(response: Any) -> str | None:
        properties = getattr(response, "properties", None)

        if isinstance(properties, dict):
            action_link = properties.get("action_link")
            if action_link:
                return str(action_link)

        if properties is not None:
            action_link = getattr(properties, "action_link", None)
            if action_link:
                return str(action_link)

        if isinstance(response, dict):
            nested_properties = response.get("properties")
            if isinstance(nested_properties, dict):
                action_link = nested_properties.get("action_link")
                if action_link:
                    return str(action_link)

        return None
