#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import uuid
from datetime import datetime, timezone

import httpx

from app.auth.jwt_service import JWTService
from app.auth.roles import CLIENT_ADMIN_INVITE_ROLES, ORG_ADMIN_ROLE, inviteable_roles
from app.db.supabase_client import supabase
from app.repositories.profile_repository import ProfileRepository
from app.services.user_management_service import UserManagementService


def _headers(*, user_id: str, org_id: str, role: str) -> dict[str, str]:
    token = JWTService().issue_access_token(
        user_id=user_id,
        org_id=org_id,
        role=role,
        token_id=f"verify-{uuid.uuid4()}",
    )
    return {
        "Authorization": f"Bearer {token}",
        "X-Organization-ID": org_id,
        "Content-Type": "application/json",
    }


def _pick_organization() -> dict:
    response = (
        supabase.table("organizations")
        .select("id, organization_name, owner_profile_id")
        .order("created_at")
        .limit(1)
        .execute()
    )
    if not response.data:
        raise RuntimeError("No organizations found in Supabase")
    return response.data[0]


def _print_step(name: str, ok: bool, detail: str = "") -> None:
    status = "PASS" if ok else "FAIL"
    line = f"[{status}] {name}"
    if detail:
        line += f" - {detail}"
    print(line)


def main() -> int:
    api_base = "http://127.0.0.1:8000"
    failures = 0
    created_project_id: str | None = None

    print("=== OrgFlow verification ===\n")

    try:
        httpx.get(f"{api_base}/healthcheck", timeout=5.0).raise_for_status()
        _print_step("Backend healthcheck", True, api_base)
    except Exception as error:
        _print_step("Backend healthcheck", False, str(error))
        return 1

    organization = _pick_organization()
    org_id = str(organization["id"])
    org_name = organization.get("organization_name") or org_id
    _print_step("Load organization", True, org_name)

    profile_repo = ProfileRepository()
    profiles = profile_repo.list_profiles_by_organization(org_id)
    admin_profiles = [
        profile
        for profile in profiles
        if str(profile.get("role") or "").upper() == ORG_ADMIN_ROLE
    ]
    admin_count_ok = len(admin_profiles) <= 1
    _print_step(
        "Single client admin in organization",
        admin_count_ok,
        f"{len(admin_profiles)} admin profile(s)",
    )
    if not admin_count_ok:
        failures += 1

    actor_id = (
        str(admin_profiles[0]["id"])
        if admin_profiles
        else str(profiles[0]["id"]) if profiles else "verify-user"
    )

    suffix = datetime.now(timezone.utc).strftime("%H%M%S")
    project_payload = {
        "project_name": f"בדיקת מערכת {suffix}",
        "developer_name": "יזם בדיקה",
        "contractor_name": "קבלן בדיקה",
        "lawyer_name": "עו״ד בדיקה",
        "supervisor_name": "מפקח בדיקה",
        "supervisor_email": None,
        "organization_id": org_id,
        "owner_id": actor_id,
    }

    try:
        create_response = httpx.post(
            f"{api_base}/projects",
            headers=_headers(
                user_id=actor_id,
                org_id=org_id,
                role=ORG_ADMIN_ROLE,
            ),
            json=project_payload,
            timeout=15.0,
        )
        create_response.raise_for_status()
        created = create_response.json()
        created_project_id = str(created.get("id") or "")
        fields_ok = all(
            created.get(field) == project_payload[field]
            for field in (
                "project_name",
                "developer_name",
                "contractor_name",
                "lawyer_name",
                "supervisor_name",
            )
        )
        _print_step(
            "Create project with stakeholder fields",
            fields_ok,
            created_project_id or "no id returned",
        )
        if not fields_ok:
            failures += 1
            print(json.dumps(created, ensure_ascii=False, indent=2))
    except Exception as error:
        _print_step("Create project with stakeholder fields", False, str(error))
        failures += 1

    platform_roles = inviteable_roles("PLATFORM_ADMIN")
    client_roles = inviteable_roles(ORG_ADMIN_ROLE)
    roles_ok = (
        ORG_ADMIN_ROLE in platform_roles
        and "SUPERVISOR" in platform_roles
        and "VIEWER" in platform_roles
        and client_roles == CLIENT_ADMIN_INVITE_ROLES
        and ORG_ADMIN_ROLE not in client_roles
    )
    _print_step(
        "Role invitation policy",
        roles_ok,
        f"platform={platform_roles}, client={client_roles}",
    )
    if not roles_ok:
        failures += 1

    service = UserManagementService(profile_repository=profile_repo)
    duplicate_admin_blocked = False
    duplicate_admin_message = ""
    if len(admin_profiles) >= 1:
        try:
            service.invite_user(
                organization_id=org_id,
                email=f"duplicate-admin-{suffix}@example.com",
                full_name="Admin Duplicate Test",
                role=ORG_ADMIN_ROLE,
                invited_by=actor_id,
                inviter_role="PLATFORM_ADMIN",
            )
        except Exception as error:
            duplicate_admin_blocked = True
            duplicate_admin_message = str(error)

        _print_step(
            "Block second client admin invitation",
            duplicate_admin_blocked,
            duplicate_admin_message or "invitation unexpectedly succeeded",
        )
        if not duplicate_admin_blocked:
            failures += 1
    else:
        _print_step(
            "Block second client admin invitation",
            True,
            "skipped - no existing client admin in organization",
        )

    existing_projects = (
        supabase.table("projects")
        .select(
            "id, developer_name, contractor_name, lawyer_name"
        )
        .eq("organization_id", org_id)
        .limit(5)
        .execute()
    )
    backfill_ok = True
    backfill_detail = "no projects"
    if existing_projects.data:
        backfill_ok = all(
            all(
                str(project.get(field) or "").strip()
                for field in (
                    "developer_name",
                    "contractor_name",
                    "lawyer_name",
                )
            )
            for project in existing_projects.data
        )
        backfill_detail = (
            f"{len(existing_projects.data)} project(s) checked"
        )

    _print_step(
        "Existing projects have stakeholder values",
        backfill_ok,
        backfill_detail,
    )
    if not backfill_ok:
        failures += 1

    backfill_ok = True
    backfill_detail = "skipped"
    if created_project_id:
        project_row = (
            supabase.table("projects")
            .select(
                "developer_name, contractor_name, lawyer_name"
            )
            .eq("id", created_project_id)
            .limit(1)
            .execute()
        )
        if project_row.data:
            row = project_row.data[0]
            backfill_ok = all(
                str(row.get(field) or "").strip()
                for field in (
                    "developer_name",
                    "contractor_name",
                    "lawyer_name",
                )
            )
            backfill_detail = json.dumps(row, ensure_ascii=False)

    _print_step(
        "Project stakeholder fields persisted in DB",
        backfill_ok,
        backfill_detail,
    )
    if not backfill_ok:
        failures += 1

    if created_project_id:
        try:
            delete_response = httpx.delete(
                f"{api_base}/projects/{created_project_id}",
                headers=_headers(
                    user_id=actor_id,
                    org_id=org_id,
                    role=ORG_ADMIN_ROLE,
                ),
                timeout=15.0,
            )
            delete_response.raise_for_status()
            _print_step(
                "Cleanup test project",
                True,
                created_project_id,
            )
        except Exception as error:
            _print_step(
                "Cleanup test project",
                False,
                f"{created_project_id}: {error}",
            )

    print()
    if failures:
        print(f"Verification finished with {failures} failure(s).")
        return 1

    print("Verification finished successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
