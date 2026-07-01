"""Report routes.

Extracted from app/main.py during the 2026-07 architecture-modularization
refactor. Shared service singletons live in app/dependencies.py; shared
request models live in app/schemas/api_requests.py.
"""
from __future__ import annotations

import shutil
import threading
from app.auth import require_permission
from datetime import (
    UTC,
    datetime,
)
from fastapi import (
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
)
from pathlib import Path

from fastapi import APIRouter
import app.dependencies as deps


router = APIRouter()


@router.post("/reports/upload/resolve-project")
async def resolve_report_upload_project(
    file: UploadFile = File(...),
    auth=Depends(require_permission("reports:write")),
):
    upload_dir = Path("tmp_uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S%f")
    target_path = upload_dir / f"{timestamp}_{file.filename or 'report'}"

    with target_path.open("wb") as target_file:
        shutil.copyfileobj(file.file, target_file)

    try:
        return deps.report_upload_project_resolver_service.resolve_from_upload(
            file_path=str(target_path),
            filename=file.filename or target_path.name,
            organization_id=auth.org_id,
            role=auth.role,
            actor_user_id=auth.actor_user_id,
        )
    finally:
        if target_path.exists():
            target_path.unlink()


@router.post("/reports/upload")
async def upload_report(
    project_id: str = Form(...),
    file: UploadFile = File(...),
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

    upload_dir = Path("tmp_uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S%f")
    target_path = upload_dir / f"{timestamp}_{file.filename or 'report'}"

    with target_path.open("wb") as target_file:
        shutil.copyfileobj(file.file, target_file)

    try:
        result = deps.report_processing_service.process_uploaded_report(
            project_id=project_id,
            filename=file.filename or target_path.name,
            file_path=str(target_path),
        )
    except Exception:
        deps.logger.exception(
            "Report upload processing failed",
            extra={"project_id": project_id},
        )
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "REPORT_PROCESSING_FAILED",
                "message": "Report processing failed",
            },
        ) from None
    finally:
        if target_path.exists():
            target_path.unlink()

    if not result.get("success", False):
        raise HTTPException(
            status_code=422,
            detail={
                "error_code": result.get("error_code", "REPORT_PROCESSING_FAILED"),
                "message": result.get("error_message", "Report processing failed"),
            },
        )

    return result


@router.post("/reports/upload/bulk")
async def upload_reports_bulk(
    project_id: str = Form(...),
    files: list[UploadFile] = File(...),
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

    if not files:
        raise HTTPException(status_code=422, detail="At least one file is required")

    upload_dir = Path("tmp_uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)
    uploads: list[dict] = []

    for file in files:
        timestamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S%f")
        target_path = upload_dir / f"{timestamp}_{file.filename or 'report'}"
        with target_path.open("wb") as target_file:
            shutil.copyfileobj(file.file, target_file)
        uploads.append(
            {
                "filename": file.filename or target_path.name,
                "file_path": str(target_path),
            }
        )

    job_id = deps.report_processing_service.start_bulk_upload_job(
        project_id,
        len(uploads),
    )

    def run_bulk_job() -> None:
        try:
            deps.report_processing_service.run_bulk_upload_job(
                job_id,
                project_id,
                uploads,
            )
        finally:
            for item in uploads:
                path = Path(item["file_path"])
                if path.exists():
                    path.unlink()

    threading.Thread(target=run_bulk_job, daemon=True).start()

    progress = deps.report_processing_service.get_bulk_upload_progress(project_id, job_id)
    if not progress:
        raise HTTPException(
            status_code=500,
            detail="Failed to start bulk upload job",
        )
    return progress


