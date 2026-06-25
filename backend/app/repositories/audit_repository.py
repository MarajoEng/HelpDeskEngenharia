from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.schemas.audit import AuditLogListParams

_SENSITIVE_KEYS = {"password", "password_hash", "token", "access_token", "secret", "authorization"}


def sanitize_metadata(data: dict) -> dict:
    return {k: v for k, v in data.items() if k.lower() not in _SENSITIVE_KEYS}


def create_audit_log(
    session: Session,
    *,
    actor_user_id: int | None,
    actor_user_name: str | None,
    action: str,
    entity_type: str,
    entity_id: int | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    metadata_json: dict | None = None,
) -> AuditLog:
    log = AuditLog(
        actor_user_id=actor_user_id,
        actor_user_name=actor_user_name,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        ip_address=ip_address,
        user_agent=user_agent,
        metadata_json=metadata_json or {},
        created_at=datetime.now(tz=timezone.utc),
    )
    session.add(log)
    session.flush()
    return log


def _apply_audit_filters(stmt, params: AuditLogListParams):
    if params.actor_user_id is not None:
        stmt = stmt.where(AuditLog.actor_user_id == params.actor_user_id)
    if params.action is not None:
        stmt = stmt.where(AuditLog.action == params.action)
    if params.entity_type is not None:
        stmt = stmt.where(AuditLog.entity_type == params.entity_type)
    if params.entity_id is not None:
        stmt = stmt.where(AuditLog.entity_id == params.entity_id)
    if params.date_from is not None:
        stmt = stmt.where(AuditLog.created_at >= params.date_from)
    if params.date_to is not None:
        stmt = stmt.where(AuditLog.created_at <= params.date_to)
    if params.search is not None:
        term = f"%{params.search}%"
        stmt = stmt.where(
            AuditLog.action.ilike(term)
            | AuditLog.entity_type.ilike(term)
            | AuditLog.actor_user_name.ilike(term)
        )
    return stmt


def list_audit_logs(session: Session, params: AuditLogListParams) -> list[AuditLog]:
    stmt = select(AuditLog)
    stmt = _apply_audit_filters(stmt, params)
    stmt = stmt.order_by(AuditLog.created_at.desc(), AuditLog.id.desc())
    offset = (params.page - 1) * params.page_size
    stmt = stmt.offset(offset).limit(params.page_size)
    return list(session.scalars(stmt).all())


def count_audit_logs(session: Session, params: AuditLogListParams) -> int:
    stmt = select(func.count()).select_from(AuditLog)
    stmt = _apply_audit_filters(stmt, params)
    return session.scalar(stmt) or 0
