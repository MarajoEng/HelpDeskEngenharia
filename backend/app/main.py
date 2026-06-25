from fastapi import FastAPI

from app.api.routes.health_routes import router as health_router
from app.core.config import get_settings


def create_application() -> FastAPI:
    settings = get_settings()
    application = FastAPI(
        title=settings.app_name,
        debug=settings.app_debug,
        version="0.1.0",
    )
    application.include_router(health_router, prefix=settings.api_prefix)
    return application


app = create_application()
