from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import Select, func, select, update
from sqlalchemy.orm import Session, selectinload

from app.models.enums import AlertSeverity, AlertType
from app.models.ticket import Ticket
from app.models.ticket_alert import TicketAlert
from app.models.unit import Unit


def _alert_base_query() -> Select[tuple[TicketAlert]]:
    return select(TicketAlert).options(
        selectinload(TicketAlert.ticket).selectinload(Ticket.unit),
    )


def _apply_alert_filters(
    statement: Select,
    *,
    is_read: bool | None = None,
    alert_type: AlertType | None = None,
    severity: AlertSeverity | None = None,
    ticket_id: int | None = None,
    unit_id: int | None = None,
) -> Select:
    if is_read is not None:
        statement = statement.where(TicketAlert.is_read.is_(is_read))
    if alert_type is not None:
        statement = statement.where(TicketAlert.alert_type == alert_type)
    if severity is not None:
        statement = statement.where(TicketAlert.severity == severity)
    if ticket_id is not None:
        statement = statement.where(TicketAlert.ticket_id == ticket_id)
    if unit_id is not None:
        ticket_ids_stmt = select(Ticket.id).where(Ticket.unit_id == unit_id)
        statement = statement.where(TicketAlert.ticket_id.in_(ticket_ids_stmt))
    return statement


def create_alert(
    session: Session,
    *,
    ticket_id: int,
    alert_type: AlertType,
    severity: AlertSeverity,
    message: str,
) -> TicketAlert:
    alert = TicketAlert(
        ticket_id=ticket_id,
        alert_type=alert_type,
        severity=severity,
        message=message,
    )
    session.add(alert)
    session.flush()
    return alert


def get_existing_open_alert(
    session: Session,
    *,
    ticket_id: int,
    alert_type: AlertType,
    since: datetime,
) -> TicketAlert | None:
    statement = (
        select(TicketAlert)
        .where(
            TicketAlert.ticket_id == ticket_id,
            TicketAlert.alert_type == alert_type,
            TicketAlert.created_at >= since,
        )
        .limit(1)
    )
    return session.scalar(statement)


def get_alert_by_id(session: Session, alert_id: int) -> TicketAlert | None:
    statement = _alert_base_query().where(TicketAlert.id == alert_id).limit(1)
    return session.scalar(statement)


def list_alerts(
    session: Session,
    *,
    page: int,
    page_size: int,
    is_read: bool | None = None,
    alert_type: AlertType | None = None,
    severity: AlertSeverity | None = None,
    ticket_id: int | None = None,
    unit_id: int | None = None,
) -> list[TicketAlert]:
    statement = _alert_base_query()
    statement = _apply_alert_filters(
        statement,
        is_read=is_read,
        alert_type=alert_type,
        severity=severity,
        ticket_id=ticket_id,
        unit_id=unit_id,
    )
    statement = statement.order_by(TicketAlert.created_at.desc(), TicketAlert.id.desc())
    statement = statement.offset((page - 1) * page_size).limit(page_size)
    return list(session.scalars(statement).all())


def count_alerts(
    session: Session,
    *,
    is_read: bool | None = None,
    alert_type: AlertType | None = None,
    severity: AlertSeverity | None = None,
    ticket_id: int | None = None,
    unit_id: int | None = None,
) -> int:
    statement = select(func.count()).select_from(TicketAlert)
    statement = _apply_alert_filters(
        statement,
        is_read=is_read,
        alert_type=alert_type,
        severity=severity,
        ticket_id=ticket_id,
        unit_id=unit_id,
    )
    return int(session.scalar(statement) or 0)


def mark_alert_read(session: Session, alert: TicketAlert) -> TicketAlert:
    alert.is_read = True
    alert.read_at = datetime.now(UTC)
    session.add(alert)
    session.flush()
    return alert


def mark_all_alerts_read(session: Session, *, unit_id: int | None = None) -> int:
    now = datetime.now(UTC)
    statement = (
        update(TicketAlert)
        .where(TicketAlert.is_read.is_(False))
        .values(is_read=True, read_at=now)
    )
    if unit_id is not None:
        ticket_ids_stmt = select(Ticket.id).where(Ticket.unit_id == unit_id)
        statement = statement.where(TicketAlert.ticket_id.in_(ticket_ids_stmt))
    result = session.execute(statement)
    session.flush()
    return result.rowcount
