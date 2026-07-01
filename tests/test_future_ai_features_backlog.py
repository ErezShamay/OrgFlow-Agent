from fastapi.testclient import TestClient

import app.main as main_module
from app.auth.jwt_service import JWTService
from app.main import app
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
from app.services.future_ai_features_dashboard_service import (
    FutureAiFeaturesDashboardService,
)
import app.dependencies as deps


def build_dashboard():
    return FutureAiFeaturesDashboardService()



def test_autonomous_workflows():
    service = AutonomousWorkflowsService()
    config = service.get_config()
    assert config["engine_id"] == 'orgflow_autonomous_v1'

    listed = service.list_workflow_templates()
    assert listed["total"] >= 3

    action = service.evaluate_run()
    assert action is not None
    assert service.validate_setup()["valid"] is True

def test_ai_action_generation():
    service = AiActionGenerationService()
    config = service.get_config()
    assert config["model_route"] == 'ai_routing_engine'

    listed = service.list_action_types()
    assert listed["total"] >= 3

    action = service.simulate_generation()
    assert action is not None
    assert service.validate_setup()["valid"] is True

def test_ai_project_forecasting():
    service = AiProjectForecastingService()
    config = service.get_config()
    assert config["horizon_weeks"] == 12

    listed = service.list_forecast_metrics()
    assert listed["total"] >= 3

    action = service.forecast_project()
    assert action is not None
    assert service.validate_setup()["valid"] is True

def test_ai_anomaly_detection():
    service = AiAnomalyDetectionService()
    config = service.get_config()
    assert config["detector_id"] == 'orgflow_anomaly_v1'

    listed = service.list_detectors()
    assert listed["total"] >= 3

    action = service.scan()
    assert action is not None
    assert service.validate_setup()["valid"] is True

def test_ai_scheduling_optimization():
    service = AiSchedulingOptimizationService()
    config = service.get_config()
    assert config["optimizer_id"] == 'schedule_opt_v1'

    listed = service.list_constraints()
    assert listed["total"] >= 3

    action = service.optimize()
    assert action is not None
    assert service.validate_setup()["valid"] is True

def test_ai_recommendation_engine():
    service = AiRecommendationEngineService()
    config = service.get_config()
    assert config["engine_id"] == 'orgflow_recommendations_v1'

    listed = service.list_recommendation_types()
    assert listed["total"] >= 3

    action = service.generate()
    assert action is not None
    assert service.validate_setup()["valid"] is True

def test_ai_executive_assistant():
    service = AiExecutiveAssistantService()
    config = service.get_config()
    assert config["assistant_id"] == 'orgflow_exec_assistant_v1'

    listed = service.list_capabilities()
    assert listed["total"] >= 3

    action = service.compose_briefing()
    assert action is not None
    assert service.validate_setup()["valid"] is True

def test_voice_summaries():
    service = VoiceSummariesService()
    config = service.get_config()
    assert config["provider"] == 'elevenlabs'

    listed = service.list_voices()
    assert listed["total"] >= 3

    action = service.synthesize()
    assert action is not None
    assert service.validate_setup()["valid"] is True

def test_whatsapp_integration():
    service = WhatsappIntegrationService()
    config = service.get_config()
    assert config["provider"] == 'meta_cloud_api'

    listed = service.list_templates()
    assert listed["total"] >= 3

    action = service.validate_webhook()
    assert action is not None
    assert service.validate_setup()["valid"] is True

def test_email_ingestion_ai():
    service = EmailIngestionAiService()
    config = service.get_config()
    assert config["pipeline_id"] == 'orgflow_email_ingest_v1'

    listed = service.list_parsers()
    assert listed["total"] >= 3

    action = service.process_message()
    assert action is not None
    assert service.validate_setup()["valid"] is True

def test_sharepoint_integration():
    service = SharepointIntegrationService()
    config = service.get_config()
    assert config["connector"] == 'microsoft_graph'

    listed = service.list_sync_targets()
    assert listed["total"] >= 3

    action = service.sync_library()
    assert action is not None
    assert service.validate_setup()["valid"] is True

def test_teams_integration():
    service = TeamsIntegrationService()
    config = service.get_config()
    assert config["connector"] == 'microsoft_teams_bot'

    listed = service.list_commands()
    assert listed["total"] >= 3

    action = service.post_notification()
    assert action is not None
    assert service.validate_setup()["valid"] is True

def test_slack_integration():
    service = SlackIntegrationService()
    config = service.get_config()
    assert config["app_id"] == 'orgflow_slack_app'

    listed = service.list_slash_commands()
    assert listed["total"] >= 3

    action = service.handle_event()
    assert action is not None
    assert service.validate_setup()["valid"] is True

def test_ai_copilots():
    service = AiCopilotsService()
    config = service.get_config()
    assert config["copilot_suite"] == 'orgflow_copilots_v1'

    listed = service.list_copilots()
    assert listed["total"] >= 3

    action = service.invoke()
    assert action is not None
    assert service.validate_setup()["valid"] is True

def test_conversational_workspace_ai():
    service = ConversationalWorkspaceAiService()
    config = service.get_config()
    assert config["session_store"] == 'redis'

    listed = service.list_tools()
    assert listed["total"] >= 3

    action = service.chat()
    assert action is not None
    assert service.validate_setup()["valid"] is True

def test_autonomous_recovery_agents():
    service = AutonomousRecoveryAgentsService()
    config = service.get_config()
    assert config["agent_pool"] == 'recovery_agents_v1'

    listed = service.list_agents()
    assert listed["total"] >= 3

    action = service.triage_failure()
    assert action is not None
    assert service.validate_setup()["valid"] is True


def test_future_ai_features_dashboard_aggregates_all_domains():
    dashboard = build_dashboard()
    result = dashboard.get_dashboard()

    assert result["future_ai_ready"] is True
    assert result["autonomous_workflows"]["engine_id"] == "orgflow_autonomous_v1"
    assert result["slack_integration"]["app_id"] == "orgflow_slack_app"
    assert result["autonomous_recovery_agents"]["agent_pool"] == "recovery_agents_v1"


def _auth_headers():
    token = JWTService().issue_access_token(
        user_id="user-1",
        org_id="org-1",
        role="ADMIN",
        token_id="future-ai-features-backlog-tests",
    )
    return {"Authorization": f"Bearer {token}", "X-Organization-ID": "org-1"}


def test_future_ai_features_api_endpoints(monkeypatch):
    dashboard = build_dashboard()
    monkeypatch.setattr(
        deps,
        "future_ai_features_dashboard_service",
        dashboard,
    )

    client = TestClient(app)
    headers = _auth_headers()

    get_endpoints = [
        "/future-ai/dashboard",
        "/future-ai/autonomous-workflows/config",
        "/future-ai/autonomous-workflows/templates",
        "/future-ai/autonomous-workflows/run",
        "/future-ai/autonomous-workflows/validate",
        "/future-ai/ai-action-generation/config",
        "/future-ai/ai-action-generation/types",
        "/future-ai/ai-action-generation/simulate",
        "/future-ai/ai-action-generation/validate",
        "/future-ai/project-forecasting/config",
        "/future-ai/project-forecasting/metrics",
        "/future-ai/project-forecasting/forecast",
        "/future-ai/project-forecasting/validate",
        "/future-ai/anomaly-detection/config",
        "/future-ai/anomaly-detection/detectors",
        "/future-ai/anomaly-detection/scan",
        "/future-ai/anomaly-detection/validate",
        "/future-ai/scheduling-optimization/config",
        "/future-ai/scheduling-optimization/constraints",
        "/future-ai/scheduling-optimization/optimize",
        "/future-ai/scheduling-optimization/validate",
        "/future-ai/recommendation-engine/config",
        "/future-ai/recommendation-engine/types",
        "/future-ai/recommendation-engine/generate",
        "/future-ai/recommendation-engine/validate",
        "/future-ai/executive-assistant/config",
        "/future-ai/executive-assistant/capabilities",
        "/future-ai/executive-assistant/briefing",
        "/future-ai/executive-assistant/validate",
        "/future-ai/voice-summaries/config",
        "/future-ai/voice-summaries/voices",
        "/future-ai/voice-summaries/synthesize",
        "/future-ai/voice-summaries/validate",
        "/future-ai/whatsapp/config",
        "/future-ai/whatsapp/templates",
        "/future-ai/whatsapp/webhook",
        "/future-ai/whatsapp/validate",
        "/future-ai/email-ingestion/config",
        "/future-ai/email-ingestion/parsers",
        "/future-ai/email-ingestion/process",
        "/future-ai/email-ingestion/validate",
        "/future-ai/sharepoint/config",
        "/future-ai/sharepoint/targets",
        "/future-ai/sharepoint/sync",
        "/future-ai/sharepoint/validate",
        "/future-ai/teams/config",
        "/future-ai/teams/commands",
        "/future-ai/teams/notify",
        "/future-ai/teams/validate",
        "/future-ai/slack/config",
        "/future-ai/slack/commands",
        "/future-ai/slack/events",
        "/future-ai/slack/validate",
        "/future-ai/copilots/config",
        "/future-ai/copilots/list",
        "/future-ai/copilots/invoke",
        "/future-ai/copilots/validate",
        "/future-ai/conversational-workspace/config",
        "/future-ai/conversational-workspace/tools",
        "/future-ai/conversational-workspace/chat",
        "/future-ai/conversational-workspace/validate",
        "/future-ai/recovery-agents/config",
        "/future-ai/recovery-agents/agents",
        "/future-ai/recovery-agents/triage",
        "/future-ai/recovery-agents/validate"
    ]

    for path in get_endpoints:
        response = client.get(path, headers=headers)
        assert response.status_code == 200, path

    dashboard_response = client.get(
        "/future-ai/dashboard",
        headers=headers,
    ).json()
    assert dashboard_response["future_ai_ready"] is True
