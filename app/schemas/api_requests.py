"""Shared Pydantic request/response models for app/routers/*.py."""
from __future__ import annotations

from app.config.field_report_project_scheme import is_valid_project_scheme
from app.lib.email_validation import (
    require_valid_email,
    validate_optional_email,
)
from app.lib.project_date_validation import validate_project_dates
from pydantic import (
    BaseModel,
    Field,
    field_validator,
    model_validator,
)
from typing import Self


class AgentRequest(
    BaseModel
):

    user_request: str


class ReviewDecisionRequest(
    BaseModel
):

    reviewed_by: str

    review_notes: str | None = None


class AssignActionRequest(
    BaseModel
):

    assigned_to: str


class AssignReviewerRequest(
    BaseModel
):

    reviewer_id: str


class HumanOverrideRequest(
    BaseModel
):

    overridden_by: str
    override_reason: str


class RecommendationReviewRequest(
    BaseModel
):

    reviewed_by: str
    decision: str
    review_notes: str | None = None


class ReviewCommentRequest(
    BaseModel
):
    author: str
    comment: str


class ReviewNotificationRequest(
    BaseModel
):
    recipient_id: str
    message: str
    channel: str = "IN_APP"


class ManualApprovalRequest(
    BaseModel
):
    requested_by: str
    notes: str | None = None


class ExchangeTokenRequest(
    BaseModel
):
    user_id: str
    organization_id: str | None = None


class TenantExtractRequest(BaseModel):
    text: str = Field(..., min_length=1)


class TenantExtractResponse(BaseModel):
    tenants: list[dict]
    error: str | None = None


class ApproveReviewRequest(
    BaseModel
):
    reviewed_by: str
    review_notes: str | None = None


class RejectReviewRequest(
    BaseModel
):
    reviewed_by: str
    review_notes: str | None = None


class ActionAssignRequest(
    BaseModel
):
    assigned_to: str


class CreateProjectRequest(
    BaseModel
):
    project_name: str
    developer_name: str
    contractor_name: str
    lawyer_name: str
    supervisor_name: str
    supervisor_email: str
    organization_id: str | None = None
    owner_id: str | None = None
    tags: list[str] = Field(default_factory=list)
    scheme: str
    developer_pm_name: str
    accompanying_lawyer: str
    architect_name: str
    site_manager_name: str
    city: str
    housing_units_count: int
    floors_count: int
    project_start_date: str
    project_end_date: str
    project_grace_end_date: str
    structure_documentation_date: str
    developer_email: str
    developer_pm_email: str
    site_manager_email: str
    contractor_email: str
    lawyer_email: str
    accompanying_lawyer_email: str
    architect_email: str

    @field_validator("scheme")
    @classmethod
    def validate_scheme(cls, value: str) -> str:
        if not is_valid_project_scheme(value):
            raise ValueError("invalid project scheme")
        return value

    @field_validator("floors_count", "housing_units_count")
    @classmethod
    def validate_positive_counts(cls, value: int) -> int:
        if value < 1:
            raise ValueError("count must be a positive integer")
        return value

    @field_validator(
        "supervisor_email",
        "developer_email",
        "developer_pm_email",
        "site_manager_email",
        "contractor_email",
        "lawyer_email",
        "accompanying_lawyer_email",
        "architect_email",
    )
    @classmethod
    def validate_email_fields(cls, value: str) -> str:
        return require_valid_email(value)

    @field_validator(
        "project_name",
        "developer_name",
        "contractor_name",
        "lawyer_name",
        "supervisor_name",
        "developer_pm_name",
        "accompanying_lawyer",
        "architect_name",
        "site_manager_name",
        "city",
        "project_start_date",
        "project_end_date",
        "project_grace_end_date",
        "structure_documentation_date",
    )
    @classmethod
    def validate_non_empty_text(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("field is required")
        return normalized

    @model_validator(mode="after")
    def validate_project_date_order(self) -> Self:
        validate_project_dates(
            self.project_start_date,
            self.project_end_date,
            self.project_grace_end_date,
        )
        return self


class EditProjectRequest(
    BaseModel
):
    project_name: str | None = None
    developer_name: str | None = None
    contractor_name: str | None = None
    lawyer_name: str | None = None
    supervisor_name: str | None = None
    supervisor_email: str | None = None
    scheme: str | None = None
    developer_pm_name: str | None = None
    accompanying_lawyer: str | None = None
    architect_name: str | None = None
    site_manager_name: str | None = None
    city: str | None = None
    housing_units_count: int | None = None
    floors_count: int | None = None
    project_start_date: str | None = None
    project_end_date: str | None = None
    project_grace_end_date: str | None = None
    structure_documentation_date: str | None = None
    illustration_url: str | None = None
    illustration_source_he: str | None = None
    developer_email: str | None = None
    developer_pm_email: str | None = None
    site_manager_email: str | None = None
    contractor_email: str | None = None
    lawyer_email: str | None = None
    accompanying_lawyer_email: str | None = None
    architect_email: str | None = None

    @field_validator("scheme")
    @classmethod
    def validate_scheme(cls, value: str | None) -> str | None:
        if value is not None and not is_valid_project_scheme(value):
            raise ValueError("invalid project scheme")
        return value

    @field_validator("floors_count", "housing_units_count")
    @classmethod
    def validate_positive_counts(cls, value: int | None) -> int | None:
        if value is not None and value < 1:
            raise ValueError("count must be a positive integer")
        return value

    @field_validator(
        "supervisor_email",
        "developer_email",
        "developer_pm_email",
        "site_manager_email",
        "contractor_email",
        "lawyer_email",
        "accompanying_lawyer_email",
        "architect_email",
        mode="before",
    )
    @classmethod
    def validate_optional_email_fields(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if isinstance(value, str):
            return validate_optional_email(value)
        return value

    @model_validator(mode="after")
    def validate_project_date_order(self) -> Self:
        validate_project_dates(
            self.project_start_date,
            self.project_end_date,
            self.project_grace_end_date,
        )
        return self


class ProjectTagsRequest(
    BaseModel
):
    tags: list[str]


class ProjectOwnerRequest(
    BaseModel
):
    owner_id: str


class ProjectLifecycleRequest(
    BaseModel
):
    lifecycle_phase: str


class DeleteProjectRequest(
    BaseModel
):
    confirm_project_name: str


class ProjectAttachmentRequest(
    BaseModel
):
    filename: str
    uploaded_by: str


class ProjectCommentRequest(
    BaseModel
):
    comment: str
    author: str


class ReportAttachmentRequest(
    BaseModel
):
    report_id: str
    filename: str
    uploaded_by: str


class ReportTagsRequest(
    BaseModel
):
    tags: list[str]


class ActionRecurringRequest(
    BaseModel
):
    title: str
    recurrence_rule: str
    created_by: str


class ActionBulkRequest(
    BaseModel
):
    actions: list[dict]


class ActionAttachmentRequest(
    BaseModel
):
    filename: str
    uploaded_by: str


class ActionNotificationRequest(
    BaseModel
):
    recipient_id: str
    message: str
    channel: str = "IN_APP"


class NotificationCreateRequest(
    BaseModel
):
    title: str
    message: str
    notification_type: str = "GENERAL"
    channel: str = "IN_APP"
    channels: list[str] | None = None
    category: str | None = None
    priority: str = "NORMAL"
    banner: bool = False
    max_attempts: int = 3
    force_fail_channels: list[str] = Field(default_factory=list)


class NotificationReadSyncRequest(
    BaseModel
):
    read_ids: list[str]


class NotificationPreferenceRequest(
    BaseModel
):
    channels: dict[str, bool] = Field(default_factory=dict)
    categories: dict[str, bool] = Field(default_factory=dict)


class NotificationEscalationRequest(
    BaseModel
):
    title: str
    message: str
    escalation_level: str


class ActionCommentRequest(
    BaseModel
):
    comment: str
    created_by: str


class ActionRetryRequest(
    BaseModel
):
    reason: str


class ActionOwnerRequest(
    BaseModel
):
    owner_id: str


class ActionEscalationRequest(
    BaseModel
):
    level: str
    reason: str


class ActionAIGenerationRequest(
    BaseModel
):
    context: str


class ActionTemplateRequest(
    BaseModel
):
    name: str
    title: str
    description: str
    category: str


class ActionTemplateApplyRequest(
    BaseModel
):
    created_by: str


class ActionCategoryRequest(
    BaseModel
):
    category: str


class WorkspaceActivityCreateRequest(
    BaseModel
):
    activity_type: str
    title: str
    description: str | None = None
    metadata: dict = Field(default_factory=dict)
    actor_id: str | None = None


class WorkspaceLayoutRequest(
    BaseModel
):
    layout: dict


class WorkspaceWidgetsRequest(
    BaseModel
):
    widgets: list[dict]


class CrossProjectWorkspaceRequest(
    BaseModel
):
    project_ids: list[str]
    limit: int = 50


class AutomationCronScheduleRequest(
    BaseModel
):
    cron: str
    enabled: bool = True


class AutomationJobStatusRequest(
    BaseModel
):
    enabled: bool


class AutomationQueueRequest(
    BaseModel
):
    job_name: str
    payload: dict = Field(default_factory=dict)
    priority: int = 5
    idempotency_key: str | None = None


class AutomationWorkerProcessRequest(
    BaseModel
):
    worker_id: str = "worker-default"


class AutomationRetryPolicyRequest(
    BaseModel
):
    max_attempts: int
    backoff_seconds: int
    multiplier: int = 2


class AutomationRetryEvaluationRequest(
    BaseModel
):
    attempts: int


class AutomationSchedulerClaimRequest(
    BaseModel
):
    job_name: str
    owner_id: str = "scheduler"
    window_seconds: int = 30


class AutomationGovernanceRequest(
    BaseModel
):
    job_name: str
    payload: dict = Field(default_factory=dict)
    actor: str = "system"


class WorkflowVersionCreateRequest(
    BaseModel
):
    workflow_name: str
    definition: dict = Field(default_factory=dict)
    published_by: str
    activate: bool = True


class WorkflowExecutionLogCreateRequest(
    BaseModel
):
    level: str
    message: str
    context: dict = Field(default_factory=dict)


class DynamicWorkflowBuilderRequest(
    BaseModel
):
    workflow_name: str
    created_by: str
    steps: list[dict]


