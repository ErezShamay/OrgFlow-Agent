"""Quality issue routes.

Extracted from app/main.py during the 2026-07 architecture-modularization
refactor. Shared service singletons live in app/dependencies.py; shared
request models live in app/schemas/api_requests.py.
"""
from __future__ import annotations

from app.auth import get_auth_context
from app.schemas.quality_issue import (
    QualityIssue,
    QualityIssueDetailResponse,
    QualityIssueListQuery,
    QualityIssueOrgListResponse,
    QualityIssuePhotoUploadResponse,
    QualityIssueSeverity,
    QualityIssueStatus,
    QualityIssueUpdateRequest,
    parse_quality_issue_row,
)
from fastapi import (
    Depends,
    File,
    Query,
    UploadFile,
)
from fastapi.responses import Response
from typing import Annotated

from fastapi import APIRouter
import app.dependencies as deps


router = APIRouter()


@router.get(
    "/issues",
    response_model=QualityIssueOrgListResponse,
)
def list_organization_quality_issues(
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
    return deps.quality_issue_service.list_organization_issues(
        organization_id=auth.org_id,
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


@router.get(
    "/issues/{issue_id}",
    response_model=QualityIssueDetailResponse,
)
def get_quality_issue_detail(
    issue_id: str,
    auth=Depends(get_auth_context),
):
    return deps.quality_issue_service.get_issue_detail(
        organization_id=auth.org_id,
        issue_id=issue_id,
        actor_role=auth.role,
        actor_user_id=auth.actor_user_id,
    )


@router.patch(
    "/issues/{issue_id}",
    response_model=QualityIssue,
)
def update_quality_issue(
    issue_id: str,
    request: QualityIssueUpdateRequest,
    auth=Depends(get_auth_context),
):
    record = deps.quality_issue_service.update_issue(
        organization_id=auth.org_id,
        issue_id=issue_id,
        request=request,
        actor_role=auth.role,
        actor_id=auth.effective_user_id or auth.user_id,
    )
    return parse_quality_issue_row(record)


@router.post(
    "/issues/{issue_id}/photos",
    response_model=QualityIssuePhotoUploadResponse,
)
async def upload_quality_issue_remediation_photo(
    issue_id: str,
    file: UploadFile = File(...),
    auth=Depends(get_auth_context),
):
    content = await file.read()
    return deps.quality_issue_service.upload_remediation_photo(
        organization_id=auth.org_id,
        issue_id=issue_id,
        content=content,
        content_type=file.content_type,
        filename=file.filename,
        actor_role=auth.role,
    )


@router.get("/issues/{issue_id}/photos/{photo_id}")
def get_quality_issue_photo(
    issue_id: str,
    photo_id: str,
    auth=Depends(get_auth_context),
):
    content, content_type = deps.quality_issue_service.get_issue_photo(
        organization_id=auth.org_id,
        issue_id=issue_id,
        photo_id=photo_id,
        actor_role=auth.role,
    )
    return Response(content=content, media_type=content_type)


