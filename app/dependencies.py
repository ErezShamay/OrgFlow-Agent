"""Shared service/repository singletons for the whole backend.

Single place these objects are instantiated; app/main.py and every
app/routers/*.py module import the specific singletons/constants they
need from here instead of each redefining them. Each singleton also
has a get_<name>() provider for idiomatic FastAPI Depends() injection
in new code.
"""
from __future__ import annotations

from app.agent.orchestrator import Orchestrator
from app.agent.workflow_history import WorkflowHistory
from app.auth import JWTService
from app.config.settings import settings
from app.exceptions import get_logger
from app.repositories.ai_interpretation_repository import AIInterpretationRepository
from app.repositories.operational_action_repository import OperationalActionRepository
from app.repositories.organization_repository import OrganizationRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.weekly_report_repository import WeeklyReportRepository
from app.services.ai_review_service import AIReviewService
from app.services.ai_usage_dashboard_service import AIUsageDashboardService
from app.services.alert_engine_service import AlertEngineService
from app.services.approval_service import ApprovalService
from app.services.auto_recovery_rules_service import AutoRecoveryRulesService
from app.services.automation_control_service import AutomationControlService
from app.services.automation_cron_management_service import AutomationCronManagementService
from app.services.automation_governance_service import AutomationGovernanceService
from app.services.automation_job_queue_service import AutomationJobQueueService
from app.services.automation_monitoring_service import AutomationMonitoringService
from app.services.automation_replay_service import AutomationReplayService
from app.services.automation_retry_policy_service import AutomationRetryPolicyService
from app.services.automation_scheduler_guard_service import AutomationSchedulerGuardService
from app.services.automation_worker_service import AutomationWorkerService
from app.services.circuit_breaker_dashboard_service import CircuitBreakerDashboardService
from app.services.circuit_breaker_reopen_service import CircuitBreakerReopenService
from app.services.circuit_breaker_service import CircuitBreakerService
from app.services.circuit_breaker_threshold_service import CircuitBreakerThresholdService
from app.services.database_hardening_dashboard_service import DatabaseHardeningDashboardService
from app.services.dead_letter_recovery_service import DeadLetterRecoveryService
from app.services.deliverable_reports_service import DeliverableReportsService
from app.services.devops_deployment_dashboard_service import DevopsDeploymentDashboardService
from app.services.dynamic_automation_builder_service import DynamicAutomationBuilderService
from app.services.field_report_finalize_service import FieldReportFinalizeService
from app.services.field_report_module_service import FieldReportModuleService
from app.services.field_report_organization_profile_service import FieldReportOrganizationProfileService
from app.services.field_visit_report_export_service import FieldVisitReportExportService
from app.services.field_visit_report_service import FieldVisitReportService
from app.services.future_ai_features_dashboard_service import FutureAiFeaturesDashboardService
from app.services.notification_service import NotificationService
from app.services.observability_dashboard_service import ObservabilityDashboardService
from app.services.operational_action_service import OperationalActionService
from app.services.operational_summary_service import OperationalSummaryService
from app.services.organization_admin_service import OrganizationAdminService
from app.services.portfolio_insights_service import PortfolioInsightsService
from app.services.portfolio_intelligence_dashboard_service import PortfolioIntelligenceDashboardService
from app.services.portfolio_live_service import PortfolioLiveService
from app.services.product_readiness_dashboard_service import ProductReadinessDashboardService
from app.services.profile_service import ProfileService
from app.services.project_apartment_service import ProjectApartmentService
from app.services.project_deletion_service import ProjectDeletionService
from app.services.project_service import ProjectService
from app.services.project_spatial_bootstrap_service import ProjectSpatialBootstrapService
from app.services.project_supervision_dashboard_service import ProjectSupervisionDashboardService
from app.services.project_template_service import ProjectTemplateService
from app.services.project_workspace_service import ProjectWorkspaceService
from app.services.qc_notification_service import build_qc_notification_service
from app.services.quality_issue_service import QualityIssueService
from app.services.recovery_dashboard_service import RecoveryDashboardService
from app.services.recovery_orchestration_service import RecoveryOrchestrationService
from app.services.report_deletion_service import ReportDeletionService
from app.services.report_processing_service import ReportProcessingService
from app.services.report_upload_project_resolver_service import ReportUploadProjectResolverService
from app.services.resident_activation_service import ResidentActivationService
from app.services.resident_invite_service import ResidentInviteService
from app.services.resident_portal_service import ResidentPortalService
from app.services.security_dashboard_service import SecurityDashboardService
from app.services.tenant_extraction_service import TenantExtractionService
from app.services.tenant_manager_module_service import TenantManagerModuleService
from app.services.tenant_migration_service import TenantMigrationService
from app.services.tenant_scope_service import TenantScopeService
from app.services.testing_dashboard_service import TestingDashboardService
from app.services.user_management_service import UserManagementService
from app.services.workflow_execution_log_service import WorkflowExecutionLogService
from app.services.workflow_versioning_service import WorkflowVersioningService
from app.services.workspace_activity_service import WorkspaceActivityService


automation_monitoring_service = (
    AutomationMonitoringService()
)

automation_cron_management_service = (
    AutomationCronManagementService()
)

automation_replay_service = (
    AutomationReplayService()
)

automation_control_service = (
    AutomationControlService()
)

automation_job_queue_service = (
    AutomationJobQueueService()
)

automation_retry_policy_service = (
    AutomationRetryPolicyService()
)

automation_worker_service = (
    AutomationWorkerService(
        queue_service=automation_job_queue_service,
        retry_policy_service=automation_retry_policy_service,
    )
)

automation_worker_service.register_worker(
    "worker-default",
    capabilities=["sla_monitoring", "ai_automation", "ai_recovery"],
)

automation_scheduler_guard_service = (
    AutomationSchedulerGuardService()
)

automation_governance_service = (
    AutomationGovernanceService()
)

workflow_versioning_service = (
    WorkflowVersioningService()
)

workflow_execution_log_service = (
    WorkflowExecutionLogService()
)

dynamic_automation_builder_service = (
    DynamicAutomationBuilderService()
)

dead_letter_recovery_service = (
    DeadLetterRecoveryService()
)

recovery_dashboard_service = (
    RecoveryDashboardService(
        dead_letter_recovery_service=dead_letter_recovery_service,
    )
)

recovery_orchestration_service = (
    RecoveryOrchestrationService(
        dead_letter_recovery_service=dead_letter_recovery_service,
    )
)

auto_recovery_rules_service = (
    AutoRecoveryRulesService()
)

circuit_breaker_service = (
    CircuitBreakerService()
)

circuit_breaker_threshold_service = (
    CircuitBreakerThresholdService()
)

circuit_breaker_reopen_service = (
    CircuitBreakerReopenService(
        circuit_breaker_service=circuit_breaker_service,
        threshold_service=circuit_breaker_threshold_service,
    )
)

circuit_breaker_dashboard_service = (
    CircuitBreakerDashboardService(
        circuit_breaker_service=circuit_breaker_service,
        threshold_service=circuit_breaker_threshold_service,
        reopen_service=circuit_breaker_reopen_service,
    )
)

logger = get_logger(__name__)

jwt_service = JWTService()

IS_AUTOMATION_ENABLED = settings.FEATURE_FLAGS.enable_automation

orchestrator = (
    Orchestrator()
)

workflow_history = (
    WorkflowHistory()
)

approval_service = (
    ApprovalService()
)

ai_review_service = (
    AIReviewService()
)

operational_action_service = (
    OperationalActionService()
)

project_service = (
    ProjectService()
)

project_deletion_service = (
    ProjectDeletionService()
)

project_template_service = (
    ProjectTemplateService()
)

project_spatial_bootstrap_service = (
    ProjectSpatialBootstrapService()
)

project_repository = (
    ProjectRepository()
)

organization_repository = (
    OrganizationRepository()
)

ai_interpretation_repository = (
    AIInterpretationRepository()
)

operational_action_repository = (
    OperationalActionRepository()
)

weekly_report_repository = (
    WeeklyReportRepository()
)

project_workspace_service = (
    ProjectWorkspaceService()
)

operational_summary_service = (
    OperationalSummaryService()
)

portfolio_insights_service = (
    PortfolioInsightsService()
)

portfolio_intelligence_dashboard_service = (
    PortfolioIntelligenceDashboardService(
        portfolio_insights_service=portfolio_insights_service,
    )
)

database_hardening_dashboard_service = (
    DatabaseHardeningDashboardService()
)

devops_deployment_dashboard_service = (
    DevopsDeploymentDashboardService()
)

security_dashboard_service = (
    SecurityDashboardService()
)

observability_dashboard_service = (
    ObservabilityDashboardService()
)

testing_dashboard_service = (
    TestingDashboardService()
)

product_readiness_dashboard_service = (
    ProductReadinessDashboardService()
)

future_ai_features_dashboard_service = (
    FutureAiFeaturesDashboardService()
)

alert_engine_service = (
    AlertEngineService(
        portfolio_service=portfolio_insights_service,
    )
)

profile_service = (
    ProfileService(
        organization_repository=organization_repository,
    )
)

user_management_service = UserManagementService()

organization_admin_service = OrganizationAdminService()

field_report_module_service = FieldReportModuleService()

tenant_manager_module_service = TenantManagerModuleService()

ai_usage_dashboard_service = AIUsageDashboardService()

field_report_organization_profile_service = (
    FieldReportOrganizationProfileService(
        module_service=field_report_module_service,
    )
)

field_visit_report_service = FieldVisitReportService(
    organization_profile_service=(
        field_report_organization_profile_service
    ),
)

field_visit_report_export_service = FieldVisitReportExportService()

quality_issue_service = QualityIssueService()

project_supervision_dashboard_service = (
    ProjectSupervisionDashboardService()
)

portfolio_live_service = PortfolioLiveService(
    quality_issue_service=quality_issue_service,
)

deliverable_reports_service = DeliverableReportsService()

notification_service = (
    NotificationService()
)

workspace_activity_service = (
    WorkspaceActivityService()
)

qc_notification_service = build_qc_notification_service(
    persistent_dedup=True,
    workspace_activity_service=workspace_activity_service,
)

field_visit_report_service.qc_notification_service = qc_notification_service

tenant_migration_service = TenantMigrationService()

tenant_scope_service = TenantScopeService()

tenant_extraction_service = TenantExtractionService()

project_apartment_service = ProjectApartmentService()

resident_invite_service = ResidentInviteService()

resident_portal_service = ResidentPortalService()

resident_activation_service = ResidentActivationService()

field_report_finalize_service = FieldReportFinalizeService(
    visit_report_service=field_visit_report_service,
    notification_service=notification_service,
    workspace_activity_service=workspace_activity_service,
    resident_portal_service=resident_portal_service,
)

report_processing_service = (
    ReportProcessingService()
)

report_deletion_service = ReportDeletionService(
    field_visit_report_repository=field_visit_report_service.report_repository,
    line_repository=field_visit_report_service.line_repository,
    line_photo_repository=field_visit_report_service.line_photo_repository,
    photo_service=field_visit_report_service.photo_service,
)

report_upload_project_resolver_service = (
    ReportUploadProjectResolverService()
)


# ==========================================
# Depends()-compatible providers
# ==========================================

def get_automation_monitoring_service():
    return automation_monitoring_service


def get_automation_cron_management_service():
    return automation_cron_management_service


def get_automation_replay_service():
    return automation_replay_service


def get_automation_control_service():
    return automation_control_service


def get_automation_job_queue_service():
    return automation_job_queue_service


def get_automation_retry_policy_service():
    return automation_retry_policy_service


def get_automation_worker_service():
    return automation_worker_service


def get_automation_scheduler_guard_service():
    return automation_scheduler_guard_service


def get_automation_governance_service():
    return automation_governance_service


def get_workflow_versioning_service():
    return workflow_versioning_service


def get_workflow_execution_log_service():
    return workflow_execution_log_service


def get_dynamic_automation_builder_service():
    return dynamic_automation_builder_service


def get_dead_letter_recovery_service():
    return dead_letter_recovery_service


def get_recovery_dashboard_service():
    return recovery_dashboard_service


def get_recovery_orchestration_service():
    return recovery_orchestration_service


def get_auto_recovery_rules_service():
    return auto_recovery_rules_service


def get_circuit_breaker_service():
    return circuit_breaker_service


def get_circuit_breaker_threshold_service():
    return circuit_breaker_threshold_service


def get_circuit_breaker_reopen_service():
    return circuit_breaker_reopen_service


def get_circuit_breaker_dashboard_service():
    return circuit_breaker_dashboard_service


def get_jwt_service():
    return jwt_service


def get_orchestrator():
    return orchestrator


def get_workflow_history():
    return workflow_history


def get_approval_service():
    return approval_service


def get_ai_review_service():
    return ai_review_service


def get_operational_action_service():
    return operational_action_service


def get_project_service():
    return project_service


def get_project_deletion_service():
    return project_deletion_service


def get_project_template_service():
    return project_template_service


def get_project_spatial_bootstrap_service():
    return project_spatial_bootstrap_service


def get_project_repository():
    return project_repository


def get_organization_repository():
    return organization_repository


def get_ai_interpretation_repository():
    return ai_interpretation_repository


def get_operational_action_repository():
    return operational_action_repository


def get_weekly_report_repository():
    return weekly_report_repository


def get_project_workspace_service():
    return project_workspace_service


def get_operational_summary_service():
    return operational_summary_service


def get_portfolio_insights_service():
    return portfolio_insights_service


def get_portfolio_intelligence_dashboard_service():
    return portfolio_intelligence_dashboard_service


def get_database_hardening_dashboard_service():
    return database_hardening_dashboard_service


def get_devops_deployment_dashboard_service():
    return devops_deployment_dashboard_service


def get_security_dashboard_service():
    return security_dashboard_service


def get_observability_dashboard_service():
    return observability_dashboard_service


def get_testing_dashboard_service():
    return testing_dashboard_service


def get_product_readiness_dashboard_service():
    return product_readiness_dashboard_service


def get_future_ai_features_dashboard_service():
    return future_ai_features_dashboard_service


def get_alert_engine_service():
    return alert_engine_service


def get_profile_service():
    return profile_service


def get_user_management_service():
    return user_management_service


def get_organization_admin_service():
    return organization_admin_service


def get_field_report_module_service():
    return field_report_module_service


def get_tenant_manager_module_service():
    return tenant_manager_module_service


def get_ai_usage_dashboard_service():
    return ai_usage_dashboard_service


def get_field_report_organization_profile_service():
    return field_report_organization_profile_service


def get_field_visit_report_service():
    return field_visit_report_service


def get_field_visit_report_export_service():
    return field_visit_report_export_service


def get_quality_issue_service():
    return quality_issue_service


def get_project_supervision_dashboard_service():
    return project_supervision_dashboard_service


def get_portfolio_live_service():
    return portfolio_live_service


def get_deliverable_reports_service():
    return deliverable_reports_service


def get_notification_service():
    return notification_service


def get_workspace_activity_service():
    return workspace_activity_service


def get_tenant_migration_service():
    return tenant_migration_service


def get_tenant_scope_service():
    return tenant_scope_service


def get_tenant_extraction_service():
    return tenant_extraction_service


def get_project_apartment_service():
    return project_apartment_service


def get_resident_invite_service():
    return resident_invite_service


def get_resident_portal_service():
    return resident_portal_service


def get_resident_activation_service():
    return resident_activation_service


def get_field_report_finalize_service():
    return field_report_finalize_service


def get_report_processing_service():
    return report_processing_service


def get_report_deletion_service():
    return report_deletion_service


def get_report_upload_project_resolver_service():
    return report_upload_project_resolver_service


