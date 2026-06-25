from fastapi import FastAPI

from app.api.routes.alert_routes import router as alert_router
from app.api.routes.attachment_routes import router as attachment_router
from app.api.routes.approval_level_routes import router as approval_level_router
from app.api.routes.auth_routes import router as auth_router
from app.api.routes.dashboard_routes import router as dashboard_router
from app.api.routes.health_routes import router as health_router
from app.api.routes.supplier_routes import router as supplier_router
from app.api.routes.ticket_routes import router as ticket_router
from app.api.routes.unit_routes import router as unit_router
from app.api.routes.user_routes import router as user_router
from app.core.config import get_settings


def create_application() -> FastAPI:
    settings = get_settings()
    application = FastAPI(
        title=settings.app_name,
        debug=settings.app_debug,
        version="0.1.0",
    )
    application.include_router(alert_router, prefix=settings.api_prefix)
    application.include_router(attachment_router, prefix=settings.api_prefix)
    application.include_router(approval_level_router, prefix=settings.api_prefix)
    application.include_router(auth_router, prefix=settings.api_prefix)
    application.include_router(dashboard_router, prefix=settings.api_prefix)
    application.include_router(health_router, prefix=settings.api_prefix)
    application.include_router(supplier_router, prefix=settings.api_prefix)
    application.include_router(ticket_router, prefix=settings.api_prefix)
    application.include_router(unit_router, prefix=settings.api_prefix)
    application.include_router(user_router, prefix=settings.api_prefix)
    return application


app = create_application()
