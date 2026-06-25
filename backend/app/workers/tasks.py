from __future__ import annotations

import logging

from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="app.workers.tasks.monitor_sla_alerts")
def monitor_sla_alerts() -> dict:
    from app.core.database import get_session_factory
    from app.services.alert_service import run_sla_monitoring

    session = get_session_factory()()
    try:
        result = run_sla_monitoring(session)
        session.commit()
        logger.info("SLA monitoring completed: %s", result)
        return result
    except Exception:
        session.rollback()
        logger.exception("SLA monitoring task failed")
        raise
    finally:
        session.close()
