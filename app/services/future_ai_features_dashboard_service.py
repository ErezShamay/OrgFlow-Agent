from app.services.autonomous_workflows_service import AutonomousWorkflowsService
from app.services.ai_action_generation_service import AiActionGenerationService
from app.services.ai_project_forecasting_service import AiProjectForecastingService
from app.services.ai_anomaly_detection_service import AiAnomalyDetectionService
from app.services.ai_scheduling_optimization_service import AiSchedulingOptimizationService
from app.services.ai_recommendation_engine_service import AiRecommendationEngineService
from app.services.ai_executive_assistant_service import AiExecutiveAssistantService
from app.services.voice_summaries_service import VoiceSummariesService
from app.services.whatsapp_integration_service import WhatsappIntegrationService
from app.services.email_ingestion_ai_service import EmailIngestionAiService
from app.services.sharepoint_integration_service import SharepointIntegrationService
from app.services.teams_integration_service import TeamsIntegrationService
from app.services.slack_integration_service import SlackIntegrationService
from app.services.ai_copilots_service import AiCopilotsService
from app.services.conversational_workspace_ai_service import ConversationalWorkspaceAiService
from app.services.autonomous_recovery_agents_service import AutonomousRecoveryAgentsService


class FutureAiFeaturesDashboardService:
    def __init__(
        self,
        autonomous_workflows_service: AutonomousWorkflowsService | None = None,
        ai_action_generation_service: AiActionGenerationService | None = None,
        ai_project_forecasting_service: AiProjectForecastingService | None = None,
        ai_anomaly_detection_service: AiAnomalyDetectionService | None = None,
        ai_scheduling_optimization_service: AiSchedulingOptimizationService | None = None,
        ai_recommendation_engine_service: AiRecommendationEngineService | None = None,
        ai_executive_assistant_service: AiExecutiveAssistantService | None = None,
        voice_summaries_service: VoiceSummariesService | None = None,
        whatsapp_integration_service: WhatsappIntegrationService | None = None,
        email_ingestion_ai_service: EmailIngestionAiService | None = None,
        sharepoint_integration_service: SharepointIntegrationService | None = None,
        teams_integration_service: TeamsIntegrationService | None = None,
        slack_integration_service: SlackIntegrationService | None = None,
        ai_copilots_service: AiCopilotsService | None = None,
        conversational_workspace_ai_service: ConversationalWorkspaceAiService | None = None,
        autonomous_recovery_agents_service: AutonomousRecoveryAgentsService | None = None,
    ):
        self.autonomous_workflows_service = autonomous_workflows_service or AutonomousWorkflowsService()
        self.ai_action_generation_service = ai_action_generation_service or AiActionGenerationService()
        self.ai_project_forecasting_service = ai_project_forecasting_service or AiProjectForecastingService()
        self.ai_anomaly_detection_service = ai_anomaly_detection_service or AiAnomalyDetectionService()
        self.ai_scheduling_optimization_service = ai_scheduling_optimization_service or AiSchedulingOptimizationService()
        self.ai_recommendation_engine_service = ai_recommendation_engine_service or AiRecommendationEngineService()
        self.ai_executive_assistant_service = ai_executive_assistant_service or AiExecutiveAssistantService()
        self.voice_summaries_service = voice_summaries_service or VoiceSummariesService()
        self.whatsapp_integration_service = whatsapp_integration_service or WhatsappIntegrationService()
        self.email_ingestion_ai_service = email_ingestion_ai_service or EmailIngestionAiService()
        self.sharepoint_integration_service = sharepoint_integration_service or SharepointIntegrationService()
        self.teams_integration_service = teams_integration_service or TeamsIntegrationService()
        self.slack_integration_service = slack_integration_service or SlackIntegrationService()
        self.ai_copilots_service = ai_copilots_service or AiCopilotsService()
        self.conversational_workspace_ai_service = conversational_workspace_ai_service or ConversationalWorkspaceAiService()
        self.autonomous_recovery_agents_service = autonomous_recovery_agents_service or AutonomousRecoveryAgentsService()

    def get_dashboard(self) -> dict:
        validations = [
            self.autonomous_workflows_service.validate_setup()["valid"],
            self.ai_action_generation_service.validate_setup()["valid"],
            self.ai_project_forecasting_service.validate_setup()["valid"],
            self.ai_anomaly_detection_service.validate_setup()["valid"],
            self.ai_scheduling_optimization_service.validate_setup()["valid"],
            self.ai_recommendation_engine_service.validate_setup()["valid"],
            self.ai_executive_assistant_service.validate_setup()["valid"],
            self.voice_summaries_service.validate_setup()["valid"],
            self.whatsapp_integration_service.validate_setup()["valid"],
            self.email_ingestion_ai_service.validate_setup()["valid"],
            self.sharepoint_integration_service.validate_setup()["valid"],
            self.teams_integration_service.validate_setup()["valid"],
            self.slack_integration_service.validate_setup()["valid"],
            self.ai_copilots_service.validate_setup()["valid"],
            self.conversational_workspace_ai_service.validate_setup()["valid"],
            self.autonomous_recovery_agents_service.validate_setup()["valid"],
        ]

        return {
            "autonomous_workflows": self.autonomous_workflows_service.get_config(),
            "ai_action_generation": self.ai_action_generation_service.get_config(),
            "ai_project_forecasting": self.ai_project_forecasting_service.get_config(),
            "ai_anomaly_detection": self.ai_anomaly_detection_service.get_config(),
            "ai_scheduling_optimization": self.ai_scheduling_optimization_service.get_config(),
            "ai_recommendation_engine": self.ai_recommendation_engine_service.get_config(),
            "ai_executive_assistant": self.ai_executive_assistant_service.get_config(),
            "voice_summaries": self.voice_summaries_service.get_config(),
            "whatsapp_integration": self.whatsapp_integration_service.get_config(),
            "email_ingestion_ai": self.email_ingestion_ai_service.get_config(),
            "sharepoint_integration": self.sharepoint_integration_service.get_config(),
            "teams_integration": self.teams_integration_service.get_config(),
            "slack_integration": self.slack_integration_service.get_config(),
            "ai_copilots": self.ai_copilots_service.get_config(),
            "conversational_workspace_ai": self.conversational_workspace_ai_service.get_config(),
            "autonomous_recovery_agents": self.autonomous_recovery_agents_service.get_config(),
            "future_ai_ready": all(validations),
        }

    def get_autonomous_workflows_config(self) -> dict:
        return self.autonomous_workflows_service.get_config()
    def list_autonomous_workflow_templates(self) -> dict:
        return self.autonomous_workflows_service.list_workflow_templates()
    def evaluate_autonomous_workflow_run(self, *, template_id: str = "escalation_response", approved: bool = True) -> dict:
        return self.autonomous_workflows_service.evaluate_run(template_id=template_id, approved=approved)
    def validate_autonomous_workflows(self) -> dict:
        return self.autonomous_workflows_service.validate_setup()
    def get_ai_action_generation_config(self) -> dict:
        return self.ai_action_generation_service.get_config()
    def list_ai_action_generation_types(self) -> dict:
        return self.ai_action_generation_service.list_action_types()
    def simulate_ai_action_generation(self, *, project_id: str = "p1", signal_count: int = 3) -> dict:
        return self.ai_action_generation_service.simulate_generation(project_id=project_id, signal_count=signal_count)
    def validate_ai_action_generation(self) -> dict:
        return self.ai_action_generation_service.validate_setup()
    def get_ai_project_forecasting_config(self) -> dict:
        return self.ai_project_forecasting_service.get_config()
    def list_ai_project_forecast_metrics(self) -> dict:
        return self.ai_project_forecasting_service.list_forecast_metrics()
    def run_ai_project_forecast(self, *, project_id: str = "p1", health_score: int = 55) -> dict:
        return self.ai_project_forecasting_service.forecast_project(project_id=project_id, health_score=health_score)
    def validate_ai_project_forecasting(self) -> dict:
        return self.ai_project_forecasting_service.validate_setup()
    def get_ai_anomaly_detection_config(self) -> dict:
        return self.ai_anomaly_detection_service.get_config()
    def list_ai_anomaly_detectors(self) -> dict:
        return self.ai_anomaly_detection_service.list_detectors()
    def scan_ai_anomalies(self, *, metric: str = "actions", current_value: float = 120.0, baseline: float = 40.0) -> dict:
        return self.ai_anomaly_detection_service.scan(metric=metric, current_value=current_value, baseline=baseline)
    def validate_ai_anomaly_detection(self) -> dict:
        return self.ai_anomaly_detection_service.validate_setup()
    def get_ai_scheduling_optimization_config(self) -> dict:
        return self.ai_scheduling_optimization_service.get_config()
    def list_ai_scheduling_constraints(self) -> dict:
        return self.ai_scheduling_optimization_service.list_constraints()
    def run_ai_schedule_optimization(self, *, action_count: int = 8, available_hours: float = 6.0) -> dict:
        return self.ai_scheduling_optimization_service.optimize(action_count=action_count, available_hours=available_hours)
    def validate_ai_scheduling_optimization(self) -> dict:
        return self.ai_scheduling_optimization_service.validate_setup()
    def get_ai_recommendation_engine_config(self) -> dict:
        return self.ai_recommendation_engine_service.get_config()
    def list_ai_recommendation_types(self) -> dict:
        return self.ai_recommendation_engine_service.list_recommendation_types()
    def generate_ai_recommendations(self, *, context: str = "project", item_count: int = 3) -> dict:
        return self.ai_recommendation_engine_service.generate(context=context, item_count=item_count)
    def validate_ai_recommendation_engine(self) -> dict:
        return self.ai_recommendation_engine_service.validate_setup()
    def get_ai_executive_assistant_config(self) -> dict:
        return self.ai_executive_assistant_service.get_config()
    def list_ai_executive_assistant_capabilities(self) -> dict:
        return self.ai_executive_assistant_service.list_capabilities()
    def compose_ai_executive_briefing(self, *, topics: str = "") -> dict:
        topic_list = [t for t in topics.split(",") if t]
        return self.ai_executive_assistant_service.compose_briefing(topics=topic_list)
    def validate_ai_executive_assistant(self) -> dict:
        return self.ai_executive_assistant_service.validate_setup()
    def get_voice_summaries_config(self) -> dict:
        return self.voice_summaries_service.get_config()
    def list_voice_summary_voices(self) -> dict:
        return self.voice_summaries_service.list_voices()
    def synthesize_voice_summary(self, *, text_length: int = 500) -> dict:
        return self.voice_summaries_service.synthesize(text_length=text_length)
    def validate_voice_summaries(self) -> dict:
        return self.voice_summaries_service.validate_setup()
    def get_whatsapp_integration_config(self) -> dict:
        return self.whatsapp_integration_service.get_config()
    def list_whatsapp_templates(self) -> dict:
        return self.whatsapp_integration_service.list_templates()
    def validate_whatsapp_webhook(self, *, signature_valid: bool = True) -> dict:
        return self.whatsapp_integration_service.validate_webhook(signature_valid=signature_valid)
    def validate_whatsapp_integration(self) -> dict:
        return self.whatsapp_integration_service.validate_setup()
    def get_email_ingestion_ai_config(self) -> dict:
        return self.email_ingestion_ai_service.get_config()
    def list_email_ingestion_parsers(self) -> dict:
        return self.email_ingestion_ai_service.list_parsers()
    def process_email_ingestion(self, *, has_attachment: bool = True, subject: str = "Q1 report") -> dict:
        return self.email_ingestion_ai_service.process_message(has_attachment=has_attachment, subject=subject)
    def validate_email_ingestion_ai(self) -> dict:
        return self.email_ingestion_ai_service.validate_setup()
    def get_sharepoint_integration_config(self) -> dict:
        return self.sharepoint_integration_service.get_config()
    def list_sharepoint_sync_targets(self) -> dict:
        return self.sharepoint_integration_service.list_sync_targets()
    def sync_sharepoint_library(self, *, site_id: str = "site-1", files_found: int = 5) -> dict:
        return self.sharepoint_integration_service.sync_library(site_id=site_id, files_found=files_found)
    def validate_sharepoint_integration(self) -> dict:
        return self.sharepoint_integration_service.validate_setup()
    def get_teams_integration_config(self) -> dict:
        return self.teams_integration_service.get_config()
    def list_teams_commands(self) -> dict:
        return self.teams_integration_service.list_commands()
    def post_teams_notification(self, *, channel_id: str = "general", urgent: bool = False) -> dict:
        return self.teams_integration_service.post_notification(channel_id=channel_id, urgent=urgent)
    def validate_teams_integration(self) -> dict:
        return self.teams_integration_service.validate_setup()
    def get_slack_integration_config(self) -> dict:
        return self.slack_integration_service.get_config()
    def list_slack_slash_commands(self) -> dict:
        return self.slack_integration_service.list_slash_commands()
    def handle_slack_event(self, *, event_type: str = "app_mention") -> dict:
        return self.slack_integration_service.handle_event(event_type=event_type)
    def validate_slack_integration(self) -> dict:
        return self.slack_integration_service.validate_setup()
    def get_ai_copilots_config(self) -> dict:
        return self.ai_copilots_service.get_config()
    def list_ai_copilots(self) -> dict:
        return self.ai_copilots_service.list_copilots()
    def invoke_ai_copilot(self, *, copilot_id: str = "project_copilot", prompt_length: int = 50) -> dict:
        return self.ai_copilots_service.invoke(copilot_id=copilot_id, prompt_length=prompt_length)
    def validate_ai_copilots(self) -> dict:
        return self.ai_copilots_service.validate_setup()
    def get_conversational_workspace_ai_config(self) -> dict:
        return self.conversational_workspace_ai_service.get_config()
    def list_conversational_workspace_tools(self) -> dict:
        return self.conversational_workspace_ai_service.list_tools()
    def chat_conversational_workspace(self, *, message: str = "Summarize today", project_id: str = "p1") -> dict:
        return self.conversational_workspace_ai_service.chat(message=message, project_id=project_id)
    def validate_conversational_workspace_ai(self) -> dict:
        return self.conversational_workspace_ai_service.validate_setup()
    def get_autonomous_recovery_agents_config(self) -> dict:
        return self.autonomous_recovery_agents_service.get_config()
    def list_autonomous_recovery_agents(self) -> dict:
        return self.autonomous_recovery_agents_service.list_agents()
    def triage_autonomous_recovery_failure(self, *, failure_category: str = "transient", retry_count: int = 1) -> dict:
        return self.autonomous_recovery_agents_service.triage_failure(failure_category=failure_category, retry_count=retry_count)
    def validate_autonomous_recovery_agents(self) -> dict:
        return self.autonomous_recovery_agents_service.validate_setup()
