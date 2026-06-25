from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.database import get_db_session
from app.models.enums import AlertSeverity, AlertType
from app.models.user import User
from app.schemas.alert import (
    RunSlaMonitorResponse,
    TicketAlertListParams,
    TicketAlertListResponse,
    TicketAlertResponse,
)
from app.services.alert_service import (
    list_alert_records,
    mark_alert_read_record,
    mark_all_read_record,
    run_sla_monitoring,
)
from app.services.exceptions import ServiceError

router = APIRouter(prefix="/alerts", tags=["alerts"])


def _raise_service_error(error: ServiceError) -> None:
    raise HTTPException(status_code=error.status_code, detail=error.detail)


def _build_list_params(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    is_read: bool | None = Query(default=None),
    alert_type: AlertType | None = Query(default=None),
    severity: AlertSeverity | None = Query(default=None),
    ticket_id: int | None = Query(default=None, ge=1),
    unit_id: int | None = Query(default=None, ge=1),
) -> TicketAlertListParams:
    return TicketAlertListParams(
        page=page,
        page_size=page_size,
        is_read=is_read,
        alert_type=alert_type,
        severity=severity,
        ticket_id=ticket_id,
        unit_id=unit_id,
    )


@router.get("", response_model=TicketAlertListResponse)
def read_alerts(
    params: Annotated[TicketAlertListParams, Depends(_build_list_params)],
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> TicketAlertListResponse:
    try:
        return list_alert_records(session, params, current_user)
    except ServiceError as error:
        _raise_service_error(error)


@router.patch("/read-all")
def mark_read_all(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> dict:
    try:
        count = mark_all_read_record(session, current_user)
        session.commit()
        return {"marked_read": count}
    except ServiceError as error:
        _raise_service_error(error)


@router.patch("/{alert_id}/read", response_model=TicketAlertResponse)
def mark_read(
    alert_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> TicketAlertResponse:
    try:
        result = mark_alert_read_record(session, alert_id, current_user)
        session.commit()
        return result
    except ServiceError as error:
        _raise_service_error(error)


@router.post("/run-sla-monitor", response_model=RunSlaMonitorResponse)
def trigger_sla_monitor(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> RunSlaMonitorResponse:
    from app.services.alert_service import AlertPermissionError
    from app.models.enums import UserRole

    if current_user.role not in {UserRole.ADMIN, UserRole.ENGINEERING}:
        raise HTTPException(status_code=403, detail="Insufficient permissions.")
    try:
        result = run_sla_monitoring(session)
        session.commit()
        return RunSlaMonitorResponse(**result)
    except ServiceError as error:
        _raise_service_error(error)
