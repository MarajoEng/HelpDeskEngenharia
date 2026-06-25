from __future__ import annotations

from datetime import datetime

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.ticket import Ticket
from app.models.ticket_history import TicketHistory


def _ticket_base_query() -> Select[tuple[Ticket]]:
    return select(Ticket).options(
        selectinload(Ticket.unit),
        selectinload(Ticket.opened_by_user),
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
    if search:
        pattern = f"%{search.strip()}%"
        statement = statement.where(
            or_(
                Ticket.ticket_number.ilike(pattern),
                Ticket.title.ilike(pattern),
                Ticket.description.ilike(pattern),
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
    )
    return int(session.scalar(statement) or 0)
