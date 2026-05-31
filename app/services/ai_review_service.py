from app.repositories.ai_interpretation_repository import (
    AIInterpretationRepository
)
from datetime import UTC, datetime

from app.repositories.operational_action_repository import (
    OperationalActionRepository
)
from app.schemas.operational_action import (
    OperationalAction,
)
from app.repositories.ai_log_repository import (
    AILogRepository,
)
from app.services.approval_service import (
    ApprovalService,
)


class AIReviewService:

    def __init__(self):

        self.repository = (
            AIInterpretationRepository()
        )

        self.operational_repository = (
            OperationalActionRepository()
        )
        self.audit_repository = (
            AILogRepository()
        )
        self.approval_service = (
            ApprovalService()
        )

    def get_pending_reviews(self):

        return (
            self.repository
            .get_pending_reviews()
        )

    def approve_review(
        self,
        interpretation_id: str,
        reviewed_by: str,
        review_notes: str
    ):

        approved_interpretation = (
            self.repository
            .approve_interpretation(
                interpretation_id=
                    interpretation_id,

                reviewed_by=
                    reviewed_by,

                review_notes=
                    review_notes,
            )
        )

        created_action = (
            self.operational_repository
            .create_action(
                OperationalAction(
                    interpretation_id=
                        interpretation_id,

                    action_type=
                        "ESCALATION",

                    title=
                        approved_interpretation[
                            "recommended_action"
                        ],

                    description=
                        approved_interpretation[
                            "business_impact"
                        ],

                    status=
                        "OPEN",
                )
            )
        )
        self._write_audit_log(
            interpretation_id=
                interpretation_id,
            event_type=
                "REVIEW_APPROVED",
            actor=
                reviewed_by,
            details={
                "review_notes": review_notes,
            },
        )

        return {
            "approved_interpretation":
                approved_interpretation,

            "created_action":
                created_action,
        }

    def reject_review(
        self,
        interpretation_id: str,
        reviewed_by: str,
        review_notes: str | None = None,
    ):

        rejected = (
            self.repository
            .reject_interpretation(
                interpretation_id=
                    interpretation_id,
                reviewed_by=
                    reviewed_by,
                review_notes=
                    review_notes,
            )
        )

        if not rejected:
            return None

        self._write_audit_log(
            interpretation_id=
                interpretation_id,
            event_type=
                "REVIEW_REJECTED",
            actor=
                reviewed_by,
            details={
                "review_notes": review_notes,
            },
        )

        return rejected

    def get_reviews_by_project(
        self,
        project_id: str
    ):

        return (
            self.repository
            .get_reviews_by_project(
                project_id
            )
        )

    def assign_reviewer(
        self,
        interpretation_id: str,
        reviewer_id: str,
    ):
        assignment = (
            self.repository
            .assign_reviewer(
                interpretation_id=
                    interpretation_id,
                reviewer_id=
                    reviewer_id,
            )
        )

        if assignment:
            self._write_audit_log(
                interpretation_id=
                    interpretation_id,
                event_type=
                    "REVIEW_ASSIGNED",
                actor=
                    reviewer_id,
                details={
                    "assigned_reviewer": reviewer_id,
                },
            )

        return assignment

    def get_review_confidence(
        self,
        interpretation_id: str,
    ):
        review = (
            self.repository
            .get_review_by_id(
                interpretation_id
            )
        )

        if not review:
            return None

        recommended_action = (
            review.get("recommended_action")
            or ""
        )

        business_impact = (
            review.get("business_impact")
            or ""
        )

        raw_response = (
            review.get("raw_response")
            or ""
        )

        score = 40

        if len(recommended_action.strip()) >= 20:
            score += 25
        elif recommended_action.strip():
            score += 10

        if len(business_impact.strip()) >= 20:
            score += 20
        elif business_impact.strip():
            score += 10

        if "{" in raw_response and "}" in raw_response:
            score += 15

        model_name = (
            review.get("model_name")
            or ""
        )

        if model_name:
            score += 5

        score = max(0, min(score, 100))

        return {
            "interpretation_id":
                interpretation_id,
            "confidence_score":
                score,
            "confidence_level":
                self._get_confidence_level(
                    score
                ),
            "factors": {
                "recommended_action_length":
                    len(recommended_action),
                "business_impact_length":
                    len(business_impact),
                "has_structured_raw_response":
                    ("{" in raw_response and "}" in raw_response),
                "model_name":
                    model_name or None,
            },
        }

    def apply_human_override(
        self,
        interpretation_id: str,
        overridden_by: str,
        override_reason: str,
    ):
        override_payload = (
            self.repository
            .apply_human_override(
                interpretation_id=
                    interpretation_id,
                overridden_by=
                    overridden_by,
                override_reason=
                    override_reason,
            )
        )

        if override_payload:
            self._write_audit_log(
                interpretation_id=
                    interpretation_id,
                event_type=
                    "REVIEW_OVERRIDDEN",
                actor=
                    overridden_by,
                details={
                    "override_reason": override_reason,
                },
            )

        return override_payload

    def get_review_explainability(
        self,
        interpretation_id: str,
    ):
        review = (
            self.repository
            .get_review_by_id(
                interpretation_id
            )
        )

        if not review:
            return None

        business_impact = (
            review.get("business_impact")
            or ""
        )
        tenant_risk = (
            review.get("tenant_risk")
            or ""
        )
        recommended_action = (
            review.get("recommended_action")
            or ""
        )
        raw_response = (
            review.get("raw_response")
            or ""
        )

        explanation_factors = []

        if business_impact.strip():
            explanation_factors.append({
                "factor":
                    "business_impact",
                "summary":
                    business_impact,
                "weight":
                    0.4,
            })

        if tenant_risk.strip():
            explanation_factors.append({
                "factor":
                    "tenant_risk",
                "summary":
                    tenant_risk,
                "weight":
                    0.3,
            })

        if recommended_action.strip():
            explanation_factors.append({
                "factor":
                    "recommended_action",
                "summary":
                    recommended_action,
                "weight":
                    0.2,
            })

        if raw_response.strip():
            preview = raw_response[:250]
            explanation_factors.append({
                "factor":
                    "raw_model_output",
                "summary":
                    preview,
                "weight":
                    0.1,
            })

        return {
            "interpretation_id":
                interpretation_id,
            "model_name":
                review.get("model_name"),
            "review_status":
                review.get("review_status"),
            "explanation_factors":
                explanation_factors,
            "explanation_version":
                "v1",
        }

    def get_review_dashboard(
        self,
        recent_limit: int = 20,
    ):
        all_reviews = (
            self.repository
            .get_all_reviews()
        )

        pending_reviews = [
            review
            for review in all_reviews
            if review.get("review_status") == "PENDING"
        ]

        approved_reviews = [
            review
            for review in all_reviews
            if review.get("review_status") == "APPROVED"
        ]

        rejected_reviews = [
            review
            for review in all_reviews
            if review.get("review_status") == "REJECTED"
        ]

        overdue_pending_reviews = [
            review
            for review in pending_reviews
            if self._is_review_overdue(
                review.get("created_at")
            )
        ]

        sorted_reviews = sorted(
            all_reviews,
            key=lambda item: (
                item.get("created_at")
                or ""
            ),
            reverse=True,
        )

        return {
            "total_reviews":
                len(all_reviews),
            "pending_reviews":
                len(pending_reviews),
            "approved_reviews":
                len(approved_reviews),
            "rejected_reviews":
                len(rejected_reviews),
            "pending_overdue_reviews":
                len(overdue_pending_reviews),
            "recent_reviews":
                sorted_reviews[:recent_limit],
        }

    def _is_review_overdue(
        self,
        created_at: str | None,
    ) -> bool:
        created_at_dt = (
            self._parse_iso_datetime(
                created_at
            )
        )

        if not created_at_dt:
            return False

        now = (
            datetime
            .now(UTC)
        )

        return (
            now - created_at_dt
        ).total_seconds() > (48 * 3600)

    def get_review_sla_tracking(
        self,
        target_hours: int = 48,
    ):
        all_reviews = (
            self.repository
            .get_all_reviews()
        )

        pending_reviews = [
            review
            for review in all_reviews
            if review.get("review_status") == "PENDING"
        ]

        breached_reviews = []
        healthy_reviews = []

        now = (
            datetime
            .now(UTC)
        )

        for review in pending_reviews:
            created_at = (
                self._parse_iso_datetime(
                    review.get("created_at")
                )
            )

            if not created_at:
                healthy_reviews.append(review)
                continue

            age_hours = (
                now - created_at
            ).total_seconds() / 3600

            if age_hours > target_hours:
                breached_reviews.append(review)
            else:
                healthy_reviews.append(review)

        total_pending = len(pending_reviews)
        breached = len(breached_reviews)

        return {
            "target_hours":
                target_hours,
            "total_pending_reviews":
                total_pending,
            "within_sla_reviews":
                len(healthy_reviews),
            "breached_reviews":
                breached,
            "breach_rate":
                (
                    round((breached / total_pending) * 100, 2)
                    if total_pending > 0
                    else 0.0
                ),
            "breached_review_ids":
                [
                    review.get("id")
                    for review in breached_reviews
                    if review.get("id")
                ],
        }

    def get_review_analytics(
        self,
    ):
        all_reviews = (
            self.repository
            .get_all_reviews()
        )

        total_reviews = len(all_reviews)

        status_breakdown: dict[str, int] = {}
        reviewer_breakdown: dict[str, int] = {}
        model_breakdown: dict[str, int] = {}
        confidence_bucket_breakdown = {
            "low": 0,
            "medium": 0,
            "high": 0,
        }

        approval_cycle_hours: list[float] = []

        for review in all_reviews:
            status = (
                review.get("review_status")
                or "UNKNOWN"
            )
            status_breakdown[status] = (
                status_breakdown.get(status, 0) + 1
            )

            reviewer = (
                review.get("reviewed_by")
                or review.get("assigned_reviewer")
            )
            if reviewer:
                reviewer_breakdown[reviewer] = (
                    reviewer_breakdown.get(reviewer, 0) + 1
                )

            model_name = (
                review.get("model_name")
                or "UNKNOWN"
            )
            model_breakdown[model_name] = (
                model_breakdown.get(model_name, 0) + 1
            )

            confidence_payload = (
                self.get_review_confidence(
                    review.get("id", "")
                )
                if review.get("id")
                else None
            )
            score = (
                confidence_payload.get("confidence_score")
                if confidence_payload
                else None
            )

            if score is not None and score < 50:
                confidence_bucket_breakdown["low"] += 1
            elif score is not None and score < 75:
                confidence_bucket_breakdown["medium"] += 1
            elif score is not None:
                confidence_bucket_breakdown["high"] += 1

            created_at = (
                self._parse_iso_datetime(
                    review.get("created_at")
                )
            )
            reviewed_at = (
                self._parse_iso_datetime(
                    review.get("reviewed_at")
                )
            )
            if created_at and reviewed_at:
                cycle_hours = (
                    reviewed_at - created_at
                ).total_seconds() / 3600
                if cycle_hours >= 0:
                    approval_cycle_hours.append(cycle_hours)

        avg_cycle_hours = (
            round(
                sum(approval_cycle_hours) /
                len(approval_cycle_hours),
                2,
            )
            if approval_cycle_hours
            else 0.0
        )

        return {
            "total_reviews":
                total_reviews,
            "status_breakdown":
                status_breakdown,
            "reviewer_breakdown":
                reviewer_breakdown,
            "model_breakdown":
                model_breakdown,
            "confidence_bucket_breakdown":
                confidence_bucket_breakdown,
            "avg_approval_cycle_hours":
                avg_cycle_hours,
            "completed_review_cycles":
                len(approval_cycle_hours),
        }

    def get_review_audit_logs(
        self,
        interpretation_id: str,
    ):
        review = (
            self.repository
            .get_review_by_id(
                interpretation_id
            )
        )

        if not review:
            return None

        audit_repository = getattr(
            self,
            "audit_repository",
            None
        )

        if not audit_repository:
            return {
                "interpretation_id": interpretation_id,
                "total_events": 0,
                "events": [],
            }

        rows = (
            audit_repository
            .list_review_audit_logs(
                interpretation_id
            )
        )

        events = [
            {
                "event_type":
                    row.get("prompt"),
                "actor":
                    row.get("response"),
                "created_at":
                    row.get("created_at"),
                "raw":
                    row,
            }
            for row in rows
        ]

        return {
            "interpretation_id":
                interpretation_id,
            "review_status":
                review.get("review_status"),
            "total_events":
                len(events),
            "events":
                events,
        }

    def run_review_escalation_logic(
        self,
        interpretation_id: str,
        force: bool = False,
    ):
        review = (
            self.repository
            .get_review_by_id(
                interpretation_id
            )
        )

        if not review:
            return None

        confidence_payload = (
            self.get_review_confidence(
                interpretation_id
            )
        )
        confidence_score = (
            confidence_payload.get("confidence_score")
            if confidence_payload
            else 0
        )

        created_at = (
            self._parse_iso_datetime(
                review.get("created_at")
            )
        )
        age_hours = 0.0
        if created_at:
            age_hours = (
                datetime.now(UTC) - created_at
            ).total_seconds() / 3600

        reasons: list[str] = []

        if force:
            reasons.append("FORCED_ESCALATION")

        if review.get("review_status") == "OVERRIDDEN":
            reasons.append("HUMAN_OVERRIDE_REQUIRES_FOLLOWUP")

        if confidence_score < 60:
            reasons.append("LOW_CONFIDENCE")

        if age_hours > 48:
            reasons.append("SLA_BREACH")

        should_escalate = len(reasons) > 0

        existing_open_action = (
            self.operational_repository
            .get_open_action_by_interpretation_id(
                interpretation_id
            )
        )

        created_action = None
        if should_escalate and not existing_open_action:
            created_action = (
                self.operational_repository
                .create_action(
                    OperationalAction(
                        interpretation_id=
                            interpretation_id,
                        action_type=
                            "ESCALATION",
                        title=
                            (
                                review.get("recommended_action")
                                or "Review escalation required"
                            ),
                        description=
                            (
                                review.get("business_impact")
                                or "Escalation triggered by policy"
                            ),
                        status=
                            "OPEN",
                    )
                )
            )

            self._write_audit_log(
                interpretation_id=
                    interpretation_id,
                event_type=
                    "REVIEW_ESCALATED",
                details={
                    "reasons": reasons,
                    "confidence_score": confidence_score,
                    "age_hours": round(age_hours, 2),
                },
            )

        return {
            "interpretation_id":
                interpretation_id,
            "should_escalate":
                should_escalate,
            "reasons":
                reasons,
            "confidence_score":
                confidence_score,
            "age_hours":
                round(age_hours, 2),
            "existing_open_action":
                existing_open_action,
            "created_action":
                created_action,
        }

    def review_ai_recommendation(
        self,
        interpretation_id: str,
        decision: str,
        reviewed_by: str,
        review_notes: str | None = None,
    ):
        normalized_decision = (
            decision.strip().upper()
        )
        if normalized_decision not in {
            "APPROVED",
            "REJECTED",
        }:
            raise ValueError(
                "decision must be APPROVED or REJECTED"
            )

        payload = (
            self.repository
            .review_recommendation(
                interpretation_id=
                    interpretation_id,
                decision=
                    normalized_decision,
                reviewed_by=
                    reviewed_by,
                review_notes=
                    review_notes,
            )
        )

        if payload:
            self._write_audit_log(
                interpretation_id=
                    interpretation_id,
                event_type=
                    f"AI_RECOMMENDATION_{normalized_decision}",
                actor=
                    reviewed_by,
                details={
                    "review_notes": review_notes,
                },
            )

        return payload

    def add_review_comment(
        self,
        interpretation_id: str,
        author: str,
        comment: str,
    ):
        review = (
            self.repository
            .get_review_by_id(
                interpretation_id
            )
        )
        if not review:
            return None

        self.audit_repository.create_review_comment(
            interpretation_id=
                interpretation_id,
            author=
                author,
            comment=
                comment,
        )

        self._write_audit_log(
            interpretation_id=
                interpretation_id,
            event_type=
                "REVIEW_COMMENT_ADDED",
            actor=
                author,
            details={
                "comment_preview":
                    comment[:120],
            },
        )

        return {
            "interpretation_id":
                interpretation_id,
            "author":
                author,
            "comment":
                comment,
        }

    def list_review_comments(
        self,
        interpretation_id: str,
    ):
        review = (
            self.repository
            .get_review_by_id(
                interpretation_id
            )
        )
        if not review:
            return None

        rows = (
            self.audit_repository
            .list_review_comments(
                interpretation_id
            )
        )
        comments = [
            {
                "author": row.get("prompt"),
                "comment": row.get("response"),
                "created_at": row.get("created_at"),
            }
            for row in rows
        ]
        return {
            "interpretation_id": interpretation_id,
            "total_comments": len(comments),
            "comments": comments,
        }

    def send_review_notification(
        self,
        interpretation_id: str,
        recipient_id: str,
        message: str,
        channel: str = "IN_APP",
    ):
        review = (
            self.repository
            .get_review_by_id(
                interpretation_id
            )
        )
        if not review:
            return None

        self.audit_repository.create_review_notification(
            interpretation_id=
                interpretation_id,
            recipient_id=
                recipient_id,
            message=
                message,
            channel=
                channel,
        )

        self._write_audit_log(
            interpretation_id=
                interpretation_id,
            event_type=
                "REVIEW_NOTIFICATION_SENT",
            actor=
                recipient_id,
            details={
                "channel": channel,
                "message_preview": message[:120],
            },
        )

        return {
            "interpretation_id":
                interpretation_id,
            "recipient_id":
                recipient_id,
            "channel":
                channel,
            "message":
                message,
        }

    def list_review_notifications(
        self,
        interpretation_id: str,
    ):
        review = (
            self.repository
            .get_review_by_id(
                interpretation_id
            )
        )
        if not review:
            return None

        rows = (
            self.audit_repository
            .list_review_notifications(
                interpretation_id
            )
        )
        notifications = []
        for row in rows:
            raw = row.get("response") or ""
            if ":" in raw:
                channel, message = raw.split(":", 1)
            else:
                channel, message = "IN_APP", raw
            notifications.append({
                "recipient_id": row.get("prompt"),
                "channel": channel,
                "message": message,
                "created_at": row.get("created_at"),
            })

        return {
            "interpretation_id": interpretation_id,
            "total_notifications": len(notifications),
            "notifications": notifications,
        }

    def create_manual_approval_workflow(
        self,
        interpretation_id: str,
        requested_by: str,
        notes: str | None = None,
    ):
        review = (
            self.repository
            .get_review_by_id(
                interpretation_id
            )
        )
        if not review:
            return None

        approval_request = (
            self.approval_service
            .create_request(
                workflow_type=
                    "REVIEW_MANUAL_APPROVAL",
                payload={
                    "interpretation_id": interpretation_id,
                    "requested_by": requested_by,
                    "notes": notes,
                },
            )
        )

        self._write_audit_log(
            interpretation_id=
                interpretation_id,
            event_type=
                "REVIEW_MANUAL_APPROVAL_REQUESTED",
            actor=
                requested_by,
            details={
                "approval_id":
                    approval_request.get("id"),
                "notes":
                    notes,
            },
        )

        return approval_request

    def _parse_iso_datetime(
        self,
        value: str | None,
    ) -> datetime | None:
        if not value:
            return None

        try:
            return (
                datetime
                .fromisoformat(
                    value.replace("Z", "+00:00")
                )
            )
        except ValueError:
            return None

    def _get_confidence_level(
        self,
        score: int,
    ) -> str:
        if score >= 85:
            return "VERY_HIGH"

        if score >= 70:
            return "HIGH"

        if score >= 50:
            return "MEDIUM"

        return "LOW"

    def _write_audit_log(
        self,
        interpretation_id: str,
        event_type: str,
        actor: str | None = None,
        details: dict | None = None,
    ):
        audit_repository = getattr(
            self,
            "audit_repository",
            None
        )

        if not audit_repository:
            return

        try:
            audit_repository.create_review_audit_log(
                interpretation_id=
                    interpretation_id,
                event_type=
                    event_type,
                actor=
                    actor,
                details=
                    details,
            )
        except Exception:
            # Audit logging must never break review flow.
            return