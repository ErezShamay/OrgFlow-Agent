"""Review routes.

Extracted from app/main.py during the 2026-07 architecture-modularization
refactor. Shared service singletons live in app/dependencies.py; shared
request models live in app/schemas/api_requests.py.
"""
from __future__ import annotations

from app.auth import require_permission
from fastapi import (
    Depends,
    HTTPException,
)

from fastapi import APIRouter
import app.dependencies as deps
from app.schemas.api_requests import (
    ApproveReviewRequest,
    AssignReviewerRequest,
    HumanOverrideRequest,
    ManualApprovalRequest,
    RecommendationReviewRequest,
    RejectReviewRequest,
    ReviewCommentRequest,
    ReviewNotificationRequest,
)


router = APIRouter()


@router.get("/reviews/pending")
def get_pending_reviews(
    auth=Depends(require_permission("projects:read")),
):

    return (
        deps.ai_review_service
        .get_pending_reviews(
            organization_id=auth.org_id,
        )
    )


@router.get("/reviews/dashboard")
def get_review_dashboard(
    limit: int = 20,
    auth=Depends(require_permission("projects:read")),
):

    return (
        deps.ai_review_service
        .get_review_dashboard(
            recent_limit=limit,
            organization_id=auth.org_id,
        )
    )


@router.post("/reviews/{interpretation_id}/assign")
def assign_review_reviewer(
    interpretation_id: str,
    request: AssignReviewerRequest,
):
    assignment = (
        deps.ai_review_service
        .assign_reviewer(
            interpretation_id=
                interpretation_id,
            reviewer_id=
                request.reviewer_id,
        )
    )

    if not assignment:
        raise HTTPException(
            status_code=404,
            detail="Review not found"
        )

    return assignment


@router.post("/reviews/{interpretation_id}/approve")
async def approve_review(
    interpretation_id: str,
    request: ApproveReviewRequest,
):
    payload = (
        deps.ai_review_service
        .approve_review(
            interpretation_id=
                interpretation_id,
            reviewed_by=
                request.reviewed_by,
            review_notes=
                request.review_notes or "",
        )
    )

    if not payload:
        raise HTTPException(
            status_code=404,
            detail="Review not found"
        )

    created_action = payload.get("created_action") or {}
    deps.notification_service.create_notification(
        profile_id=request.reviewed_by,
        title="ביקורת AI אושרה",
        message=(
            f"נוצרה פעולה תפעולית: "
            f"{created_action.get('title', 'פעולה חדשה')}"
        ),
        notification_type="REVIEW_APPROVED",
    )

    return payload


@router.post("/reviews/{interpretation_id}/reject")
def reject_review(
    interpretation_id: str,
    request: RejectReviewRequest,
):
    payload = (
        deps.ai_review_service
        .reject_review(
            interpretation_id=
                interpretation_id,
            reviewed_by=
                request.reviewed_by,
            review_notes=
                request.review_notes,
        )
    )

    if not payload:
        raise HTTPException(
            status_code=404,
            detail="Review not found"
        )

    return payload


@router.get("/reviews/sla")
def get_reviews_sla_tracking(target_hours: int = 48):
    return (
        deps.ai_review_service
        .get_review_sla_tracking(
            target_hours=target_hours
        )
    )


@router.get("/reviews/{interpretation_id}/confidence")
def get_review_confidence(
    interpretation_id: str,
):
    confidence_payload = (
        deps.ai_review_service
        .get_review_confidence(
            interpretation_id
        )
    )

    if not confidence_payload:
        raise HTTPException(
            status_code=404,
            detail="Review not found"
        )

    return confidence_payload


@router.post("/reviews/{interpretation_id}/override")
def apply_review_human_override(
    interpretation_id: str,
    request: HumanOverrideRequest,
):
    override_payload = (
        deps.ai_review_service
        .apply_human_override(
            interpretation_id=
                interpretation_id,
            overridden_by=
                request.overridden_by,
            override_reason=
                request.override_reason,
        )
    )

    if not override_payload:
        raise HTTPException(
            status_code=404,
            detail="Review not found"
        )

    return override_payload


@router.get("/reviews/analytics")
def get_review_analytics():
    return (
        deps.ai_review_service
        .get_review_analytics()
    )


@router.get("/reviews/{interpretation_id}/explainability")
def get_review_explainability(
    interpretation_id: str,
):
    explainability_payload = (
        deps.ai_review_service
        .get_review_explainability(
            interpretation_id
        )
    )

    if not explainability_payload:
        raise HTTPException(
            status_code=404,
            detail="Review not found"
        )

    return explainability_payload


@router.get("/reviews/{interpretation_id}/audit-logs")
def get_review_audit_logs(
    interpretation_id: str,
):
    audit_payload = (
        deps.ai_review_service
        .get_review_audit_logs(
            interpretation_id
        )
    )

    if not audit_payload:
        raise HTTPException(
            status_code=404,
            detail="Review not found"
        )

    return audit_payload


@router.post("/reviews/{interpretation_id}/escalate")
def run_review_escalation(
    interpretation_id: str,
    force: bool = False,
):
    escalation_payload = (
        deps.ai_review_service
        .run_review_escalation_logic(
            interpretation_id=
                interpretation_id,
            force=
                force,
        )
    )

    if not escalation_payload:
        raise HTTPException(
            status_code=404,
            detail="Review not found"
        )

    return escalation_payload


@router.post("/reviews/{interpretation_id}/recommendation/review")
def review_ai_recommendation(
    interpretation_id: str,
    request: RecommendationReviewRequest,
):
    try:
        payload = (
            deps.ai_review_service
            .review_ai_recommendation(
                interpretation_id=
                    interpretation_id,
                decision=
                    request.decision,
                reviewed_by=
                    request.reviewed_by,
                review_notes=
                    request.review_notes,
            )
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc)
        ) from exc

    if not payload:
        raise HTTPException(
            status_code=404,
            detail="Review not found"
        )

    return payload


@router.post("/reviews/{interpretation_id}/comments")
def add_review_comment(
    interpretation_id: str,
    request: ReviewCommentRequest,
):
    payload = (
        deps.ai_review_service
        .add_review_comment(
            interpretation_id=
                interpretation_id,
            author=
                request.author,
            comment=
                request.comment,
        )
    )
    if not payload:
        raise HTTPException(
            status_code=404,
            detail="Review not found"
        )
    return payload


@router.get("/reviews/{interpretation_id}/comments")
def list_review_comments(
    interpretation_id: str,
):
    payload = (
        deps.ai_review_service
        .list_review_comments(
            interpretation_id
        )
    )
    if not payload:
        raise HTTPException(
            status_code=404,
            detail="Review not found"
        )
    return payload


@router.post("/reviews/{interpretation_id}/notifications")
def send_review_notification(
    interpretation_id: str,
    request: ReviewNotificationRequest,
):
    payload = (
        deps.ai_review_service
        .send_review_notification(
            interpretation_id=
                interpretation_id,
            recipient_id=
                request.recipient_id,
            message=
                request.message,
            channel=
                request.channel,
        )
    )
    if not payload:
        raise HTTPException(status_code=404, detail="Review not found")
    return payload


@router.get("/reviews/{interpretation_id}/notifications")
def list_review_notifications(
    interpretation_id: str,
):
    payload = (
        deps.ai_review_service
        .list_review_notifications(
            interpretation_id
        )
    )
    if not payload:
        raise HTTPException(status_code=404, detail="Review not found")
    return payload


@router.post("/reviews/{interpretation_id}/manual-approval")
def create_manual_approval_workflow(
    interpretation_id: str,
    request: ManualApprovalRequest,
):
    payload = (
        deps.ai_review_service
        .create_manual_approval_workflow(
            interpretation_id=
                interpretation_id,
            requested_by=
                request.requested_by,
            notes=
                request.notes,
        )
    )
    if not payload:
        raise HTTPException(status_code=404, detail="Review not found")
    return payload


