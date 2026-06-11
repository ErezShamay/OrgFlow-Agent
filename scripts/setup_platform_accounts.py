#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.auth.password_policy import validate_password
from app.auth.roles import ORG_ADMIN_ROLE, PLATFORM_ADMIN_ROLE
from app.db.supabase_client import supabase
from app.repositories.organization_repository import OrganizationRepository
from app.repositories.profile_repository import ProfileRepository
from app.repositories.tenant_manager_module_repository import (
    TenantManagerModuleRepository,
)
from app.services.tenant_manager_module_service import (
    TenantManagerModuleService,
)

PLATFORM_ADMIN_EMAIL = "erez.shamay.elayoai@gmail.com"
PLATFORM_ADMIN_NAME = "ארז שמאי - מנהל גלובלי"

DEMO_ORG_NAME = "חברה להדגמה"
DEMO_CLIENT_ADMIN_EMAIL = "erezshamay@gmail.com"
DEMO_CLIENT_ADMIN_NAME = "ארז שמאי"


def _find_profile_by_email(email: str) -> dict | None:
    response = (
        supabase
        .table("profiles")
        .select("*")
        .eq("email", email.strip().lower())
        .limit(1)
        .execute()
    )

    if not response.data:
        return None

    return response.data[0]


def _find_demo_organization() -> dict | None:
    response = (
        supabase
        .table("organizations")
        .select("*")
        .execute()
    )

    for organization in response.data or []:
        name = str(organization.get("organization_name") or "")
        if "הדגמ" in name or "דוגמ" in name:
            return organization

    return None


def _ensure_demo_organization(
    *,
    contact_email: str,
) -> dict:
    existing = _find_demo_organization()
    if existing:
        updated_name = existing.get("organization_name")
        if updated_name != DEMO_ORG_NAME:
            response = (
                supabase
                .table("organizations")
                .update({"organization_name": DEMO_ORG_NAME})
                .eq("id", existing["id"])
                .execute()
            )
            if response.data:
                return response.data[0]
        return existing

    repository = OrganizationRepository()
    return repository.create_organization(
        name=DEMO_ORG_NAME,
        contact_email=contact_email,
        owner_profile_id=None,
    )


def _find_auth_user_id_by_email(email: str) -> str | None:
    normalized_email = email.strip().lower()
    page = 1

    while True:
        response = supabase.auth.admin.list_users(
            page=page,
            per_page=200,
        )

        users = getattr(response, "users", None) or []

        for user in users:
            user_email = str(getattr(user, "email", "") or "").strip().lower()
            if user_email == normalized_email:
                return str(user.id)

        if len(users) < 200:
            break

        page += 1

    return None


def _ensure_auth_user_with_password(
    *,
    email: str,
    password: str,
    full_name: str,
) -> str:
    password_errors = validate_password(password)
    if password_errors:
        raise RuntimeError(
            "הסיסמה לא עומדת במדיניות: "
            + ", ".join(password_errors)
        )

    normalized_email = email.strip().lower()
    user_id = _find_auth_user_id_by_email(normalized_email)

    if user_id:
        supabase.auth.admin.update_user_by_id(
            user_id,
            {
                "password": password,
                "email_confirm": True,
                "user_metadata": {
                    "full_name": full_name,
                    "role": PLATFORM_ADMIN_ROLE,
                },
            },
        )
        return user_id

    created = supabase.auth.admin.create_user(
        {
            "email": normalized_email,
            "password": password,
            "email_confirm": True,
            "user_metadata": {
                "full_name": full_name,
                "role": PLATFORM_ADMIN_ROLE,
            },
        }
    )

    created_user = getattr(created, "user", None)
    if not created_user or not getattr(created_user, "id", None):
        raise RuntimeError(
            f"יצירת משתמש Auth נכשלה עבור {normalized_email}"
        )

    return str(created_user.id)


def _ensure_profile_role(
    *,
    email: str,
    full_name: str,
    role: str,
    organization_id: str | None,
    profile_id: str | None = None,
) -> dict:
    profile_repository = ProfileRepository()
    profile = _find_profile_by_email(email)

    if not profile and profile_id:
        profile = profile_repository.create_profile(
            {
                "id": profile_id,
                "email": email.strip().lower(),
                "full_name": full_name,
                "role": role,
                "organization_id": organization_id,
            }
        )

    if not profile:
        raise RuntimeError(
            f"לא נמצא משתמש עם המייל {email}. "
            "צור את המשתמש ב-Supabase Auth ואז הרץ שוב את הסקריפט."
        )

    updates = {
        "full_name": full_name,
        "role": role,
        "organization_id": organization_id,
    }

    updated = profile_repository.update_profile(
        str(profile["id"]),
        updates,
    )
    return updated or profile


def _clear_other_admins_in_demo_org(
    *,
    organization_id: str,
    keep_profile_id: str,
) -> None:
    profile_repository = ProfileRepository()
    profiles = profile_repository.list_profiles_by_organization(
        organization_id
    )

    for profile in profiles:
        profile_id = str(profile.get("id") or "")
        if profile_id == keep_profile_id:
            continue

        role = str(profile.get("role") or "").strip().upper()
        email = str(profile.get("email") or "").strip().lower()

        if role == ORG_ADMIN_ROLE:
            profile_repository.update_profile(
                profile_id,
                {"role": "VIEWER"},
            )
            print(
                "[WARN] הוסר תפקיד מנהל לקוח מ-"
                f"{email} בארגון ההדגמה"
            )

        if role == PLATFORM_ADMIN_ROLE and email != PLATFORM_ADMIN_EMAIL:
            profile_repository.update_profile(
                profile_id,
                {"role": "VIEWER"},
            )
            print(
                "[WARN] הוסר תפקיד מנהל גלובלי מ-"
                f"{email} בארגון ההדגמה"
            )


def _clear_foreign_organization_ownership(
    *,
    profile_id: str,
    organization_id: str,
) -> None:
    response = (
        supabase
        .table("organizations")
        .select("id, organization_name, owner_profile_id")
        .eq("owner_profile_id", profile_id)
        .execute()
    )

    for organization in response.data or []:
        org_id = str(organization["id"])
        if org_id == organization_id:
            continue

        (
            supabase
            .table("organizations")
            .update({"owner_profile_id": None})
            .eq("id", org_id)
            .execute()
        )
        print(
            "[OK] הוסר ownership מ-"
            f"{organization.get('organization_name')} ({org_id})"
        )


def _disable_tenant_manager_module(
    *,
    organization_id: str,
) -> dict:
    service = TenantManagerModuleService(
        module_repository=TenantManagerModuleRepository(),
        organization_repository=OrganizationRepository(),
    )

    if not service.is_storage_available():
        return {
            "organization_id": organization_id,
            "is_enabled": False,
            "storage_available": False,
        }

    return service.set_enabled(
        organization_id=organization_id,
        is_enabled=False,
        actor_profile_id="setup-platform-accounts",
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "מגדיר מנהל גלובלי (erez.shamay.elayoai@gmail.com) "
            "ומנהל לקוח להדגמה (erezshamay@gmail.com)."
        )
    )
    parser.add_argument(
        "--demo-contact-email",
        default=DEMO_CLIENT_ADMIN_EMAIL,
        help="אימייל ליצירת ארגון הדגמה אם לא קיים",
    )
    parser.add_argument(
        "--platform-admin-password",
        help="סיסמה למנהל הגלובלי (יוצר/מעדכן משתמש Auth)",
    )
    args = parser.parse_args()

    print("=== הגדרת חשבונות פלטפורמה ===")

    demo_organization = _ensure_demo_organization(
        contact_email=args.demo_contact_email.strip().lower(),
    )
    demo_organization_id = str(demo_organization["id"])
    print(
        f"[OK] ארגון הדגמה: {DEMO_ORG_NAME} ({demo_organization_id})"
    )

    platform_admin_profile_id = _find_auth_user_id_by_email(
        PLATFORM_ADMIN_EMAIL
    )

    if args.platform_admin_password:
        platform_admin_profile_id = _ensure_auth_user_with_password(
            email=PLATFORM_ADMIN_EMAIL,
            password=args.platform_admin_password,
            full_name=PLATFORM_ADMIN_NAME,
        )
        print(
            "[OK] Auth + סיסמה למנהל גלובלי: "
            f"{PLATFORM_ADMIN_EMAIL}"
        )
    elif not platform_admin_profile_id:
        print(
            "[WARN] מנהל גלובלי לא קיים ב-Auth. "
            "העבר --platform-admin-password כדי ליצור אותו."
        )

    if platform_admin_profile_id:
        platform_admin = _ensure_profile_role(
            email=PLATFORM_ADMIN_EMAIL,
            full_name=PLATFORM_ADMIN_NAME,
            role=PLATFORM_ADMIN_ROLE,
            organization_id=None,
            profile_id=platform_admin_profile_id,
        )
        print(
            "[OK] מנהל גלובלי: "
            f"{platform_admin.get('full_name')} "
            f"<{platform_admin.get('email')}> "
            f"({platform_admin.get('role')})"
        )

    demo_admin = _ensure_profile_role(
        email=DEMO_CLIENT_ADMIN_EMAIL,
        full_name=DEMO_CLIENT_ADMIN_NAME,
        role=ORG_ADMIN_ROLE,
        organization_id=demo_organization_id,
    )
    print(
        "[OK] מנהל לקוח להדגמה: "
        f"{demo_admin.get('full_name')} "
        f"<{demo_admin.get('email')}> "
        f"({demo_admin.get('role')})"
    )

    _clear_other_admins_in_demo_org(
        organization_id=demo_organization_id,
        keep_profile_id=str(demo_admin["id"]),
    )

    _clear_foreign_organization_ownership(
        profile_id=str(demo_admin["id"]),
        organization_id=demo_organization_id,
    )

    module_status = _disable_tenant_manager_module(
        organization_id=demo_organization_id,
    )
    print(
        "[OK] מודול מנהל דיירים בהדגמה: "
        f"{'כבוי' if not module_status.get('is_enabled') else 'פעיל'}"
    )

    print("\nההגדרה הושלמה.")
    print(
        f"- התחברות מנהל גלובלי: {PLATFORM_ADMIN_EMAIL}"
    )
    print(
        f"- התחברות מנהל לקוח להדגמה: {DEMO_CLIENT_ADMIN_EMAIL}"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"[ERROR] {error}", file=sys.stderr)
        raise SystemExit(1) from error
