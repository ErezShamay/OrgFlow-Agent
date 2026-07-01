"""Future AI features routes.

Extracted from app/main.py during the 2026-07 architecture-modularization
refactor. Shared service singletons live in app/dependencies.py; shared
request models live in app/schemas/api_requests.py.
"""
from __future__ import annotations


from fastapi import APIRouter
import app.dependencies as deps


router = APIRouter()


@router.get("/future-ai/dashboard")
def get_future_ai_dashboard():
    return deps.future_ai_features_dashboard_service.get_dashboard()


@router.get("/future-ai/autonomous-workflows/config")
def future_ai_autonomous_workflows_config():
    return deps.future_ai_features_dashboard_service.get_autonomous_workflows_config()


@router.get("/future-ai/autonomous-workflows/templates")
def future_ai_autonomous_workflows_templates():
    return deps.future_ai_features_dashboard_service.list_autonomous_workflow_templates()


@router.get("/future-ai/autonomous-workflows/run")
def future_ai_autonomous_workflows_run(template_id: str = "escalation_response", approved: bool = True):
    return deps.future_ai_features_dashboard_service.evaluate_autonomous_workflow_run(template_id=template_id, approved=approved)


@router.get("/future-ai/autonomous-workflows/validate")
def future_ai_autonomous_workflows_validate():
    return deps.future_ai_features_dashboard_service.validate_autonomous_workflows()


@router.get("/future-ai/ai-action-generation/config")
def future_ai_ai_action_generation_config():
    return deps.future_ai_features_dashboard_service.get_ai_action_generation_config()


@router.get("/future-ai/ai-action-generation/types")
def future_ai_ai_action_generation_types():
    return deps.future_ai_features_dashboard_service.list_ai_action_generation_types()


@router.get("/future-ai/ai-action-generation/simulate")
def future_ai_ai_action_generation_simulate(project_id: str = "p1", signal_count: int = 3):
    return deps.future_ai_features_dashboard_service.simulate_ai_action_generation(project_id=project_id, signal_count=signal_count)


@router.get("/future-ai/ai-action-generation/validate")
def future_ai_ai_action_generation_validate():
    return deps.future_ai_features_dashboard_service.validate_ai_action_generation()


@router.get("/future-ai/project-forecasting/config")
def future_ai_project_forecasting_config():
    return deps.future_ai_features_dashboard_service.get_ai_project_forecasting_config()


@router.get("/future-ai/project-forecasting/metrics")
def future_ai_project_forecasting_metrics():
    return deps.future_ai_features_dashboard_service.list_ai_project_forecast_metrics()


@router.get("/future-ai/project-forecasting/forecast")
def future_ai_project_forecasting_forecast(project_id: str = "p1", health_score: int = 55):
    return deps.future_ai_features_dashboard_service.run_ai_project_forecast(project_id=project_id, health_score=health_score)


@router.get("/future-ai/project-forecasting/validate")
def future_ai_project_forecasting_validate():
    return deps.future_ai_features_dashboard_service.validate_ai_project_forecasting()


@router.get("/future-ai/anomaly-detection/config")
def future_ai_anomaly_detection_config():
    return deps.future_ai_features_dashboard_service.get_ai_anomaly_detection_config()


@router.get("/future-ai/anomaly-detection/detectors")
def future_ai_anomaly_detection_detectors():
    return deps.future_ai_features_dashboard_service.list_ai_anomaly_detectors()


@router.get("/future-ai/anomaly-detection/scan")
def future_ai_anomaly_detection_scan(metric: str = "actions", current_value: float = 120.0, baseline: float = 40.0):
    return deps.future_ai_features_dashboard_service.scan_ai_anomalies(metric=metric, current_value=current_value, baseline=baseline)


@router.get("/future-ai/anomaly-detection/validate")
def future_ai_anomaly_detection_validate():
    return deps.future_ai_features_dashboard_service.validate_ai_anomaly_detection()


@router.get("/future-ai/scheduling-optimization/config")
def future_ai_scheduling_optimization_config():
    return deps.future_ai_features_dashboard_service.get_ai_scheduling_optimization_config()


@router.get("/future-ai/scheduling-optimization/constraints")
def future_ai_scheduling_optimization_constraints():
    return deps.future_ai_features_dashboard_service.list_ai_scheduling_constraints()


@router.get("/future-ai/scheduling-optimization/optimize")
def future_ai_scheduling_optimization_optimize(action_count: int = 8, available_hours: float = 6.0):
    return deps.future_ai_features_dashboard_service.run_ai_schedule_optimization(action_count=action_count, available_hours=available_hours)


@router.get("/future-ai/scheduling-optimization/validate")
def future_ai_scheduling_optimization_validate():
    return deps.future_ai_features_dashboard_service.validate_ai_scheduling_optimization()


@router.get("/future-ai/recommendation-engine/config")
def future_ai_recommendation_engine_config():
    return deps.future_ai_features_dashboard_service.get_ai_recommendation_engine_config()


@router.get("/future-ai/recommendation-engine/types")
def future_ai_recommendation_engine_types():
    return deps.future_ai_features_dashboard_service.list_ai_recommendation_types()


@router.get("/future-ai/recommendation-engine/generate")
def future_ai_recommendation_engine_generate(context: str = "project", item_count: int = 3):
    return deps.future_ai_features_dashboard_service.generate_ai_recommendations(context=context, item_count=item_count)


@router.get("/future-ai/recommendation-engine/validate")
def future_ai_recommendation_engine_validate():
    return deps.future_ai_features_dashboard_service.validate_ai_recommendation_engine()


@router.get("/future-ai/executive-assistant/config")
def future_ai_executive_assistant_config():
    return deps.future_ai_features_dashboard_service.get_ai_executive_assistant_config()


@router.get("/future-ai/executive-assistant/capabilities")
def future_ai_executive_assistant_capabilities():
    return deps.future_ai_features_dashboard_service.list_ai_executive_assistant_capabilities()


@router.get("/future-ai/executive-assistant/briefing")
def future_ai_executive_assistant_briefing(topics: str = ""):
    return deps.future_ai_features_dashboard_service.compose_ai_executive_briefing(topics=topics)


@router.get("/future-ai/executive-assistant/validate")
def future_ai_executive_assistant_validate():
    return deps.future_ai_features_dashboard_service.validate_ai_executive_assistant()


@router.get("/future-ai/voice-summaries/config")
def future_ai_voice_summaries_config():
    return deps.future_ai_features_dashboard_service.get_voice_summaries_config()


@router.get("/future-ai/voice-summaries/voices")
def future_ai_voice_summaries_voices():
    return deps.future_ai_features_dashboard_service.list_voice_summary_voices()


@router.get("/future-ai/voice-summaries/synthesize")
def future_ai_voice_summaries_synthesize(text_length: int = 500):
    return deps.future_ai_features_dashboard_service.synthesize_voice_summary(text_length=text_length)


@router.get("/future-ai/voice-summaries/validate")
def future_ai_voice_summaries_validate():
    return deps.future_ai_features_dashboard_service.validate_voice_summaries()


@router.get("/future-ai/whatsapp/config")
def future_ai_whatsapp_config():
    return deps.future_ai_features_dashboard_service.get_whatsapp_integration_config()


@router.get("/future-ai/whatsapp/templates")
def future_ai_whatsapp_templates():
    return deps.future_ai_features_dashboard_service.list_whatsapp_templates()


@router.get("/future-ai/whatsapp/webhook")
def future_ai_whatsapp_webhook(signature_valid: bool = True):
    return deps.future_ai_features_dashboard_service.validate_whatsapp_webhook(signature_valid=signature_valid)


@router.get("/future-ai/whatsapp/validate")
def future_ai_whatsapp_validate():
    return deps.future_ai_features_dashboard_service.validate_whatsapp_integration()


@router.get("/future-ai/email-ingestion/config")
def future_ai_email_ingestion_config():
    return deps.future_ai_features_dashboard_service.get_email_ingestion_ai_config()


@router.get("/future-ai/email-ingestion/parsers")
def future_ai_email_ingestion_parsers():
    return deps.future_ai_features_dashboard_service.list_email_ingestion_parsers()


@router.get("/future-ai/email-ingestion/process")
def future_ai_email_ingestion_process(has_attachment: bool = True, subject: str = "Q1 report"):
    return deps.future_ai_features_dashboard_service.process_email_ingestion(has_attachment=has_attachment, subject=subject)


@router.get("/future-ai/email-ingestion/validate")
def future_ai_email_ingestion_validate():
    return deps.future_ai_features_dashboard_service.validate_email_ingestion_ai()


@router.get("/future-ai/sharepoint/config")
def future_ai_sharepoint_config():
    return deps.future_ai_features_dashboard_service.get_sharepoint_integration_config()


@router.get("/future-ai/sharepoint/targets")
def future_ai_sharepoint_targets():
    return deps.future_ai_features_dashboard_service.list_sharepoint_sync_targets()


@router.get("/future-ai/sharepoint/sync")
def future_ai_sharepoint_sync(site_id: str = "site-1", files_found: int = 5):
    return deps.future_ai_features_dashboard_service.sync_sharepoint_library(site_id=site_id, files_found=files_found)


@router.get("/future-ai/sharepoint/validate")
def future_ai_sharepoint_validate():
    return deps.future_ai_features_dashboard_service.validate_sharepoint_integration()


@router.get("/future-ai/teams/config")
def future_ai_teams_config():
    return deps.future_ai_features_dashboard_service.get_teams_integration_config()


@router.get("/future-ai/teams/commands")
def future_ai_teams_commands():
    return deps.future_ai_features_dashboard_service.list_teams_commands()


@router.get("/future-ai/teams/notify")
def future_ai_teams_notify(channel_id: str = "general", urgent: bool = False):
    return deps.future_ai_features_dashboard_service.post_teams_notification(channel_id=channel_id, urgent=urgent)


@router.get("/future-ai/teams/validate")
def future_ai_teams_validate():
    return deps.future_ai_features_dashboard_service.validate_teams_integration()


@router.get("/future-ai/slack/config")
def future_ai_slack_config():
    return deps.future_ai_features_dashboard_service.get_slack_integration_config()


@router.get("/future-ai/slack/commands")
def future_ai_slack_commands():
    return deps.future_ai_features_dashboard_service.list_slack_slash_commands()


@router.get("/future-ai/slack/events")
def future_ai_slack_events(event_type: str = "app_mention"):
    return deps.future_ai_features_dashboard_service.handle_slack_event(event_type=event_type)


@router.get("/future-ai/slack/validate")
def future_ai_slack_validate():
    return deps.future_ai_features_dashboard_service.validate_slack_integration()


@router.get("/future-ai/copilots/config")
def future_ai_copilots_config():
    return deps.future_ai_features_dashboard_service.get_ai_copilots_config()


@router.get("/future-ai/copilots/list")
def future_ai_copilots_list():
    return deps.future_ai_features_dashboard_service.list_ai_copilots()


@router.get("/future-ai/copilots/invoke")
def future_ai_copilots_invoke(copilot_id: str = "project_copilot", prompt_length: int = 50):
    return deps.future_ai_features_dashboard_service.invoke_ai_copilot(copilot_id=copilot_id, prompt_length=prompt_length)


@router.get("/future-ai/copilots/validate")
def future_ai_copilots_validate():
    return deps.future_ai_features_dashboard_service.validate_ai_copilots()


@router.get("/future-ai/conversational-workspace/config")
def future_ai_conversational_workspace_config():
    return deps.future_ai_features_dashboard_service.get_conversational_workspace_ai_config()


@router.get("/future-ai/conversational-workspace/tools")
def future_ai_conversational_workspace_tools():
    return deps.future_ai_features_dashboard_service.list_conversational_workspace_tools()


@router.get("/future-ai/conversational-workspace/chat")
def future_ai_conversational_workspace_chat(message: str = "Summarize today", project_id: str = "p1"):
    return deps.future_ai_features_dashboard_service.chat_conversational_workspace(message=message, project_id=project_id)


@router.get("/future-ai/conversational-workspace/validate")
def future_ai_conversational_workspace_validate():
    return deps.future_ai_features_dashboard_service.validate_conversational_workspace_ai()


@router.get("/future-ai/recovery-agents/config")
def future_ai_recovery_agents_config():
    return deps.future_ai_features_dashboard_service.get_autonomous_recovery_agents_config()


@router.get("/future-ai/recovery-agents/agents")
def future_ai_recovery_agents_agents():
    return deps.future_ai_features_dashboard_service.list_autonomous_recovery_agents()


@router.get("/future-ai/recovery-agents/triage")
def future_ai_recovery_agents_triage(failure_category: str = "transient", retry_count: int = 1):
    return deps.future_ai_features_dashboard_service.triage_autonomous_recovery_failure(failure_category=failure_category, retry_count=retry_count)


@router.get("/future-ai/recovery-agents/validate")
def future_ai_recovery_agents_validate():
    return deps.future_ai_features_dashboard_service.validate_autonomous_recovery_agents()


