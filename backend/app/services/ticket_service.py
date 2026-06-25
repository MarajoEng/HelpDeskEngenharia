from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.enums import TicketStatus, UserRole
from app.models.ticket import Ticket
from app.models.user import User
from app.repositories.supplier_repository import get_supplier_by_id as get_supplier
from app.repositories.ticket_repository import (
    count_tickets,
    create_ticket,
    create_ticket_history,
    get_ticket_by_id,
    get_ticket_detail_by_id,
    get_ticket_for_update,
    list_tickets,
    update_ticket,
)
from app.repositories.unit_repository import get_unit_by_id
from app.repositories.user_repository import count_users, get_user_by_id, list_users
from app.schemas import TicketCreate, TicketListParams, TicketListResponse, TicketResponse, TicketTriageRequest
from app.schemas.approval import ApprovalResponse
from app.schemas.ticket import (
    TicketDetailResponse,
    TicketHistoryResponse,
    TicketIndicators,
    TicketStartExecutionRequest,
    TicketProgressUpdateRequest,
    TicketSupplierSummary,
    TicketUnitSummary,
    TicketUserSummary,
)
from app.schemas.pagination import calculate_pages
from app.schemas.user import UserListParams, UserListResponse, UserResponse
from app.services.exceptions import ConflictServiceError, NotFoundServiceError, ValidationServiceError

_FINAL_STATUSES = {TicketStatus.RESOLVED, TicketStatus.CLOSED, TicketStatus.CANCELED}
_TRIAGE_ALLOWED_STATUSES = {TicketStatus.OPEN, TicketStatus.WAITING_UNIT, TicketStatus.TRIAGE}


class TicketNotFoundError(NotFoundServiceError):
    detail = "Ticket not found."


class TicketPermissionError(ValidationServiceError):
    status_code = 403
    detail = "Insufficient permissions."


class InvalidTicketUnitError(ValidationServiceError):
    detail = "Provided unit does not exist."


class InactiveTicketUnitError(ValidationServiceError):
    detail = "Provided unit is inactive."


class AssignedUserNotFoundError(ValidationServiceError):
    detail = "Assigned user not found."


class AssignedUserInactiveError(ValidationServiceError):
    detail = "Assigned user must be active."


class AssignedUserRoleError(ValidationServiceError):
    detail = "Assigned user must have admin or engineering role."


class TicketTriageTransitionError(ConflictServiceError):
    detail = "Ticket cannot be triaged from the current status."


class TicketExecutionTransitionError(ConflictServiceError):
    detail = "Ticket cannot start execution from the current status."


class TicketProgressTransitionError(ConflictServiceError):
    detail = "Ticket must be in progress to update progress."


class SupplierNotFoundError(ValidationServiceError):
    detail = "Supplier not found."


class SupplierInactiveError(ValidationServiceError):
    detail = "Supplier must be active."


def _to_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def _calculate_estimated_loss_total(
    fuel_nozzles_stopped: int | None,
    estimated_daily_loss: Decimal | None,
) -> Decimal | None:
    if fuel_nozzles_stopped is None or estimated_daily_loss is None or fuel_nozzles_stopped <= 0:
        return None
    return estimated_daily_loss * Decimal(fuel_nozzles_stopped)


def _build_ticket_number(ticket_id: int, opened_at: datetime) -> str:
    return f"ENG-{opened_at.strftime('%Y%m%d')}-{ticket_id:06d}"


def _to_ticket_response(ticket: Ticket) -> TicketResponse:
    return TicketResponse.model_validate(
        {
            "id": ticket.id,
            "ticket_number": ticket.ticket_number,
            "unit_id": ticket.unit_id,
            "opened_by_user_id": ticket.opened_by_user_id,
            "assigned_to_user_id": ticket.assigned_to_user_id,
            "category": ticket.category,
            "problem_type": ticket.problem_type,
            "title": ticket.title,
            "description": ticket.description,
            "priority": ticket.priority,
            "severity": ticket.severity,
            "status": ticket.status,
            "operational_impact": ticket.operational_impact,
            "fuel_nozzles_stopped": ticket.fuel_nozzles_stopped,
            "estimated_daily_loss": ticket.estimated_daily_loss,
            "estimated_loss_total": _calculate_estimated_loss_total(
                ticket.fuel_nozzles_stopped,
                ticket.estimated_daily_loss,
            ),
            "estimated_cost": ticket.estimated_cost,
            "approved_cost": ticket.approved_cost,
            "final_cost": ticket.final_cost,
            "requires_approval": ticket.requires_approval,
            "opened_at": ticket.opened_at,
            "triaged_at": ticket.triaged_at,
            "approved_at": ticket.approved_at,
            "started_at": ticket.started_at,
            "resolved_at": ticket.resolved_at,
            "closed_at": ticket.closed_at,
            "sla_due_at": ticket.sla_due_at,
            "expected_resolution_at": ticket.expected_resolution_at,
            "supplier_id": ticket.supplier_id,
            "created_at": ticket.created_at,
            "updated_at": ticket.updated_at,
            "unit_name": ticket.unit.name if ticket.unit else None,
            "unit_code": ticket.unit.code if ticket.unit else None,
            "opened_by_user_name": ticket.opened_by_user.name if ticket.opened_by_user else None,
            "assigned_to_user_name": ticket.assigned_to_user.name if ticket.assigned_to_user else None,
            "supplier_name": ticket.supplier.name if ticket.supplier else None,
        }
    )


def _to_approval_response(approval) -> ApprovalResponse:
    return ApprovalResponse(
        id=approval.id,
        ticket_id=approval.ticket_id,
        requested_by_user_id=approval.requested_by_user_id,
        requested_by_user_name=approval.requested_by_user.name if approval.requested_by_user else None,
        approved_by_user_id=approval.approved_by_user_id,
        approved_by_user_name=approval.approved_by_user.name if approval.approved_by_user else None,
        approval_level_id=approval.approval_level_id,
        approval_level_name=approval.approval_level.name if approval.approval_level else None,
        approval_allowed_roles=list(approval.approval_level.allowed_roles) if approval.approval_level else [],
        status=approval.status,
        amount_requested=approval.amount_requested,
        amount_approved=approval.amount_approved,
        justification=approval.justification,
        approved_at=approval.approved_at,
        created_at=approval.created_at,
    )


def _calculate_indicators(ticket: Ticket) -> TicketIndicators:
    now = datetime.now(UTC)
    opened_at = _to_utc(ticket.opened_at)
    end_time = _to_utc(ticket.closed_at) if ticket.closed_at else now
    elapsed_hours = round((end_time - opened_at).total_seconds() / 3600, 2)

    is_final = ticket.status in _FINAL_STATUSES
    sla_due = _to_utc(ticket.sla_due_at) if ticket.sla_due_at else None

    if is_final:
        sla_status: str = "closed"
        is_late = False
    elif sla_due is None:
        sla_status = "no_sla"
        is_late = False
    elif sla_due >= now:
        sla_status = "on_track"
        is_late = False
    else:
        sla_status = "late"
        is_late = True

    elapsed_execution_hours: float | None = None
    execution_is_late = False
    if ticket.started_at and ticket.status == TicketStatus.IN_PROGRESS:
        started_utc = _to_utc(ticket.started_at)
        elapsed_execution_hours = round((now - started_utc).total_seconds() / 3600, 2)
        if ticket.expected_resolution_at:
            expected_utc = _to_utc(ticket.expected_resolution_at)
            execution_is_late = expected_utc < now

    return TicketIndicators(
        estimated_loss_total=_calculate_estimated_loss_total(
            ticket.fuel_nozzles_stopped,
            ticket.estimated_daily_loss,
        ),
        elapsed_hours=elapsed_hours,
        is_late=is_late,
        sla_status=sla_status,
        elapsed_execution_hours=elapsed_execution_hours,
        execution_is_late=execution_is_late,
    )


def build_ticket_detail_response(ticket: Ticket) -> TicketDetailResponse:
    unit_summary = (
        TicketUnitSummary(
            id=ticket.unit.id,
            code=ticket.unit.code,
            name=ticket.unit.name,
            city=ticket.unit.city,
            state=ticket.unit.state,
        )
        if ticket.unit
        else None
    )

    opened_by_summary = (
        TicketUserSummary(id=ticket.opened_by_user.id, name=ticket.opened_by_user.name)
        if ticket.opened_by_user
        else None
    )

    assigned_to_summary = (
        TicketUserSummary(id=ticket.assigned_to_user.id, name=ticket.assigned_to_user.name)
        if ticket.assigned_to_user
        else None
    )

    supplier_summary = (
        TicketSupplierSummary(
            id=ticket.supplier.id,
            name=ticket.supplier.name,
            document=ticket.supplier.document,
            phone=ticket.supplier.phone,
            email=ticket.supplier.email,
            specialty=ticket.supplier.specialty,
            is_active=ticket.supplier.is_active,
        )
        if ticket.supplier
        else None
    )

    history = sorted(ticket.history_entries, key=lambda h: h.created_at)
    history_responses = [
        TicketHistoryResponse(
            id=h.id,
            user_id=h.user_id,
            user_name=h.user.name if h.user else None,
            old_status=h.old_status,
            new_status=h.new_status,
            comment=h.comment,
            created_at=h.created_at,
        )
        for h in history
    ]
    approvals = sorted(ticket.approvals, key=lambda approval: approval.created_at)
    approval_responses = [_to_approval_response(approval) for approval in approvals]

    return TicketDetailResponse(
        id=ticket.id,
        ticket_number=ticket.ticket_number,
        unit_id=ticket.unit_id,
        opened_by_user_id=ticket.opened_by_user_id,
        assigned_to_user_id=ticket.assigned_to_user_id,
        category=ticket.category,
        problem_type=ticket.problem_type,
        title=ticket.title,
        description=ticket.description,
        priority=ticket.priority,
        severity=ticket.severity,
        status=ticket.status,
        operational_impact=ticket.operational_impact,
        fuel_nozzles_stopped=ticket.fuel_nozzles_stopped,
        estimated_daily_loss=ticket.estimated_daily_loss,
        estimated_cost=ticket.estimated_cost,
        approved_cost=ticket.approved_cost,
        final_cost=ticket.final_cost,
        requires_approval=ticket.requires_approval,
        opened_at=ticket.opened_at,
        triaged_at=ticket.triaged_at,
        approved_at=ticket.approved_at,
        started_at=ticket.started_at,
        resolved_at=ticket.resolved_at,
        closed_at=ticket.closed_at,
        sla_due_at=ticket.sla_due_at,
        expected_resolution_at=ticket.expected_resolution_at,
        supplier_id=ticket.supplier_id,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
        unit=unit_summary,
        opened_by=opened_by_summary,
        assigned_to=assigned_to_summary,
        supplier=supplier_summary,
        history=history_responses,
        approvals=approval_responses,
        indicators=_calculate_indicators(ticket),
    )


def _ensure_unit_available(session: Session, unit_id: int):
    unit = get_unit_by_id(session, unit_id)
    if unit is None:
        raise InvalidTicketUnitError
    if not unit.is_active:
        raise InactiveTicketUnitError
    return unit


def _enforce_create_permission(current_user: User, unit_id: int) -> None:
    if current_user.role == UserRole.SUPPLIER:
        raise TicketPermissionError
    if current_user.role == UserRole.MANAGER and current_user.unit_id != unit_id:
        raise TicketPermissionError
    if current_user.role not in {
        UserRole.ADMIN,
        UserRole.MANAGER,
        UserRole.ENGINEERING,
        UserRole.DIRECTOR,
    }:
        raise TicketPermissionError


def _restrict_unit_scope(current_user: User, params: TicketListParams) -> TicketListParams:
    if current_user.role == UserRole.MANAGER:
        return params.model_copy(update={"unit_id": current_user.unit_id})
    return params


def _can_view_ticket(current_user: User, ticket: Ticket) -> bool:
    if current_user.role in {UserRole.ADMIN, UserRole.ENGINEERING, UserRole.DIRECTOR}:
        return True
    if current_user.role == UserRole.MANAGER and current_user.unit_id == ticket.unit_id:
        return True
    return False


def create_ticket_record(session: Session, payload: TicketCreate, current_user: User) -> TicketResponse:
    _enforce_create_permission(current_user, payload.unit_id)
    _ensure_unit_available(session, payload.unit_id)

    opened_at = datetime.now(UTC)
    ticket = create_ticket(
        session,
        ticket_number=f"PENDING-{opened_at.strftime('%Y%m%d%H%M%S%f')}",
        unit_id=payload.unit_id,
        opened_by_user_id=current_user.id,
        assigned_to_user_id=None,
        category=payload.category,
        problem_type=payload.problem_type,
        title=payload.title,
        description=payload.description,
        priority=payload.priority,
        severity=payload.severity,
        status=TicketStatus.OPEN,
        operational_impact=payload.operational_impact,
        fuel_nozzles_stopped=payload.fuel_nozzles_stopped,
        estimated_daily_loss=payload.estimated_daily_loss,
        estimated_cost=payload.estimated_cost,
        approved_cost=None,
        final_cost=None,
        requires_approval=payload.requires_approval,
        opened_at=opened_at,
        triaged_at=None,
        approved_at=None,
        started_at=None,
        resolved_at=None,
        closed_at=None,
        sla_due_at=None,
        expected_resolution_at=None,
        supplier_id=None,
    )
    ticket.ticket_number = _build_ticket_number(ticket.id, opened_at)
    create_ticket_history(
        session,
        ticket_id=ticket.id,
        user_id=current_user.id,
        old_status=None,
        new_status=TicketStatus.OPEN,
        comment="Chamado aberto",
    )
    session.commit()

    persisted_ticket = get_ticket_by_id(session, ticket.id)
    if persisted_ticket is None:
        raise TicketNotFoundError
    return _to_ticket_response(persisted_ticket)


def get_ticket_or_404(session: Session, ticket_id: int) -> Ticket:
    ticket = get_ticket_by_id(session, ticket_id)
    if ticket is None:
        raise TicketNotFoundError
    return ticket


def list_ticket_records(session: Session, params: TicketListParams, current_user: User) -> TicketListResponse:
    if current_user.role == UserRole.SUPPLIER:
        raise TicketPermissionError

    scoped_params = _restrict_unit_scope(current_user, params)
    total = count_tickets(
        session,
        unit_id=scoped_params.unit_id,
        status=scoped_params.status,
        category=scoped_params.category,
        priority=scoped_params.priority,
        severity=scoped_params.severity,
        requires_approval=scoped_params.requires_approval,
        opened_from=scoped_params.opened_from,
        opened_to=scoped_params.opened_to,
        search=scoped_params.search,
        only_late=scoped_params.only_late,
        has_fuel_nozzles_stopped=scoped_params.has_fuel_nozzles_stopped,
        min_estimated_cost=scoped_params.min_estimated_cost,
        max_estimated_cost=scoped_params.max_estimated_cost,
        queue=scoped_params.queue,
    )
    items = list_tickets(
        session,
        page=scoped_params.page,
        page_size=scoped_params.page_size,
        unit_id=scoped_params.unit_id,
        status=scoped_params.status,
        category=scoped_params.category,
        priority=scoped_params.priority,
        severity=scoped_params.severity,
        requires_approval=scoped_params.requires_approval,
        opened_from=scoped_params.opened_from,
        opened_to=scoped_params.opened_to,
        search=scoped_params.search,
        only_late=scoped_params.only_late,
        has_fuel_nozzles_stopped=scoped_params.has_fuel_nozzles_stopped,
        min_estimated_cost=scoped_params.min_estimated_cost,
        max_estimated_cost=scoped_params.max_estimated_cost,
        queue=scoped_params.queue,
    )
    return TicketListResponse(
        items=[_to_ticket_response(ticket) for ticket in items],
        total=total,
        page=scoped_params.page,
        page_size=scoped_params.page_size,
        pages=calculate_pages(total, scoped_params.page_size),
    )


def get_ticket_detail(session: Session, ticket_id: int, current_user: User) -> TicketDetailResponse:
    if current_user.role == UserRole.SUPPLIER:
        raise TicketPermissionError

    ticket = get_ticket_detail_by_id(session, ticket_id)
    if ticket is None:
        raise TicketNotFoundError
    if not _can_view_ticket(current_user, ticket):
        raise TicketPermissionError
    return build_ticket_detail_response(ticket)


def _enforce_triage_permission(current_user: User) -> None:
    if current_user.role not in {UserRole.ADMIN, UserRole.ENGINEERING}:
        raise TicketPermissionError


def _enforce_execution_permission(current_user: User) -> None:
    if current_user.role not in {UserRole.ADMIN, UserRole.ENGINEERING}:
        raise TicketPermissionError


def _validate_assigned_user(session: Session, user_id: int | None) -> User | None:
    if user_id is None:
        return None

    user = get_user_by_id(session, user_id)
    if user is None:
        raise AssignedUserNotFoundError
    if not user.is_active:
        raise AssignedUserInactiveError
    if user.role not in {UserRole.ADMIN, UserRole.ENGINEERING}:
        raise AssignedUserRoleError
    return user


def _validate_supplier(session: Session, supplier_id: int | None) -> None:
    if supplier_id is None:
        return
    supplier = get_supplier(session, supplier_id)
    if supplier is None:
        raise SupplierNotFoundError
    if not supplier.is_active:
        raise SupplierInactiveError


def triage_ticket(
    session: Session,
    ticket_id: int,
    payload: TicketTriageRequest,
    current_user: User,
) -> TicketDetailResponse:
    _enforce_triage_permission(current_user)

    ticket = get_ticket_for_update(session, ticket_id)
    if ticket is None:
        raise TicketNotFoundError

    if ticket.status not in _TRIAGE_ALLOWED_STATUSES:
        raise TicketTriageTransitionError

    payload_fields = payload.model_fields_set
    changes: dict[str, object] = {}

    if "assigned_to_user_id" in payload_fields:
        _validate_assigned_user(session, payload.assigned_to_user_id)
        changes["assigned_to_user_id"] = payload.assigned_to_user_id

    if "priority" in payload_fields and payload.priority is not None:
        changes["priority"] = payload.priority

    if "severity" in payload_fields and payload.severity is not None:
        changes["severity"] = payload.severity

    if "requires_approval" in payload_fields and payload.requires_approval is not None:
        changes["requires_approval"] = payload.requires_approval

    if "sla_due_at" in payload_fields:
        changes["sla_due_at"] = payload.sla_due_at

    old_status = ticket.status
    if ticket.status in {TicketStatus.OPEN, TicketStatus.WAITING_UNIT}:
        changes["status"] = TicketStatus.TRIAGE
        if ticket.triaged_at is None:
            changes["triaged_at"] = datetime.now(UTC)

    if changes:
        update_ticket(session, ticket, **changes)

    create_ticket_history(
        session,
        ticket_id=ticket.id,
        user_id=current_user.id,
        old_status=old_status,
        new_status=TicketStatus.TRIAGE,
        comment=payload.technical_comment,
    )
    session.commit()

    persisted_ticket = get_ticket_detail_by_id(session, ticket.id)
    if persisted_ticket is None:
        raise TicketNotFoundError
    return build_ticket_detail_response(persisted_ticket)


def start_ticket_execution(
    session: Session,
    ticket_id: int,
    payload: TicketStartExecutionRequest,
    current_user: User,
) -> TicketDetailResponse:
    _enforce_execution_permission(current_user)

    ticket = get_ticket_for_update(session, ticket_id)
    if ticket is None:
        raise TicketNotFoundError

    valid_from_no_approval = {TicketStatus.TRIAGE}
    valid_from_with_approval = {TicketStatus.APPROVED}
    valid_statuses = valid_from_no_approval | valid_from_with_approval

    if ticket.status not in valid_statuses:
        raise TicketExecutionTransitionError

    if ticket.status == TicketStatus.TRIAGE and ticket.requires_approval:
        raise TicketExecutionTransitionError

    if ticket.status == TicketStatus.APPROVED and not ticket.requires_approval:
        raise TicketExecutionTransitionError

    _validate_assigned_user(session, payload.assigned_to_user_id)
    _validate_supplier(session, payload.supplier_id)

    now = datetime.now(UTC)
    changes: dict[str, object] = {
        "status": TicketStatus.IN_PROGRESS,
        "started_at": now,
    }
    if payload.assigned_to_user_id is not None:
        changes["assigned_to_user_id"] = payload.assigned_to_user_id
    if payload.supplier_id is not None:
        changes["supplier_id"] = payload.supplier_id
    if payload.expected_resolution_at is not None:
        changes["expected_resolution_at"] = payload.expected_resolution_at

    old_status = ticket.status
    update_ticket(session, ticket, **changes)
    create_ticket_history(
        session,
        ticket_id=ticket.id,
        user_id=current_user.id,
        old_status=old_status,
        new_status=TicketStatus.IN_PROGRESS,
        comment=payload.execution_comment,
    )
    session.commit()

    persisted_ticket = get_ticket_detail_by_id(session, ticket.id)
    if persisted_ticket is None:
        raise TicketNotFoundError
    return build_ticket_detail_response(persisted_ticket)


def update_ticket_progress(
    session: Session,
    ticket_id: int,
    payload: TicketProgressUpdateRequest,
    current_user: User,
) -> TicketDetailResponse:
    _enforce_execution_permission(current_user)

    ticket = get_ticket_for_update(session, ticket_id)
    if ticket is None:
        raise TicketNotFoundError

    if ticket.status != TicketStatus.IN_PROGRESS:
        raise TicketProgressTransitionError

    _validate_assigned_user(session, payload.assigned_to_user_id)
    _validate_supplier(session, payload.supplier_id)

    changes: dict[str, object] = {}
    payload_fields = payload.model_fields_set

    if "expected_resolution_at" in payload_fields:
        changes["expected_resolution_at"] = payload.expected_resolution_at
    if "estimated_cost" in payload_fields and payload.estimated_cost is not None:
        changes["estimated_cost"] = payload.estimated_cost
    if "supplier_id" in payload_fields and payload.supplier_id is not None:
        changes["supplier_id"] = payload.supplier_id
    if "assigned_to_user_id" in payload_fields and payload.assigned_to_user_id is not None:
        changes["assigned_to_user_id"] = payload.assigned_to_user_id

    if changes:
        update_ticket(session, ticket, **changes)

    create_ticket_history(
        session,
        ticket_id=ticket.id,
        user_id=current_user.id,
        old_status=TicketStatus.IN_PROGRESS,
        new_status=TicketStatus.IN_PROGRESS,
        comment=payload.progress_comment,
    )
    session.commit()

    persisted_ticket = get_ticket_detail_by_id(session, ticket.id)
    if persisted_ticket is None:
        raise TicketNotFoundError
    return build_ticket_detail_response(persisted_ticket)


def list_ticket_triage_assignees(
    session: Session,
    params: UserListParams,
    current_user: User,
) -> UserListResponse:
    _enforce_triage_permission(current_user)

    eligible_roles = [UserRole.ADMIN, UserRole.ENGINEERING]
    total = count_users(
        session,
        search=params.search,
        roles=eligible_roles,
        is_active=True,
    )
    items = list_users(
        session,
        page=params.page,
        page_size=params.page_size,
        search=params.search,
        roles=eligible_roles,
        is_active=True,
        sort=params.sort,
    )
    return UserListResponse(
        items=[UserResponse.model_validate(user) for user in items],
        total=total,
        page=params.page,
        page_size=params.page_size,
        pages=calculate_pages(total, params.page_size),
    )
