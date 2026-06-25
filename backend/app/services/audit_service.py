import logging

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.user import User
from app.repositories.audit_repository import (
    count_audit_logs,
    create_audit_log,
    list_audit_logs,
    sanitize_metadata,
)
from app.schemas.pagination import calculate_pages
from app.schemas.audit import AuditLogListParams, AuditLogListResponse, AuditLogResponse

logger = logging.getLogger(__name__)


def log_action(
    session: Session,
    *,
    actor_user: User | None,
    action: str,
    entity_type: str,
    entity_id: int | None = None,
    request=None,
    metadata: dict | None = None,
) -> None:
    try:
        ip_address: str | None = None
        user_agent: str | None = None
        if request is not None:
            if hasattr(request, "client") and request.client:
                ip_address = request.client.host
            ua = request.headers.get("user-agent") if hasattr(request, "headers") else None
            if ua:
                user_agent = ua[:500]

        create_audit_log(
            session,
            actor_user_id=actor_user.id if actor_user else None,
            actor_user_name=actor_user.name if actor_user else None,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata_json=sanitize_metadata(metadata or {}),
        )
    except Exception:
        logger.warning("Audit log failed: %s on %s#%s", action, entity_type, entity_id)


def list_audit_log_records(
    session: Session,
    params: AuditLogListParams,
) -> AuditLogListResponse:
    items = list_audit_logs(session, params)
    total = count_audit_logs(session, params)
    return AuditLogListResponse(
        items=[AuditLogResponse.model_validate(item) for item in items],
        total=total,
        page=params.page,
        page_size=params.page_size,
        pages=calculate_pages(total, params.page_size),
    )
