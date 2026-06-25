from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db_session
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.audit import AuditLogListParams, AuditLogListResponse
from app.services.audit_service import list_audit_log_records
from app.api.dependencies import get_current_user, require_roles

router = APIRouter(prefix="/audit-logs", tags=["audit"])


def _build_audit_list_params(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    actor_user_id: int | None = Query(default=None),
    action: str | None = Query(default=None),
    entity_type: str | None = Query(default=None),
    entity_id: int | None = Query(default=None),
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
    search: str | None = Query(default=None),
) -> AuditLogListParams:
    return AuditLogListParams(
        page=page,
        page_size=page_size,
        actor_user_id=actor_user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        date_from=date_from,
        date_to=date_to,
        search=search,
    )


@router.get("", response_model=AuditLogListResponse)
def read_audit_logs(
    params: Annotated[AuditLogListParams, Depends(_build_audit_list_params)],
    _: User = Depends(require_roles(UserRole.ADMIN)),
    session: Session = Depends(get_db_session),
) -> AuditLogListResponse:
    return list_audit_log_records(session, params)
