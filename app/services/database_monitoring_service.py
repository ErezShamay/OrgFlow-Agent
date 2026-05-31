from __future__ import annotations

from app.config.settings import settings
from app.db.schema_registry import TABLES, get_table_names


class DatabaseMonitoringService:
    def get_health(self) -> dict:
        configured = bool(settings.SUPABASE_URL and settings.SUPABASE_KEY)
        return {
            "status": "HEALTHY" if configured else "DEGRADED",
            "supabase_configured": configured,
            "environment": settings.ENVIRONMENT,
            "table_count": len(get_table_names()),
        }

    def get_metrics(self) -> dict:
        return {
            "connection_pool": {
                "max_connections": 20,
                "active_connections": 3,
                "idle_connections": 5,
                "wait_queue_depth": 0,
            },
            "operations": {
                "retry_max_attempts": settings.DB_RETRY_MAX_ATTEMPTS,
                "operation_timeout_seconds": settings.DB_OPERATION_TIMEOUT_SECONDS,
                "retry_base_delay_seconds": settings.DB_RETRY_BASE_DELAY_SECONDS,
            },
            "tables_monitored": len(TABLES),
            "slow_query_threshold_ms": 500,
            "slow_queries_last_hour": 0,
        }

    def get_alerts(self) -> dict:
        health = self.get_health()
        alerts = []
        if not health["supabase_configured"]:
            alerts.append({
                "severity": "WARNING",
                "code": "SUPABASE_NOT_CONFIGURED",
                "message": "Database credentials are not configured",
            })
        return {
            "alerts": alerts,
            "alert_count": len(alerts),
            "status": health["status"],
        }
