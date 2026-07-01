"""Project routes.

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
from app.auth.tenant_manager_dependencies import require_tenant_manager_module
from app.schemas.project_apartment import (
    BulkUpsertProjectApartmentsRequest,
    BulkUpsertProjectApartmentsResponse,
    InviteResidentResponse,
    ProjectApartmentListResponse,
    ResidentPortalPayload,
    UpdateProjectApartmentRequest,
    UpdateProjectApartmentResponse,
)
from app.schemas.project_spatial_bootstrap import ProjectSpatialBootstrapResponse
from app.schemas.project_supervision_dashboard import (
    ProjectSupervisionDashboardResponse,
    SupervisionProjectSummariesResponse,
    SupervisionTradeDetailResponse,
)
from app.schemas.quality_issue import (
    QualityIssue,
    QualityIssueCreateRequest,
    QualityIssueListQuery,
    QualityIssueListResponse,
    QualityIssueOpenListResponse,
    QualityIssueSeverity,
    QualityIssueStatus,
    QualityIssueSuggestMatchesRequest,
    QualityIssueSuggestMatchesResponse,
    QualityIssueVisitDiffResponse,
    parse_quality_issue_row,
)
from fastapi import (
    Depends,
    File,
    HTTPException,
    Query,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.responses import Response
from typing import Annotated

from fastapi import APIRouter
import app.dependencies as deps
import app.services.connection_managers as conn_mgrs
from app.schemas.api_requests import (
    ActionAIGenerationRequest,
    ActionAttachmentRequest,
    ActionBulkRequest,
    ActionCategoryRequest,
    ActionCommentRequest,
    ActionEscalationRequest,
    ActionNotificationRequest,
    ActionOwnerRequest,
    ActionRecurringRequest,
    ActionRetryRequest,
    ActionTemplateApplyRequest,
    ActionTemplateRequest,
    CreateProjectRequest,
    DeleteProjectRequest,
    EditProjectRequest,
    ProjectAttachmentRequest,
    ProjectCommentRequest,
    ProjectLifecycleRequest,
    ProjectOwnerRequest,
    ProjectTagsRequest,
    ReportAttachmentRequest,
    ReportTagsRequest,
    WorkspaceActivityCreateRequest,
    WorkspaceLayoutRequest,
    WorkspaceWidgetsRequest,
)


router = APIRouter()


@router.get(
    "/projects/{project_id}/apartments",
    response_model=ProjectApartmentListResponse,
)
def list_project_apartments(
    project_id: str,
    auth=Depends(require_permission("apartments:read")),
    _module=Depends(require_tenant_manager_module),
):
    return deps.project_apartment_service.list_apartments(
        organization_id=auth.org_id,
        project_id=project_id,
        actor_role=auth.role,
        actor_user_id=auth.actor_user_id,
    )


@router.post(
    "/projects/{project_id}/apartments/bulk",
    response_model=BulkUpsertProjectApartmentsResponse,
)
def bulk_upsert_project_apartments(
    project_id: str,
    request: BulkUpsertProjectApartmentsRequest,
    auth=Depends(require_permission("apartments:write")),
    _module=Depends(require_tenant_manager_module),
):
    return deps.project_apartment_service.bulk_upsert(
        organization_id=auth.org_id,
        project_id=project_id,
        apartments=[item.model_dump() for item in request.apartments],
        actor_role=auth.role,
        actor_user_id=auth.actor_user_id,
    )


@router.patch(
    "/projects/{project_id}/apartments/{apartment_id}",
    response_model=UpdateProjectApartmentResponse,
)
def update_project_apartment(
    project_id: str,
    apartment_id: str,
    request: UpdateProjectApartmentRequest,
    auth=Depends(require_permission("apartments:write")),
    _module=Depends(require_tenant_manager_module),
):
    return deps.project_apartment_service.update_apartment(
        organization_id=auth.org_id,
        project_id=project_id,
        apartment_id=apartment_id,
        apartment_number=request.apartment_number,
        owner_name=request.owner_name,
        phone=request.phone,
        email=request.email,
        actor_role=auth.role,
        actor_user_id=auth.actor_user_id,
    )


@router.post(
    "/projects/{project_id}/apartments/{apartment_id}/invite",
    response_model=InviteResidentResponse,
)
def invite_project_apartment_resident(
    project_id: str,
    apartment_id: str,
    auth=Depends(require_permission("apartments:write")),
    _module=Depends(require_tenant_manager_module),
):
    _ = project_id
    return deps.resident_invite_service.invite_resident_for_apartment(
        organization_id=auth.org_id,
        apartment_id=apartment_id,
        invited_by=auth.user_id,
        inviter_role=auth.role,
    )


@router.post("/projects/{project_id}/apartments/invite-all")
def invite_all_project_apartment_residents(
    project_id: str,
    auth=Depends(require_permission("apartments:write")),
    _module=Depends(require_tenant_manager_module),
):
    return deps.resident_invite_service.bulk_invite_residents(
        organization_id=auth.org_id,
        project_id=project_id,
        invited_by=auth.user_id,
        inviter_role=auth.role,
    )


@router.get(
    "/projects/{project_id}/apartments/{apartment_id}/portal",
    response_model=ResidentPortalPayload,
)
def get_apartment_resident_portal(
    project_id: str,
    apartment_id: str,
    auth=Depends(require_permission("apartments:read")),
    _module=Depends(require_tenant_manager_module),
):
    _ = project_id
    return deps.resident_portal_service.get_portal_for_apartment(
        organization_id=auth.org_id,
        apartment_id=apartment_id,
        actor_user_id=auth.user_id,
        actor_role=auth.role,
    )


@router.get("/projects/{project_id}/field-reports/archive")
def get_project_field_report_archive(
    project_id: str,
    auth=Depends(
        require_permission("field_reports:read")
    ),
    _module=Depends(require_field_report_module),
):
    if not deps.tenant_scope_service.get_organization_scoped_project(
        project_id,
        auth.org_id,
        role=auth.role,
        actor_user_id=auth.actor_user_id,
    ):
        raise HTTPException(status_code=404, detail="Project not found")

    return deps.field_visit_report_service.get_project_field_report_archive(
        organization_id=auth.org_id,
        project_id=project_id,
    )


@router.post(
    "/projects/{project_id}/issues",
    response_model=QualityIssue,
)
def create_project_quality_issue(
    project_id: str,
    request: QualityIssueCreateRequest,
    auth=Depends(get_auth_context),
):
    record = deps.quality_issue_service.create_issue(
        organization_id=auth.org_id,
        project_id=project_id,
        request=request,
        actor_role=auth.role,
        actor_id=auth.effective_user_id or auth.user_id,
    )
    return parse_quality_issue_row(record)


@router.get(
    "/projects/{project_id}/issues/open",
    response_model=QualityIssueOpenListResponse,
)
def list_project_open_quality_issues(
    project_id: str,
    auth=Depends(get_auth_context),
):
    return deps.quality_issue_service.list_open_issues(
        organization_id=auth.org_id,
        project_id=project_id,
        actor_role=auth.role,
        actor_user_id=auth.actor_user_id,
    )


@router.post(
    "/projects/{project_id}/issues/suggest-matches",
    response_model=QualityIssueSuggestMatchesResponse,
)
def suggest_project_quality_issue_matches(
    project_id: str,
    request: QualityIssueSuggestMatchesRequest,
    auth=Depends(get_auth_context),
):
    return deps.quality_issue_service.suggest_matches(
        organization_id=auth.org_id,
        project_id=project_id,
        request=request,
        actor_role=auth.role,
        actor_user_id=auth.actor_user_id,
    )


@router.get(
    "/projects/{project_id}/visits/{report_id}/issue-diff",
    response_model=QualityIssueVisitDiffResponse,
)
def get_project_visit_issue_diff(
    project_id: str,
    report_id: str,
    auth=Depends(get_auth_context),
):
    return deps.quality_issue_service.get_visit_issue_diff(
        organization_id=auth.org_id,
        project_id=project_id,
        report_id=report_id,
        actor_role=auth.role,
        actor_user_id=auth.actor_user_id,
    )


@router.get(
    "/projects/{project_id}/issues",
    response_model=QualityIssueListResponse,
)
def list_project_quality_issues(
    project_id: str,
    status: Annotated[
        list[QualityIssueStatus] | None,
        Query(),
    ] = None,
    severity: Annotated[
        list[QualityIssueSeverity] | None,
        Query(),
    ] = None,
    trade: str | None = None,
    search: str | None = None,
    limit: int = 50,
    offset: int = 0,
    auth=Depends(get_auth_context),
):
    return deps.quality_issue_service.list_issues(
        organization_id=auth.org_id,
        project_id=project_id,
        query=QualityIssueListQuery(
            status=status,
            severity=severity,
            trade=trade,
            search=search,
            limit=limit,
            offset=offset,
        ),
        actor_role=auth.role,
        actor_user_id=auth.actor_user_id,
    )


@router.get("/project-templates/resolve")
def resolve_project_template(
    scheme: str,
    auth=Depends(require_permission("projects:read")),
):
    return deps.project_template_service.resolve_for_scheme(
        scheme,
        organization_id=auth.org_id,
    ).model_dump()


@router.post("/projects")
def create_project(
    request: CreateProjectRequest,
    auth=Depends(require_permission("projects:write")),
):
    return deps.project_service.create_project(
        project_name=request.project_name,
        developer_name=request.developer_name,
        contractor_name=request.contractor_name,
        lawyer_name=request.lawyer_name,
        supervisor_name=request.supervisor_name,
        supervisor_email=request.supervisor_email,
        organization_id=auth.org_id,
        owner_id=request.owner_id or auth.user_id,
        tags=request.tags,
        scheme=request.scheme,
        developer_pm_name=request.developer_pm_name,
        accompanying_lawyer=request.accompanying_lawyer,
        architect_name=request.architect_name,
        site_manager_name=request.site_manager_name,
        city=request.city,
        housing_units_count=request.housing_units_count,
        floors_count=request.floors_count,
        project_start_date=request.project_start_date,
        project_end_date=request.project_end_date,
        project_grace_end_date=request.project_grace_end_date,
        structure_documentation_date=request.structure_documentation_date,
        developer_email=request.developer_email,
        developer_pm_email=request.developer_pm_email,
        site_manager_email=request.site_manager_email,
        contractor_email=request.contractor_email,
        lawyer_email=request.lawyer_email,
        accompanying_lawyer_email=request.accompanying_lawyer_email,
        architect_email=request.architect_email,
    )


@router.post(
    "/projects/{project_id}/bootstrap-spatial",
    response_model=ProjectSpatialBootstrapResponse,
)
def bootstrap_project_spatial(
    project_id: str,
    auth=Depends(require_permission("projects:write")),
):
    project = deps.tenant_scope_service.get_organization_scoped_project(
        project_id,
        auth.org_id,
        role=auth.role,
        actor_user_id=auth.actor_user_id,
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    scheme = project.get("scheme")
    if not scheme:
        raise HTTPException(
            status_code=422,
            detail="Project scheme is required for spatial bootstrap",
        )

    return deps.project_spatial_bootstrap_service.bootstrap(
        project_id=project_id,
        scheme=str(scheme),
        organization_id=auth.org_id,
        floors=project.get("floors_count"),
        housing_units_count=project.get("housing_units_count"),
    )


@router.get("/projects/{project_id}/offline-prep")
def get_project_offline_prep(
    project_id: str,
    auth=Depends(require_permission("field_reports:read")),
    _module=Depends(require_field_report_module),
):
    if not deps.tenant_scope_service.get_organization_scoped_project(
        project_id,
        auth.org_id,
        role=auth.role,
        actor_user_id=auth.actor_user_id,
    ):
        raise HTTPException(status_code=404, detail="Project not found")

    return deps.field_visit_report_service.build_offline_prep_bundle_for_project(
        auth.org_id,
        project_id,
    )


@router.patch("/projects/{project_id}")
def edit_project(
    project_id: str,
    request: EditProjectRequest,
    auth=Depends(require_permission("projects:write")),
):
    if not deps.tenant_scope_service.get_organization_scoped_project(
        project_id,
        auth.org_id,
        role=auth.role,
        actor_user_id=auth.actor_user_id,
    ):
        raise HTTPException(status_code=404, detail="Project not found")

    updated = deps.project_service.edit_project(
        project_id,
        project_name=request.project_name,
        developer_name=request.developer_name,
        contractor_name=request.contractor_name,
        lawyer_name=request.lawyer_name,
        supervisor_name=request.supervisor_name,
        supervisor_email=request.supervisor_email,
        scheme=request.scheme,
        developer_pm_name=request.developer_pm_name,
        accompanying_lawyer=request.accompanying_lawyer,
        architect_name=request.architect_name,
        site_manager_name=request.site_manager_name,
        city=request.city,
        housing_units_count=request.housing_units_count,
        floors_count=request.floors_count,
        project_start_date=request.project_start_date,
        project_end_date=request.project_end_date,
        project_grace_end_date=request.project_grace_end_date,
        structure_documentation_date=request.structure_documentation_date,
        illustration_url=request.illustration_url,
        illustration_source_he=request.illustration_source_he,
        developer_email=request.developer_email,
        developer_pm_email=request.developer_pm_email,
        site_manager_email=request.site_manager_email,
        contractor_email=request.contractor_email,
        lawyer_email=request.lawyer_email,
        accompanying_lawyer_email=request.accompanying_lawyer_email,
        architect_email=request.architect_email,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Project not found")
    return updated


@router.post("/projects/{project_id}/illustration")
async def upload_project_illustration(
    project_id: str,
    file: UploadFile = File(...),
    auth=Depends(require_permission("projects:write")),
):
    project = deps.tenant_scope_service.get_organization_scoped_project(
        project_id,
        auth.org_id,
        role=auth.role,
        actor_user_id=auth.actor_user_id,
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    content = await file.read()
    updated = deps.project_service.upload_project_illustration(
        project_id=project_id,
        organization_id=auth.org_id,
        content=content,
        content_type=file.content_type,
        filename=file.filename,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Project not found")
    return updated


@router.get("/projects/{project_id}/illustration")
def get_project_illustration(
    project_id: str,
    auth=Depends(require_permission("projects:read")),
):
    project = deps.tenant_scope_service.get_organization_scoped_project(
        project_id,
        auth.org_id,
        role=auth.role,
        actor_user_id=auth.actor_user_id,
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    payload = deps.project_service.read_project_illustration(
        organization_id=auth.org_id,
        project_id=project_id,
    )
    if not payload:
        raise HTTPException(status_code=404, detail="Illustration not found")

    content, content_type = payload
    return Response(content=content, media_type=content_type)


@router.post("/projects/{project_id}/archive")
def archive_project(project_id: str):
    archived = deps.project_service.archive_project(project_id)
    if not archived:
        raise HTTPException(status_code=404, detail="Project not found")
    return archived


@router.delete("/projects/{project_id}")
def delete_project(
    project_id: str,
    request: DeleteProjectRequest,
    auth=Depends(require_permission("projects:delete")),
):
    if not deps.tenant_scope_service.get_organization_scoped_project(
        project_id,
        auth.org_id,
        role=auth.role,
        actor_user_id=auth.actor_user_id,
    ):
        raise HTTPException(status_code=404, detail="Project not found")

    return deps.project_deletion_service.delete_project(
        organization_id=auth.org_id,
        project_id=project_id,
        confirm_project_name=request.confirm_project_name,
        actor_user_id=auth.user_id,
        actor_role=auth.role,
    )


@router.get("/projects/search")
def search_projects(
    query: str,
    auth=Depends(require_permission("projects:read")),
):
    projects = deps.project_service.search_projects(
        query,
        organization_id=auth.org_id,
    )
    return deps.tenant_scope_service.filter_actor_projects(
        projects,
        role=auth.role,
        actor_user_id=auth.actor_user_id,
    )


@router.get("/projects")
def filter_projects(
    status: str | None = None,
    owner_id: str | None = None,
    tag: str | None = None,
    auth=Depends(require_permission("projects:read")),
):
    projects = deps.project_service.filter_projects(
        status=status,
        owner_id=owner_id,
        tag=tag,
        organization_id=auth.org_id,
    )
    return deps.tenant_scope_service.filter_actor_projects(
        projects,
        role=auth.role,
        actor_user_id=auth.actor_user_id,
    )


@router.patch("/projects/{project_id}/tags")
def update_project_tags(project_id: str, request: ProjectTagsRequest):
    updated = deps.project_service.update_project_tags(project_id, request.tags)
    if not updated:
        raise HTTPException(status_code=404, detail="Project not found")
    return updated


@router.patch("/projects/{project_id}/owner")
def set_project_owner(project_id: str, request: ProjectOwnerRequest):
    updated = deps.project_service.set_project_owner(project_id, request.owner_id)
    if not updated:
        raise HTTPException(status_code=404, detail="Project not found")
    return updated


@router.patch("/projects/{project_id}/lifecycle")
def set_project_lifecycle(project_id: str, request: ProjectLifecycleRequest):
    updated = deps.project_service.set_project_lifecycle_phase(
        project_id,
        request.lifecycle_phase,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Project not found")
    return updated


@router.get(
    "/projects/{project_id}/supervision-dashboard",
    response_model=ProjectSupervisionDashboardResponse,
)
def get_project_supervision_dashboard(
    project_id: str,
    auth=Depends(get_auth_context),
):
    return deps.project_supervision_dashboard_service.build_dashboard_for_actor(
        organization_id=auth.org_id,
        project_id=project_id,
        actor_role=auth.role,
    )


@router.get(
    "/projects/supervision-summaries",
    response_model=SupervisionProjectSummariesResponse,
)
def get_project_supervision_summaries(
    auth=Depends(get_auth_context),
):
    return deps.project_supervision_dashboard_service.build_summaries_for_actor(
        organization_id=auth.org_id,
        actor_role=auth.role,
    )


@router.get(
    "/projects/{project_id}/supervision-dashboard/trades/{trade_key}",
    response_model=SupervisionTradeDetailResponse,
)
def get_project_supervision_trade_detail(
    project_id: str,
    trade_key: str,
    auth=Depends(get_auth_context),
):
    return deps.project_supervision_dashboard_service.build_trade_detail_for_actor(
        organization_id=auth.org_id,
        project_id=project_id,
        trade_key=trade_key,
        actor_role=auth.role,
    )


@router.get("/projects/{project_id}/dashboard-widgets")
def get_project_dashboard_widgets(project_id: str):
    widgets = deps.project_service.get_dashboard_widgets(project_id)
    if not widgets:
        raise HTTPException(status_code=404, detail="Project not found")
    return widgets


@router.get("/projects/{project_id}/links")
def get_cross_project_links(project_id: str):
    links = deps.project_service.get_cross_project_links(project_id)
    if not links:
        raise HTTPException(status_code=404, detail="Project not found")
    return links


@router.get("/projects/{project_id}/kpis")
def get_project_kpis(project_id: str):
    kpis = deps.project_service.get_project_kpis(project_id)
    if not kpis:
        raise HTTPException(status_code=404, detail="Project not found")
    return kpis


@router.get("/projects/{project_id}/analytics")
def get_project_analytics(project_id: str):
    analytics = deps.project_service.get_project_analytics(project_id)
    if not analytics:
        raise HTTPException(status_code=404, detail="Project not found")
    return analytics


@router.get("/projects/{project_id}/attachments")
def get_project_attachments(project_id: str):
    attachments = deps.project_service.get_project_attachments(project_id)
    if attachments is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"project_id": project_id, "attachments": attachments}


@router.post("/projects/{project_id}/attachments")
def add_project_attachment(project_id: str, request: ProjectAttachmentRequest):
    attachment = deps.project_service.add_project_attachment(
        project_id=project_id,
        filename=request.filename,
        uploaded_by=request.uploaded_by,
    )
    if not attachment:
        raise HTTPException(status_code=404, detail="Project not found")
    return attachment


@router.get("/projects/{project_id}/comments")
def get_project_comments(project_id: str):
    comments = deps.project_service.get_project_comments(project_id)
    if comments is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"project_id": project_id, "comments": comments}


@router.post("/projects/{project_id}/comments")
def add_project_comment(project_id: str, request: ProjectCommentRequest):
    comment = deps.project_service.add_project_comment(
        project_id=project_id,
        comment=request.comment,
        author=request.author,
    )
    if not comment:
        raise HTTPException(status_code=404, detail="Project not found")
    return comment


@router.get("/projects/{project_id}/reports/upload-jobs/{job_id}")
def get_reports_bulk_upload_progress(
    project_id: str,
    job_id: str,
    auth=Depends(require_permission("reports:read")),
):
    if not deps.tenant_scope_service.get_organization_scoped_project(
        project_id,
        auth.org_id,
        role=auth.role,
        actor_user_id=auth.actor_user_id,
    ):
        raise HTTPException(status_code=404, detail="Project not found")
    progress = deps.report_processing_service.get_bulk_upload_progress(project_id, job_id)
    if not progress:
        raise HTTPException(status_code=404, detail="Bulk upload job not found")
    return progress


@router.get("/projects/{project_id}/reports/uploads")
def list_project_uploaded_reports(
    project_id: str,
    auth=Depends(require_permission("reports:read")),
):
    if not deps.tenant_scope_service.get_organization_scoped_project(
        project_id,
        auth.org_id,
        role=auth.role,
        actor_user_id=auth.actor_user_id,
    ):
        raise HTTPException(status_code=404, detail="Project not found")

    return deps.report_processing_service.list_project_uploaded_reports(project_id)


@router.get("/projects/{project_id}/reports/timeline")
def get_project_report_timeline(project_id: str):
    project = deps.project_repository.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return deps.report_processing_service.get_project_report_timeline(project_id)


@router.get("/projects/{project_id}/reports/ai-insights")
def get_project_report_ai_insights(project_id: str, limit: int = 20):
    project = deps.project_repository.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return deps.report_processing_service.get_project_report_ai_insights(project_id, limit=limit)


@router.post("/projects/{project_id}/reports/attachments")
def add_report_attachment(project_id: str, request: ReportAttachmentRequest):
    project = deps.project_repository.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    result = deps.report_processing_service.add_report_attachment(
        project_id=project_id,
        report_id=request.report_id,
        filename=request.filename,
        uploaded_by=request.uploaded_by,
    )
    if result.get("success") is False:
        raise HTTPException(
            status_code=422,
            detail={
                "error_code": result.get("error_code", "INVALID_ATTACHMENT"),
                "message": result.get("error_message", "Attachment payload is invalid"),
            },
        )
    return result


@router.get("/projects/{project_id}/reports/{report_id}/attachments")
def list_report_attachments(project_id: str, report_id: str):
    project = deps.project_repository.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    attachments = deps.report_processing_service.list_report_attachments(report_id)
    return {"project_id": project_id, "report_id": report_id, "attachments": attachments}


@router.delete("/projects/{project_id}/reports/{report_id}/attachments/{attachment_id}")
def delete_report_attachment(project_id: str, report_id: str, attachment_id: str):
    project = deps.project_repository.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    deleted = deps.report_processing_service.delete_report_attachment(
        project_id=project_id,
        report_id=report_id,
        attachment_id=attachment_id,
    )
    if not deleted:
        raise HTTPException(status_code=404, detail="Attachment not found")
    return {"deleted": True, "attachment_id": attachment_id}


@router.get(
    "/projects/{project_id}/reports/{report_id}/delete-eligibility"
)
def get_weekly_report_delete_eligibility(
    project_id: str,
    report_id: str,
    auth=Depends(require_permission("reports:read")),
):
    project = deps.tenant_scope_service.get_organization_scoped_project(
        project_id,
        auth.org_id,
        role=auth.role,
        actor_user_id=auth.actor_user_id,
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return deps.report_deletion_service.check_weekly_report_deletable(
        organization_id=auth.org_id,
        project_id=project_id,
        report_id=report_id,
    )


@router.delete("/projects/{project_id}/reports/{report_id}")
def delete_weekly_report(
    project_id: str,
    report_id: str,
    auth=Depends(require_permission("reports:write")),
):
    project = deps.tenant_scope_service.get_organization_scoped_project(
        project_id,
        auth.org_id,
        role=auth.role,
        actor_user_id=auth.actor_user_id,
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return deps.report_deletion_service.delete_weekly_report(
        organization_id=auth.org_id,
        project_id=project_id,
        report_id=report_id,
        actor_id=auth.user_id,
    )


@router.patch("/projects/{project_id}/reports/{report_id}/tags")
def update_report_tags(project_id: str, report_id: str, request: ReportTagsRequest):
    project = deps.project_repository.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return deps.report_processing_service.update_report_tags(project_id, report_id, request.tags)


@router.get("/projects/{project_id}/reports/{report_id}/tags")
def list_report_tags(project_id: str, report_id: str):
    project = deps.project_repository.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"project_id": project_id, "report_id": report_id, "tags": deps.report_processing_service.list_report_tags(report_id)}


@router.get("/projects/{project_id}/reports/search")
def search_reports(project_id: str, q: str | None = None, tag: str | None = None, classification: str | None = None, limit: int = 20):
    project = deps.project_repository.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if q is None and tag and not classification:
        return deps.report_processing_service.search_reports_by_tag(project_id, tag)
    return deps.report_processing_service.search_reports(
        project_id,
        query=q,
        tag=tag,
        classification=classification,
        limit=limit,
    )


@router.get("/projects/{project_id}/reports/index")
def list_project_report_index(project_id: str):
    project = deps.project_repository.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return deps.report_processing_service.list_project_index_entries(project_id)


@router.get("/projects/{project_id}/reports/{report_id}/index")
def get_report_index_entry(project_id: str, report_id: str):
    project = deps.project_repository.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    entry = deps.report_processing_service.get_report_index_entry(report_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Report index not found")
    if entry.get("project_id") != project_id:
        raise HTTPException(status_code=404, detail="Report index not found")
    return entry


@router.get("/projects/{project_id}/timeline")
def get_project_timeline(project_id: str):
    timeline = deps.project_service.get_project_timeline(project_id)
    if not timeline:
        raise HTTPException(status_code=404, detail="Project not found")
    return timeline


@router.get("/projects/{project_id}/workspace")
def get_project_workspace(
    project_id: str,
    auth=Depends(require_permission("projects:read")),
):
    if not deps.tenant_scope_service.get_organization_scoped_project(
        project_id,
        auth.org_id,
        role=auth.role,
        actor_user_id=auth.actor_user_id,
    ):
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    workspace = (
        deps.project_workspace_service
        .get_workspace(project_id)
    )

    if not workspace.get("project"):
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    return workspace


@router.get("/projects/{project_id}/workspace/activities")
def list_workspace_activities(
    project_id: str,
    activity_type: str | None = None,
    actor_id: str | None = None,
    search: str | None = None,
    before: str | None = None,
    limit: int = 50,
):
    project = deps.project_repository.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return deps.workspace_activity_service.list_activities(
        project_id=project_id,
        activity_type=activity_type,
        actor_id=actor_id,
        search=search,
        before=before,
        limit=limit,
    )


@router.post("/projects/{project_id}/workspace/activities")
async def create_workspace_activity(project_id: str, request: WorkspaceActivityCreateRequest):
    project = deps.project_repository.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    activity = deps.workspace_activity_service.create_activity(
        project_id=project_id,
        activity_type=request.activity_type,
        title=request.title,
        description=request.description,
        metadata=request.metadata,
        actor_id=request.actor_id,
    )
    await conn_mgrs.workspace_connection_manager.broadcast_activity(project_id, activity)
    return activity


@router.websocket("/projects/{project_id}/workspace/stream")
async def stream_workspace_activity(project_id: str, websocket: WebSocket):
    await conn_mgrs.workspace_connection_manager.connect(project_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        conn_mgrs.workspace_connection_manager.disconnect(project_id, websocket)


@router.get("/projects/{project_id}/workspace/activities/search")
def search_workspace_activities(project_id: str, q: str, limit: int = 50):
    project = deps.project_repository.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return deps.workspace_activity_service.list_activities(
        project_id=project_id,
        search=q,
        limit=limit,
    )


@router.get("/projects/{project_id}/workspace/feed")
def get_workspace_dynamic_feed(project_id: str, since: str | None = None, limit: int = 50):
    project = deps.project_repository.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return deps.workspace_activity_service.list_activities(
        project_id=project_id,
        before=since,
        limit=limit,
    )


@router.get("/projects/{project_id}/workspace/live-operational-feed")
def get_live_operational_feed(project_id: str, limit: int = 20):
    project = deps.project_repository.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    feed = deps.workspace_activity_service.list_activities(project_id=project_id, limit=limit * 3)
    activities = [
        item
        for item in feed["activities"]
        if "ACTION" in item.get("activity_type", "")
        or "ESCALATION" in item.get("activity_type", "")
        or "OPERATIONAL" in item.get("activity_type", "")
    ][:limit]
    return {
        "project_id": project_id,
        "total": len(activities),
        "activities": activities,
    }


@router.get("/projects/{project_id}/workspace/analytics")
def get_workspace_analytics(project_id: str):
    project = deps.project_repository.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return deps.workspace_activity_service.get_analytics(project_id)


@router.get("/projects/{project_id}/workspace/grouped")
def get_grouped_workspace_activities(project_id: str, group_by: str = "activity_type"):
    project = deps.project_repository.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return deps.workspace_activity_service.group_activities(project_id, group_by=group_by)


@router.get("/projects/{project_id}/workspace/layout")
def get_workspace_layout(project_id: str, auth_context=Depends(get_auth_context)):
    project = deps.project_repository.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return deps.workspace_activity_service.get_layout(project_id, auth_context.actor_user_id)


@router.put("/projects/{project_id}/workspace/layout")
def save_workspace_layout(project_id: str, request: WorkspaceLayoutRequest, auth_context=Depends(get_auth_context)):
    project = deps.project_repository.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return deps.workspace_activity_service.save_layout(project_id, auth_context.actor_user_id, request.layout)


@router.get("/projects/{project_id}/workspace/widgets")
def get_workspace_widgets(project_id: str, auth_context=Depends(get_auth_context)):
    project = deps.project_repository.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return deps.workspace_activity_service.get_widgets(project_id, auth_context.actor_user_id)


@router.put("/projects/{project_id}/workspace/widgets")
def save_workspace_widgets(project_id: str, request: WorkspaceWidgetsRequest, auth_context=Depends(get_auth_context)):
    project = deps.project_repository.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return deps.workspace_activity_service.save_widgets(project_id, auth_context.actor_user_id, request.widgets)


@router.get("/projects/{project_id}/workspace/permissions")
def get_workspace_permissions(project_id: str, auth_context=Depends(get_auth_context)):
    project = deps.project_repository.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    can_edit = auth_context.role in {"SUPERVISOR", "MANAGER", "ADMIN", "PLATFORM_ADMIN"}
    return {
        "project_id": project_id,
        "user_id": auth_context.actor_user_id,
        "role": auth_context.role,
        "permissions": {
            "can_view": True,
            "can_edit_layout": can_edit,
            "can_customize_widgets": can_edit,
            "can_create_activity": can_edit,
        },
    }


@router.get("/projects/{project_id}/exceptions")
def get_project_exceptions(project_id: str):

    return (
        deps.operational_action_repository
        .get_exceptions_by_project(project_id)
    )


@router.get("/projects/{project_id}/actions/priorities")
def get_action_priorities(project_id: str):
    project = deps.project_repository.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return deps.operational_action_service.get_action_priorities(project_id)


@router.get("/projects/{project_id}/actions/dependency-graph")
def get_action_dependency_graph(project_id: str):
    project = deps.project_repository.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return deps.operational_action_service.get_dependency_graph(project_id)


@router.post("/projects/{project_id}/actions/recurring")
def create_recurring_action(project_id: str, request: ActionRecurringRequest):
    project = deps.project_repository.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return deps.operational_action_service.create_recurring_action(
        project_id=project_id,
        title=request.title,
        recurrence_rule=request.recurrence_rule,
        created_by=request.created_by,
    )


@router.get("/projects/{project_id}/actions/recurring")
def list_recurring_actions(project_id: str):
    project = deps.project_repository.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return deps.operational_action_service.list_recurring_actions(project_id)


@router.post("/projects/{project_id}/actions/bulk")
def bulk_create_actions(project_id: str, request: ActionBulkRequest):
    project = deps.project_repository.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return deps.operational_action_service.bulk_create_actions(project_id, request.actions)


@router.post("/projects/{project_id}/actions/{action_id}/attachments")
def add_action_attachment(project_id: str, action_id: str, request: ActionAttachmentRequest):
    project = deps.project_repository.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return deps.operational_action_service.add_attachment(action_id, request.filename, request.uploaded_by)


@router.get("/projects/{project_id}/actions/{action_id}/attachments")
def list_action_attachments(project_id: str, action_id: str):
    project = deps.project_repository.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"attachments": deps.operational_action_service.list_attachments(action_id)}


@router.delete("/projects/{project_id}/actions/{action_id}/attachments/{attachment_id}")
def delete_action_attachment(project_id: str, action_id: str, attachment_id: str):
    project = deps.project_repository.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    deleted = deps.operational_action_service.delete_attachment(action_id, attachment_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Attachment not found")
    return {"deleted": True}


@router.post("/projects/{project_id}/actions/{action_id}/notifications")
def create_action_notification(project_id: str, action_id: str, request: ActionNotificationRequest):
    project = deps.project_repository.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return deps.operational_action_service.create_notification(
        action_id=action_id,
        recipient_id=request.recipient_id,
        message=request.message,
        channel=request.channel,
    )


@router.get("/projects/{project_id}/actions/{action_id}/notifications")
def list_action_notifications(project_id: str, action_id: str):
    project = deps.project_repository.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"notifications": deps.operational_action_service.list_notifications(action_id)}


@router.get("/projects/{project_id}/actions/analytics")
def get_action_analytics(project_id: str):
    project = deps.project_repository.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return deps.operational_action_service.get_action_analytics(project_id)


@router.post("/projects/{project_id}/actions/{action_id}/comments")
def add_action_comment(project_id: str, action_id: str, request: ActionCommentRequest):
    project = deps.project_repository.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return deps.operational_action_service.add_comment(action_id, request.comment, request.created_by)


@router.get("/projects/{project_id}/actions/{action_id}/comments")
def list_action_comments(project_id: str, action_id: str):
    project = deps.project_repository.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"comments": deps.operational_action_service.list_comments(action_id)}


@router.get("/projects/{project_id}/actions/{action_id}/history")
def get_action_history(project_id: str, action_id: str):
    project = deps.project_repository.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"history": deps.operational_action_service.get_history(action_id)}


@router.get("/projects/{project_id}/actions/sla")
def get_action_sla_dashboard(project_id: str):
    project = deps.project_repository.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return deps.operational_action_service.get_sla_dashboard(project_id)


@router.post("/projects/{project_id}/actions/{action_id}/retry")
def retry_action(project_id: str, action_id: str, request: ActionRetryRequest):
    project = deps.project_repository.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return deps.operational_action_service.retry_action(action_id, request.reason)


@router.patch("/projects/{project_id}/actions/{action_id}/owner")
def set_action_owner(project_id: str, action_id: str, request: ActionOwnerRequest):
    project = deps.project_repository.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return deps.operational_action_service.set_owner(action_id, request.owner_id)


@router.post("/projects/{project_id}/actions/{action_id}/escalate")
def escalate_action_with_hierarchy(project_id: str, action_id: str, request: ActionEscalationRequest):
    project = deps.project_repository.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return deps.operational_action_service.escalate_with_hierarchy(action_id, request.level, request.reason)


@router.post("/projects/{project_id}/actions/ai-generate")
def generate_ai_actions(project_id: str, request: ActionAIGenerationRequest):
    project = deps.project_repository.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return deps.operational_action_service.generate_ai_actions(project_id, request.context)


@router.post("/projects/{project_id}/actions/templates")
def create_action_template(project_id: str, request: ActionTemplateRequest):
    project = deps.project_repository.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return deps.operational_action_service.create_template(
        project_id=project_id,
        name=request.name,
        title=request.title,
        description=request.description,
        category=request.category,
    )


@router.get("/projects/{project_id}/actions/templates")
def list_action_templates(project_id: str):
    project = deps.project_repository.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return deps.operational_action_service.list_templates(project_id)


@router.post("/projects/{project_id}/actions/templates/{template_id}/apply")
def apply_action_template(project_id: str, template_id: str, request: ActionTemplateApplyRequest):
    project = deps.project_repository.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    payload = deps.operational_action_service.apply_template(project_id, template_id, request.created_by)
    if not payload:
        raise HTTPException(status_code=404, detail="Action template not found")
    return payload


@router.patch("/projects/{project_id}/actions/{action_id}/category")
def categorize_action(project_id: str, action_id: str, request: ActionCategoryRequest):
    project = deps.project_repository.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    payload = deps.operational_action_service.categorize_action(action_id, request.category)
    if not payload:
        raise HTTPException(status_code=404, detail="Action not found")
    return payload


@router.get("/projects/{project_id}/operational-summary")
def get_project_operational_summary(project_id: str):

    return (
        deps.operational_summary_service
        .generate_project_summary(project_id)
    )


