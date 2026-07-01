
from contextlib import asynccontextmanager


from fastapi import (
    FastAPI,
)

from fastapi.middleware.cors import (
    CORSMiddleware
)


from app.config.settings import settings
from app.auth import (
    APIAuthorizationMiddleware,
)


# ==========================================
# EXCEPTION HANDLING & LOGGING
# ==========================================

from app.exceptions import (
    GlobalExceptionHandler,
    IdempotencyMiddleware,
    RequestLoggingMiddleware,
    setup_logging,
    get_logger,
)

# ==========================================
# AUTOMATION
# ==========================================

from app.automation.scheduler import (
    scheduler
)

from app.automation.jobs import (
    register_automation_jobs
)

from app.jobs.scheduler import (
    register_qc_notification_jobs,
)

from app.dependencies import (
    IS_AUTOMATION_ENABLED,
    field_report_module_service,
    tenant_manager_module_service,
)
from app.routers import (
    actions,
    admin,
    ai_features,
    auth,
    automation,
    database_admin,
    devops,
    field_reports,
    issues,
    notifications,
    observability,
    portfolio,
    product_readiness,
    profiles,
    projects,
    reports,
    resident_portal,
    reviews,
    security,
    system,
    tenants,
    testing_utils,
)


# ==========================================
# LOGGING SETUP
# ==========================================

setup_logging()
logger = get_logger(__name__)

logger.info("OrgFlow Agent starting up")

FRONTEND_URL = str(settings.FRONTEND_URL)

FRONTEND_URLS = list(
    dict.fromkeys(
        [
            FRONTEND_URL,
            "https://elayoai.com",
            "https://www.elayoai.com",
            *settings.get_cors_extra_origins(),
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "https://localhost:3000",
            "https://127.0.0.1:3000",
            # Capacitor / APK WebView origins (static export + dev server)
            "https://localhost",
            "http://localhost",
            "capacitor://localhost",
        ]
    )
)

# ==========================================
# APP
# ==========================================

@asynccontextmanager
async def lifespan(application: FastAPI):
    startup_event()
    try:
        yield
    finally:
        shutdown_event()


app = FastAPI(lifespan=lifespan)
app.state.startup_complete = False

DEMO_ORGANIZATION_ID = (
    "bb2c760b-81cb-4e49-b057-4426406d5e71"
)


# ==========================================
# MIDDLEWARE
# ==========================================

# Add request logging middleware before exception handling
app.add_middleware(
    RequestLoggingMiddleware
)

# Add idempotency middleware for write requests
app.add_middleware(
    IdempotencyMiddleware
)

# Add global exception handler middleware (must be first)
app.add_middleware(
    GlobalExceptionHandler
)

app.add_middleware(
    APIAuthorizationMiddleware,
    public_paths={
        "/",
        "/health",
        "/healthcheck",
        "/readiness",
        "/liveness",
        "/__test/error",
        "/feature-flags",
        "/config",
        "/config/reload",
        "/secrets/rotation-status",
        "/auth/refresh",
        "/auth/exchange",
        "/auth/password-policy",
    },
)

# ==========================================
# CORS
# ==========================================

_cors_kwargs: dict = {
    "allow_origins": FRONTEND_URLS,
    "allow_credentials": True,
    "allow_methods": ["*"],
    "allow_headers": ["*"],
}

if settings.ENVIRONMENT in ("staging", "development"):
    _cors_kwargs["allow_origin_regex"] = r"https://.*\.vercel\.app"

app.add_middleware(
    CORSMiddleware,
    **_cors_kwargs,
)

# ==========================================
# AUTOMATION ENGINE
# ==========================================

def startup_event():
    if IS_AUTOMATION_ENABLED:
        register_automation_jobs()
        logger.info("[AUTOMATION] jobs registered")
    else:
        logger.info("Automation disabled by feature flag")

    if settings.FEATURE_FLAGS.enable_email_delivery:
        register_qc_notification_jobs()
        logger.info("[QC] notification jobs registered")

    if not scheduler.running:
        scheduler.start()
        logger.info("[SCHEDULER] background scheduler started")

    app.state.field_report_module_service = field_report_module_service
    app.state.tenant_manager_module_service = tenant_manager_module_service
    app.state.startup_complete = True


def shutdown_event():
    app.state.startup_complete = False
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("[SCHEDULER] background scheduler stopped")


# ==========================================
# ROUTERS
# ==========================================

app.include_router(actions.router)
app.include_router(admin.router)
app.include_router(ai_features.router)
app.include_router(auth.router)
app.include_router(automation.router)
app.include_router(database_admin.router)
app.include_router(devops.router)
app.include_router(field_reports.router)
app.include_router(issues.router)
app.include_router(notifications.router)
app.include_router(observability.router)
app.include_router(portfolio.router)
app.include_router(product_readiness.router)
app.include_router(profiles.router)
app.include_router(projects.router)
app.include_router(reports.router)
app.include_router(resident_portal.router)
app.include_router(reviews.router)
app.include_router(security.router)
app.include_router(system.router)
app.include_router(tenants.router)
app.include_router(testing_utils.router)
