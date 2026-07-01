"""Field visit report routes.

Extracted from app/main.py during the 2026-07 architecture-modularization
refactor. Shared service singletons live in app/dependencies.py; shared
request models live in app/schemas/api_requests.py.
"""
from __future__ import annotations

from app.auth import (
    get_auth_context,
    require_permission,
)
from app.auth.field_report_dependencies import require_field_report_module
from app.config.settings import settings
from app.schemas.field_report_finalize import (
    FieldReportFinalizeStartResponse,
    FieldReportFinalizeStatusResponse,
)
from app.schemas.field_reports import (
    FieldVisitReportClosePreview,
    FieldVisitReportCreateRequest,
    FieldVisitReportDraftIssueRequest,
    FieldVisitReportLineCreateRequest,
    FieldVisitReportLineUpdateRequest,
    FieldVisitReportPublishPreview,
    FieldVisitReportSyncRequest,
    FieldVisitReportSyncResponse,
    FieldVisitReportUpdateRequest,
)
from fastapi import (
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
)
from fastapi.responses import Response
from urllib.parse import quote

from fastapi import APIRouter
import app.dependencies as deps


router = APIRouter()


@router.get("/field-reports/module-status")
def get_field_report_module_status(
    auth=Depends(get_auth_context),
):
    return deps.field_report_module_service.get_status(
        auth.org_id
    )


@router.get("/field-reports/organization-profile")
def get_field_report_organization_profile(
    auth=Depends(require_field_report_module),
):
    return deps.field_report_organization_profile_service.get_profile(
        auth.org_id
    )


@router.get("/field-reports/home")
def field_reports_home(
    auth=Depends(require_permission("field_reports:read")),
    _module=Depends(require_field_report_module),
):
    return {
        "module": "field_reports",
        "organization_id": auth.org_id,
        "status": "ready",
    }


@router.get("/field-reports/visit-types")
def list_field_report_visit_types(
    auth=Depends(
        require_permission("field_reports:read")
    ),
    _module=Depends(require_field_report_module),
):
    return deps.field_visit_report_service.get_visit_types()


@router.get("/field-reports/visits")
def list_field_visit_reports(
    status: str | None = None,
    project_id: str | None = None,
    auth=Depends(
        require_permission("field_reports:read")
    ),
    _module=Depends(require_field_report_module),
):
    if project_id:
        project = deps.tenant_scope_service.get_organization_scoped_project(
            project_id,
            auth.org_id,
            role=auth.role,
            actor_user_id=auth.actor_user_id,
        )
        if project is None:
            raise HTTPException(status_code=404, detail="Project not found")

    projects = deps.project_repository.get_projects_by_organization(
        auth.org_id
    )
    projects = deps.tenant_scope_service.filter_actor_projects(
        projects,
        role=auth.role,
        actor_user_id=auth.actor_user_id,
    )
    project_names = {
        str(project["id"]): project.get("project_name")
        for project in projects
    }

    return deps.field_visit_report_service.list_reports(
        auth.org_id,
        status=status,
        project_id=project_id,
        project_names=project_names,
    )


@router.get("/field-reports/visits/{report_id}")
def get_field_visit_report(
    report_id: str,
    auth=Depends(
        require_permission("field_reports:read")
    ),
    _module=Depends(require_field_report_module),
):
    return deps.field_visit_report_service.get_report(
        organization_id=auth.org_id,
        report_id=report_id,
    )


@router.get("/field-reports/visits/{report_id}/delete-eligibility")
def get_field_visit_report_delete_eligibility(
    report_id: str,
    auth=Depends(
        require_permission("field_reports:read")
    ),
    _module=Depends(require_field_report_module),
):
    return deps.report_deletion_service.check_field_visit_report_deletable(
        organization_id=auth.org_id,
        report_id=report_id,
    )


@router.delete("/field-reports/visits/{report_id}")
def delete_field_visit_report(
    report_id: str,
    auth=Depends(
        require_permission("field_reports:write")
    ),
    _module=Depends(require_field_report_module),
):
    return deps.report_deletion_service.delete_field_visit_report(
        organization_id=auth.org_id,
        report_id=report_id,
        actor_id=auth.user_id,
    )


@router.post("/field-reports/visits")
def create_field_visit_report(
    request: FieldVisitReportCreateRequest,
    auth=Depends(
        require_permission("field_reports:write")
    ),
    _module=Depends(require_field_report_module),
):
    return deps.field_visit_report_service.create_report(
        organization_id=auth.org_id,
        actor_profile_id=auth.user_id,
        project_id=request.project_id,
        visit_type=request.visit_type,
        visit_date=request.visit_date.isoformat(),
        header_fields=request.header_fields,
        catalog_version=request.catalog_version,
        client_report_uuid=request.client_report_uuid,
    )


@router.put(
    "/field-reports/visits/sync",
    response_model=FieldVisitReportSyncResponse,
)
def sync_field_visit_report(
    body: FieldVisitReportSyncRequest,
    http_request: Request,
    auth=Depends(
        require_permission("field_reports:write")
    ),
    _module=Depends(require_field_report_module),
):
    closed_at = body.closed_at
    if closed_at is not None and hasattr(closed_at, "isoformat"):
        closed_at = closed_at.isoformat()

    return deps.field_visit_report_service.sync_visit_report(
        organization_id=auth.org_id,
        actor_profile_id=auth.user_id,
        client_report_uuid=body.client_report_uuid,
        project_id=body.project_id,
        visit_type=body.visit_type,
        visit_date=body.visit_date.isoformat(),
        header_fields=body.header_fields,
        catalog_version=body.catalog_version,
        organization_profile_snapshot=body.organization_profile_snapshot,
        status=body.status,
        closed_at=closed_at,
        lines=[line.model_dump(exclude_none=True) for line in body.lines],
        idempotency_key=http_request.headers.get(
            settings.IDEMPOTENCY_HEADER
        ),
    )


@router.post(
    "/field-reports/visits/sync/{client_report_uuid}/lines/"
    "{client_line_uuid}/photos",
)
async def add_field_visit_report_sync_line_photo(
    client_report_uuid: str,
    client_line_uuid: str,
    http_request: Request,
    file: UploadFile = File(...),
    auth=Depends(
        require_permission("field_reports:write")
    ),
    _module=Depends(require_field_report_module),
):
    content = await file.read()
    return deps.field_visit_report_service.add_line_photo_by_client_uuids(
        organization_id=auth.org_id,
        client_report_uuid=client_report_uuid,
        client_line_uuid=client_line_uuid,
        content=content,
        content_type=file.content_type,
        filename=file.filename,
        idempotency_key=http_request.headers.get(
            settings.IDEMPOTENCY_HEADER
        ),
    )


@router.patch("/field-reports/visits/{report_id}")
def update_field_visit_report(
    report_id: str,
    request: FieldVisitReportUpdateRequest,
    auth=Depends(
        require_permission("field_reports:write")
    ),
    _module=Depends(require_field_report_module),
):
    return deps.field_visit_report_service.update_report(
        organization_id=auth.org_id,
        report_id=report_id,
        visit_date=(
            request.visit_date.isoformat()
            if request.visit_date
            else None
        ),
        header_fields=request.header_fields,
        catalog_version=request.catalog_version,
        actor_user_id=auth.actor_user_id,
    )


@router.get(
    "/field-reports/visits/{report_id}/close-preview",
    response_model=FieldVisitReportClosePreview,
)
def preview_close_field_visit_report(
    report_id: str,
    auth=Depends(
        require_permission("field_reports:read")
    ),
    _module=Depends(require_field_report_module),
):
    return deps.field_visit_report_service.preview_close_report(
        organization_id=auth.org_id,
        report_id=report_id,
    )


@router.post("/field-reports/visits/{report_id}/close")
def close_field_visit_report(
    report_id: str,
    auth=Depends(
        require_permission("field_reports:write")
    ),
    _module=Depends(require_field_report_module),
):
    return deps.field_visit_report_service.close_report(
        organization_id=auth.org_id,
        report_id=report_id,
        actor_id=auth.user_id,
    )


@router.get(
    "/field-reports/visits/{report_id}/publish-preview",
    response_model=FieldVisitReportPublishPreview,
)
def preview_publish_field_visit_report(
    report_id: str,
    auth=Depends(
        require_permission("field_reports:publish")
    ),
    _module=Depends(require_field_report_module),
):
    return deps.field_visit_report_service.preview_publish_report(
        organization_id=auth.org_id,
        report_id=report_id,
    )


@router.post("/field-reports/visits/{report_id}/publish")
async def publish_field_visit_report(
    report_id: str,
    file: UploadFile | None = File(None),
    auth=Depends(
        require_permission("field_reports:publish")
    ),
    _module=Depends(require_field_report_module),
):
    source_content: bytes | None = None
    source_filename: str | None = None
    if file is not None:
        source_content = await file.read()
        source_filename = file.filename or f"{report_id}.pdf"

    return deps.field_visit_report_service.publish_report(
        organization_id=auth.org_id,
        report_id=report_id,
        actor_id=auth.user_id,
        source_filename=source_filename,
        source_content=source_content,
    )


@router.post(
    "/field-reports/visits/{report_id}/finalize",
    status_code=202,
    response_model=FieldReportFinalizeStartResponse,
)
async def finalize_field_visit_report(
    report_id: str,
    request: Request,
    file: UploadFile = File(...),
    client_report_uuid: str | None = Form(None),
    auth=Depends(
        require_permission("field_reports:finalize")
    ),
    _module=Depends(require_field_report_module),
):
    file_content = await file.read()
    return deps.field_report_finalize_service.start_finalize(
        organization_id=auth.org_id,
        report_id=report_id,
        actor_id=auth.user_id,
        source_content=file_content,
        source_filename=file.filename or f"{report_id}.pdf",
        idempotency_key=request.headers.get(
            settings.IDEMPOTENCY_HEADER,
        ),
        client_report_uuid=client_report_uuid,
    )


@router.get(
    "/field-reports/visits/{report_id}/finalize-status",
    response_model=FieldReportFinalizeStatusResponse,
)
def get_field_visit_finalize_status(
    report_id: str,
    auth=Depends(
        require_permission("field_reports:read")
    ),
    _module=Depends(require_field_report_module),
):
    return deps.field_report_finalize_service.get_finalize_status(
        organization_id=auth.org_id,
        report_id=report_id,
    )


@router.post("/field-reports/visits/{report_id}/reopen")
def reopen_field_visit_report(
    report_id: str,
    auth=Depends(
        require_permission("field_reports:write")
    ),
    _module=Depends(require_field_report_module),
):
    return deps.field_visit_report_service.reopen_report(
        organization_id=auth.org_id,
        report_id=report_id,
    )


@router.post("/field-reports/visits/{report_id}/request-send")
async def request_send_field_visit_report(
    report_id: str,
    file: UploadFile = File(...),
    auth=Depends(
        require_permission("field_reports:write")
    ),
    _module=Depends(require_field_report_module),
):
    file_content = await file.read()
    return deps.field_visit_report_service.request_send_to_core(
        organization_id=auth.org_id,
        report_id=report_id,
        source_filename=file.filename or f"{report_id}.pdf",
        source_content=file_content,
    )


@router.get("/field-reports/visits/{report_id}/pdf")
def get_field_visit_report_pdf(
    report_id: str,
    auth=Depends(
        require_permission("field_reports:read")
    ),
    _module=Depends(require_field_report_module),
):
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


@router.get("/field-reports/catalog")
def get_field_report_catalog(
    visit_type: str | None = None,
    auth=Depends(
        require_permission("field_reports:read")
    ),
    _module=Depends(require_field_report_module),
):
    return deps.field_visit_report_service.get_catalog(
        visit_type=visit_type,
    )


@router.get("/field-reports/offline-prep")
def get_field_report_offline_prep(
    auth=Depends(
        require_permission("field_reports:read")
    ),
    _module=Depends(require_field_report_module),
):
    return deps.field_visit_report_service.build_offline_prep_bundle(
        auth.org_id,
    )


@router.get("/field-reports/visits/{report_id}/lines")
def list_field_visit_report_lines(
    report_id: str,
    auth=Depends(
        require_permission("field_reports:read")
    ),
    _module=Depends(require_field_report_module),
):
    return deps.field_visit_report_service.list_lines(
        organization_id=auth.org_id,
        report_id=report_id,
    )


@router.post("/field-reports/visits/{report_id}/lines")
def create_field_visit_report_line(
    report_id: str,
    request: FieldVisitReportLineCreateRequest,
    auth=Depends(
        require_permission("field_reports:write")
    ),
    _module=Depends(require_field_report_module),
):
    return deps.field_visit_report_service.create_line(
        organization_id=auth.org_id,
        report_id=report_id,
        payload=request.model_dump(exclude_none=True),
    )


@router.patch(
    "/field-reports/visits/{report_id}/lines/{line_id}"
)
def update_field_visit_report_line(
    report_id: str,
    line_id: str,
    request: FieldVisitReportLineUpdateRequest,
    auth=Depends(
        require_permission("field_reports:write")
    ),
    _module=Depends(require_field_report_module),
):
    return deps.field_visit_report_service.update_line(
        organization_id=auth.org_id,
        report_id=report_id,
        line_id=line_id,
        payload=request.model_dump(exclude_unset=True),
    )


@router.post(
    "/field-reports/visits/{report_id}/lines/{line_id}/draft-issue"
)
def materialize_field_visit_draft_issue(
    report_id: str,
    line_id: str,
    request: FieldVisitReportDraftIssueRequest,
    auth=Depends(
        require_permission("field_reports:write")
    ),
    _module=Depends(require_field_report_module),
):
    return deps.field_visit_report_service.materialize_draft_issue_from_line(
        organization_id=auth.org_id,
        report_id=report_id,
        line_id=line_id,
        actor_id=auth.user_id,
        checklist_item_id=request.checklist_item_id,
    )


@router.delete(
    "/field-reports/visits/{report_id}/lines/{line_id}"
)
def delete_field_visit_report_line(
    report_id: str,
    line_id: str,
    auth=Depends(
        require_permission("field_reports:write")
    ),
    _module=Depends(require_field_report_module),
):
    return deps.field_visit_report_service.delete_line(
        organization_id=auth.org_id,
        report_id=report_id,
        line_id=line_id,
    )


@router.post(
    "/field-reports/visits/{report_id}/lines/{line_id}/photo"
)
async def upload_field_visit_report_line_photo(
    report_id: str,
    line_id: str,
    file: UploadFile = File(...),
    auth=Depends(
        require_permission("field_reports:write")
    ),
    _module=Depends(require_field_report_module),
):
    content = await file.read()
    return deps.field_visit_report_service.upload_line_photo(
        organization_id=auth.org_id,
        report_id=report_id,
        line_id=line_id,
        content=content,
        content_type=file.content_type,
        filename=file.filename,
    )


@router.get(
    "/field-reports/visits/{report_id}/lines/{line_id}/photo"
)
def get_field_visit_report_line_photo(
    report_id: str,
    line_id: str,
    auth=Depends(
        require_permission("field_reports:read")
    ),
    _module=Depends(require_field_report_module),
):
    content, content_type = deps.field_visit_report_service.get_line_photo(
        organization_id=auth.org_id,
        report_id=report_id,
        line_id=line_id,
    )
    return Response(content=content, media_type=content_type)


@router.delete(
    "/field-reports/visits/{report_id}/lines/{line_id}/photo"
)
def delete_field_visit_report_line_photo(
    report_id: str,
    line_id: str,
    auth=Depends(
        require_permission("field_reports:write")
    ),
    _module=Depends(require_field_report_module),
):
    return deps.field_visit_report_service.delete_line_photo(
        organization_id=auth.org_id,
        report_id=report_id,
        line_id=line_id,
    )


@router.get(
    "/field-reports/visits/{report_id}/lines/{line_id}/photos"
)
def list_field_visit_report_line_photos(
    report_id: str,
    line_id: str,
    auth=Depends(
        require_permission("field_reports:read")
    ),
    _module=Depends(require_field_report_module),
):
    return deps.field_visit_report_service.list_line_photos(
        organization_id=auth.org_id,
        report_id=report_id,
        line_id=line_id,
    )


@router.post(
    "/field-reports/visits/{report_id}/lines/{line_id}/photos"
)
async def add_field_visit_report_line_photo(
    report_id: str,
    line_id: str,
    file: UploadFile = File(...),
    auth=Depends(
        require_permission("field_reports:write")
    ),
    _module=Depends(require_field_report_module),
):
    content = await file.read()
    return deps.field_visit_report_service.add_line_photo(
        organization_id=auth.org_id,
        report_id=report_id,
        line_id=line_id,
        content=content,
        content_type=file.content_type,
        filename=file.filename,
    )


@router.get(
    "/field-reports/visits/{report_id}/lines/{line_id}/photos/{photo_id}"
)
def get_field_visit_report_line_photo_by_id(
    report_id: str,
    line_id: str,
    photo_id: str,
    auth=Depends(
        require_permission("field_reports:read")
    ),
    _module=Depends(require_field_report_module),
):
    content, content_type = deps.field_visit_report_service.get_line_photo_by_id(
        organization_id=auth.org_id,
        report_id=report_id,
        line_id=line_id,
        photo_id=photo_id,
    )
    return Response(content=content, media_type=content_type)


@router.delete(
    "/field-reports/visits/{report_id}/lines/{line_id}/photos/{photo_id}"
)
def delete_field_visit_report_line_photo_by_id(
    report_id: str,
    line_id: str,
    photo_id: str,
    auth=Depends(
        require_permission("field_reports:write")
    ),
    _module=Depends(require_field_report_module),
):
    return deps.field_visit_report_service.delete_line_photo_by_id(
        organization_id=auth.org_id,
        report_id=report_id,
        line_id=line_id,
        photo_id=photo_id,
    )


