from celery import Celery

from app.core.config import get_settings


def _make_celery() -> Celery:
    settings = get_settings()
    app = Celery(
        "helpdesk_engenharia",
        broker=settings.celery_broker_url,
        backend=settings.celery_result_backend,
        include=["app.workers.tasks"],
    )
    app.conf.update(
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        timezone="UTC",
        enable_utc=True,
    )
    return app


celery_app = _make_celery()
