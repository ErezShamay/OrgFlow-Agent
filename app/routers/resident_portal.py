"""Resident portal routes.

Extracted from app/main.py during the 2026-07 architecture-modularization
refactor. Shared service singletons live in app/dependencies.py; shared
request models live in app/schemas/api_requests.py.
"""
from __future__ import annotations

from app.auth import require_permission
from app.schemas.project_apartment import ResidentPortalPayload
from fastapi import Depends
from fastapi.responses import Response
from urllib.parse import quote

from fastapi import APIRouter
import app.dependencies as deps


router = APIRouter()


@router.get(
    "/resident-portal/me",
    response_model=ResidentPortalPayload,
)
def get_my_resident_portal(
    auth=Depends(require_permission("resident_portal:read")),
):
    return deps.resident_portal_service.get_portal_for_resident(
        organization_id=auth.org_id,
        actor_user_id=auth.user_id,
        actor_role=auth.role,
    )


@router.get("/resident-portal/reports/{report_id}/pdf")
def get_resident_portal_report_pdf(
    report_id: str,
    auth=Depends(require_permission("resident_portal:read")),
):
    deps.resident_portal_service.assert_resident_can_access_report(
        organization_id=auth.org_id,
        actor_user_id=auth.user_id,
        actor_role=auth.role,
        report_id=report_id,
    )
    content, content_type, filename = (
        deps.field_visit_report_service.get_archived_report_pdf(
            organization_id=auth.org_id,
            report_id=report_id,
        )
    )
    safe_filename = quote(filename)
    return Response(
        content=content,
        media_type=content_type,
        headers={
            "Content-Disposition": (
                f'attachment; filename="{safe_filename}"; '
                f"filename*=UTF-8''{safe_filename}"
            ),
        },
    )


