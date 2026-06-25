from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.enums import TicketStatus
from app.models.ticket import Ticket
from app.models.approval import Approval
from app.models.supplier import Supplier
from app.models.ticket_history import TicketHistory
from app.models.unit import Unit

_FINAL_STATUSES = [TicketStatus.RESOLVED, TicketStatus.CLOSED, TicketStatus.CANCELED]
_ENGINEERING_QUEUE_STATUSES = [
    TicketStatus.OPEN,
    TicketStatus.TRIAGE,
    TicketStatus.WAITING_UNIT,
]


def _ticket_base_query() -> Select[tuple[Ticket]]:
    return select(Ticket).options(
        selectinload(Ticket.unit),
        selectinload(Ticket.opened_by_user),
        selectinload(Ticket.assigned_to_user),
        selectinload(Ticket.supplier),
    )


def _ticket_detail_query() -> Select[tuple[Ticket]]:
    return select(Ticket).options(
        selectinload(Ticket.unit),
        selectinload(Ticket.opened_by_user),
        selectinload(Ticket.assigned_to_user),
        selectinload(Ticket.supplier),
        selectinload(Ticket.history_entries).selectinload(TicketHistory.user),
        selectinload(Ticket.approvals).selectinload(Approval.requested_by_user),
        selectinload(Ticket.approvals).selectinload(Approval.approved_by_user),
        selectinload(Ticket.approvals).selectinload(Approval.approval_level),
    )


def _apply_ticket_filters(
    statement: Select[tuple[Ticket]] | Select[tuple[int]],
    *,
    unit_id: int | None = None,
    status: str | None = None,
    category: str | None = None,
    priority: str | None = None,
    severity: str | None = None,
    requires_approval: bool | None = None,
    opened_from: datetime | None = None,
    opened_to: datetime | None = None,
    search: str | None = None,
    only_late: bool | None = None,
    has_fuel_nozzles_stopped: bool | None = None,
    min_estimated_cost: Decimal | None = None,
    max_estimated_cost: Decimal | None = None,
    queue: str | None = None,
) -> Select[tuple[Ticket]] | Select[tuple[int]]:
    if unit_id is not None:
        statement = statement.where(Ticket.unit_id == unit_id)
    if status is not None:
        statement = statement.where(Ticket.status == status)
    if category is not None:
        statement = statement.where(Ticket.category == category)
    if priority is not None:
        statement = statement.where(Ticket.priority == priority)
    if severity is not None:
        statement = statement.where(Ticket.severity == severity)
    if requires_approval is not None:
        statement = statement.where(Ticket.requires_approval.is_(requires_approval))
    if opened_from is not None:
        statement = statement.where(Ticket.opened_at >= opened_from)
    if opened_to is not None:
        statement = statement.where(Ticket.opened_at <= opened_to)
    if only_late:
        now = datetime.now(UTC)
        statement = statement.where(
            Ticket.sla_due_at.isnot(None),
            Ticket.sla_due_at < now,
            Ticket.status.notin_(_FINAL_STATUSES),
        )
    if has_fuel_nozzles_stopped:
        statement = statement.where(
            Ticket.fuel_nozzles_stopped.isnot(None),
            Ticket.fuel_nozzles_stopped > 0,
        )
    if min_estimated_cost is not None:
        statement = statement.where(Ticket.estimated_cost >= min_estimated_cost)
    if max_estimated_cost is not None:
        statement = statement.where(Ticket.estimated_cost <= max_estimated_cost)
    if queue == "engineering":
        statement = statement.where(Ticket.status.in_(_ENGINEERING_QUEUE_STATUSES))
    if search:
        term = search.strip()
        pattern = f"%{term}%"
        unit_subq = (
            select(Unit.id)
            .where(
                Unit.id == Ticket.unit_id,
                or_(Unit.name.ilike(pattern), Unit.code.ilike(pattern)),
            )
            .correlate(Ticket)
            .exists()
        )
        statement = statement.where(
            or_(
                Ticket.ticket_number.ilike(pattern),
                Ticket.title.ilike(pattern),
                Ticket.description.ilike(pattern),
                Ticket.problem_type.ilike(pattern),
                unit_subq,
            )
        )
    return statement


def create_ticket(session: Session, **payload: object) -> Ticket:
    ticket = Ticket(**payload)
    session.add(ticket)
    session.flush()
    return ticket


def create_ticket_history(
    session: Session,
    *,
    ticket_id: int,
    user_id: int,
    old_status: str | None,
    new_status: str,
    comment: str | None,
) -> TicketHistory:
    history = TicketHistory(
        ticket_id=ticket_id,
        user_id=user_id,
        old_status=old_status,
        new_status=new_status,
        comment=comment,
    )
    session.add(history)
    session.flush()
    return history


def get_ticket_by_id(session: Session, ticket_id: int) -> Ticket | None:
    statement = _ticket_base_query().where(Ticket.id == ticket_id).limit(1)
    return session.scalar(statement)


def get_ticket_for_update(session: Session, ticket_id: int) -> Ticket | None:
    statement = select(Ticket).where(Ticket.id == ticket_id).limit(1)
    return session.scalar(statement)


def get_ticket_detail_by_id(session: Session, ticket_id: int) -> Ticket | None:
    statement = _ticket_detail_query().where(Ticket.id == ticket_id).limit(1)
    return session.scalar(statement)


def get_ticket_by_number(session: Session, ticket_number: str) -> Ticket | None:
    statement = _ticket_base_query().where(Ticket.ticket_number == ticket_number).limit(1)
    return session.scalar(statement)


def list_tickets(
    session: Session,
    *,
    page: int,
    page_size: int,
    unit_id: int | None = None,
    status: str | None = None,
    category: str | None = None,
    priority: str | None = None,
    severity: str | None = None,
    requires_approval: bool | None = None,
    opened_from: datetime | None = None,
    opened_to: datetime | None = None,
    search: str | None = None,
    only_late: bool | None = None,
    has_fuel_nozzles_stopped: bool | None = None,
    min_estimated_cost: Decimal | None = None,
    max_estimated_cost: Decimal | None = None,
    queue: str | None = None,
) -> list[Ticket]:
    statement = _ticket_base_query()
    statement = _apply_ticket_filters(
        statement,
        unit_id=unit_id,
        status=status,
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
    statement = statement.order_by(Ticket.opened_at.desc(), Ticket.id.desc())
    statement = statement.offset((page - 1) * page_size).limit(page_size)
    return list(session.scalars(statement).all())


def count_tickets(
    session: Session,
    *,
    unit_id: int | None = None,
    status: str | None = None,
    category: str | None = None,
    priority: str | None = None,
    severity: str | None = None,
    requires_approval: bool | None = None,
    opened_from: datetime | None = None,
    opened_to: datetime | None = None,
    search: str | None = None,
    only_late: bool | None = None,
    has_fuel_nozzles_stopped: bool | None = None,
    min_estimated_cost: Decimal | None = None,
    max_estimated_cost: Decimal | None = None,
    queue: str | None = None,
) -> int:
    statement = select(func.count()).select_from(Ticket)
    statement = _apply_ticket_filters(
        statement,
        unit_id=unit_id,
        status=status,
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
    return int(session.scalar(statement) or 0)


def update_ticket(session: Session, ticket: Ticket, **changes: object) -> Ticket:
    for field, value in changes.items():
        setattr(ticket, field, value)

    session.add(ticket)
    session.flush()
    return ticket
