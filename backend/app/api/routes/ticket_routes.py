from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.database import get_db_session
from app.models.enums import PriorityLevel, TicketCategory, TicketSeverity, TicketStatus
from app.models.user import User
from app.schemas import TicketCreate, TicketListParams, TicketListResponse, TicketResponse, TicketTriageRequest
from app.schemas.approval import ApprovalDecisionRequest, ApprovalRequestCreate
from app.schemas.ticket import (
    TicketCloseRequest,
    TicketDetailResponse,
    TicketProgressUpdateRequest,
    TicketResolveRequest,
    TicketStartExecutionRequest,
)
from app.schemas.user import UserListParams, UserListResponse
from app.services.approval_service import decide_ticket_approval, request_ticket_approval
from app.services.audit_service import log_action
from app.services.exceptions import ServiceError
from app.services.ticket_service import (
    close_ticket,
    create_ticket_record,
    get_ticket_detail,
    list_ticket_records,
    list_ticket_triage_assignees,
    resolve_ticket,
    start_ticket_execution,
    triage_ticket,
    update_ticket_progress,
)


router = APIRouter(prefix="/tickets", tags=["tickets"])


def _raise_service_error(error: ServiceError) -> None:
    raise HTTPException(status_code=error.status_code, detail=error.detail)


def _build_list_params(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    unit_id: int | None = Query(default=None, ge=1),
    status_filter: TicketStatus | None = Query(default=None, alias="status"),
    category: TicketCategory | None = Query(default=None),
    priority: PriorityLevel | None = Query(default=None),
    severity: TicketSeverity | None = Query(default=None),
    requires_approval: bool | None = Query(default=None),
    opened_from: datetime | None = Query(default=None),
    opened_to: datetime | None = Query(default=None),
    search: str | None = Query(default=None),
    only_late: bool | None = Query(default=None),
    has_fuel_nozzles_stopped: bool | None = Query(default=None),
    min_estimated_cost: Decimal | None = Query(default=None, ge=0),
    max_estimated_cost: Decimal | None = Query(default=None, ge=0),
    queue: Literal["engineering"] | None = Query(default=None),
) -> TicketListParams:
    return TicketListParams(
        page=page,
        page_size=page_size,
        unit_id=unit_id,
        status=status_filter,
        category=category,
        priority=priority,
        severity=severity,
        requires_approval=requires_approval,
        opened_from=opened_from,
        opened_to=opened_to,
        search=search,
        only_late=only_late,
        has_fuel_nozzles_stopped=has_fuel_nozzles_stopped,
        min_estimated_cost=min_estimated_cost,
        max_estimated_cost=max_estimated_cost,
        queue=queue,
    )


def _build_triage_assignees_params(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: str | None = Query(default=None),
) -> UserListParams:
    return UserListParams(
        page=page,
        page_size=page_size,
        search=search,
        sort="name_asc",
    )


@router.post("", response_model=TicketResponse, status_code=status.HTTP_201_CREATED)
def create_ticket(
    payload: TicketCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> TicketResponse:
    try:
        result = create_ticket_record(session, payload, current_user)
    except ServiceError as error:
        _raise_service_error(error)

    log_action(session, actor_user=current_user, action="ticket_created", entity_type="ticket", entity_id=result.id, request=request, metadata={"category": payload.category.value, "priority": payload.priority.value})
    session.commit()
    return result


@router.get("", response_model=TicketListResponse)
def read_tickets(
    params: Annotated[TicketListParams, Depends(_build_list_params)],
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> TicketListResponse:
    try:
        return list_ticket_records(session, params, current_user)
    except ServiceError as error:
        _raise_service_error(error)


@router.get("/triage-assignees", response_model=UserListResponse)
def read_ticket_triage_assignees(
    params: Annotated[UserListParams, Depends(_build_triage_assignees_params)],
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> UserListResponse:
    try:
        return list_ticket_triage_assignees(session, params, current_user)
    except ServiceError as error:
        _raise_service_error(error)


@router.get("/{ticket_id}", response_model=TicketDetailResponse)
def read_ticket(
    ticket_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> TicketDetailResponse:
    try:
        return get_ticket_detail(session, ticket_id, current_user)
    except ServiceError as error:
        _raise_service_error(error)


@router.patch("/{ticket_id}/triage", response_model=TicketDetailResponse)
def patch_ticket_triage(
    ticket_id: int,
    payload: TicketTriageRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> TicketDetailResponse:
    try:
        result = triage_ticket(session, ticket_id, payload, current_user)
    except ServiceError as error:
        _raise_service_error(error)

    log_action(session, actor_user=current_user, action="ticket_triaged", entity_type="ticket", entity_id=ticket_id, request=request)
    session.commit()
    return result


@router.post("/{ticket_id}/approval-request", response_model=TicketDetailResponse)
def create_ticket_approval_request(
    ticket_id: int,
    payload: ApprovalRequestCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> TicketDetailResponse:
    try:
        result = request_ticket_approval(session, ticket_id, payload, current_user)
    except ServiceError as error:
        _raise_service_error(error)

    log_action(session, actor_user=current_user, action="approval_requested", entity_type="ticket", entity_id=ticket_id, request=request)
    session.commit()
    return result


@router.patch("/{ticket_id}/approval-decision", response_model=TicketDetailResponse)
def patch_ticket_approval_decision(
    ticket_id: int,
    payload: ApprovalDecisionRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> TicketDetailResponse:
    try:
        result = decide_ticket_approval(session, ticket_id, payload, current_user)
    except ServiceError as error:
        _raise_service_error(error)

    log_action(session, actor_user=current_user, action="approval_decided", entity_type="ticket", entity_id=ticket_id, request=request, metadata={"decision": str(payload.decision)})
    session.commit()
    return result


@router.patch("/{ticket_id}/start-execution", response_model=TicketDetailResponse)
def patch_ticket_start_execution(
    ticket_id: int,
    payload: TicketStartExecutionRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> TicketDetailResponse:
    try:
        result = start_ticket_execution(session, ticket_id, payload, current_user)
    except ServiceError as error:
        _raise_service_error(error)

    log_action(session, actor_user=current_user, action="execution_started", entity_type="ticket", entity_id=ticket_id, request=request)
    session.commit()
    return result


@router.patch("/{ticket_id}/progress", response_model=TicketDetailResponse)
def patch_ticket_progress(
    ticket_id: int,
    payload: TicketProgressUpdateRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> TicketDetailResponse:
    try:
        result = update_ticket_progress(session, ticket_id, payload, current_user)
    except ServiceError as error:
        _raise_service_error(error)

    log_action(session, actor_user=current_user, action="progress_updated", entity_type="ticket", entity_id=ticket_id, request=request)
    session.commit()
    return result


@router.patch("/{ticket_id}/resolve", response_model=TicketDetailResponse)
def patch_ticket_resolve(
    ticket_id: int,
    payload: TicketResolveRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> TicketDetailResponse:
    try:
        result = resolve_ticket(session, ticket_id, payload, current_user)
    except ServiceError as error:
        _raise_service_error(error)

    log_action(session, actor_user=current_user, action="ticket_resolved", entity_type="ticket", entity_id=ticket_id, request=request)
    session.commit()
    return result


@router.patch("/{ticket_id}/close", response_model=TicketDetailResponse)
def patch_ticket_close(
    ticket_id: int,
    payload: TicketCloseRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> TicketDetailResponse:
    try:
        result = close_ticket(session, ticket_id, payload, current_user)
    except ServiceError as error:
        _raise_service_error(error)

    log_action(session, actor_user=current_user, action="ticket_closed", entity_type="ticket", entity_id=ticket_id, request=request)
    session.commit()
    return result
