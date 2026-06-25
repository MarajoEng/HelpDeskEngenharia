from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.enums import TicketStatus, UserRole
from app.models.ticket import Ticket
from app.models.user import User
from app.repositories.ticket_repository import count_tickets, create_ticket, create_ticket_history, get_ticket_by_id, list_tickets
from app.repositories.unit_repository import get_unit_by_id
from app.schemas import TicketCreate, TicketListParams, TicketListResponse, TicketResponse
from app.schemas.pagination import calculate_pages
from app.services.exceptions import NotFoundServiceError, ValidationServiceError


class TicketNotFoundError(NotFoundServiceError):
    detail = "Ticket not found."


class TicketPermissionError(ValidationServiceError):
    status_code = 403
    detail = "Insufficient permissions."


class InvalidTicketUnitError(ValidationServiceError):
    detail = "Provided unit does not exist."


class InactiveTicketUnitError(ValidationServiceError):
    detail = "Provided unit is inactive."


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
            "created_at": ticket.created_at,
            "updated_at": ticket.updated_at,
            "unit_name": ticket.unit.name if ticket.unit else None,
            "unit_code": ticket.unit.code if ticket.unit else None,
            "opened_by_user_name": ticket.opened_by_user.name if ticket.opened_by_user else None,
        }
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
    )
    return TicketListResponse(
        items=[_to_ticket_response(ticket) for ticket in items],
        total=total,
        page=scoped_params.page,
        page_size=scoped_params.page_size,
        pages=calculate_pages(total, scoped_params.page_size),
    )


def get_ticket_detail(session: Session, ticket_id: int, current_user: User) -> TicketResponse:
    if current_user.role == UserRole.SUPPLIER:
        raise TicketPermissionError

    ticket = get_ticket_or_404(session, ticket_id)
    if not _can_view_ticket(current_user, ticket):
        raise TicketPermissionError
    return _to_ticket_response(ticket)
