from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.config import get_settings
from app.models.enums import AlertSeverity, AlertType, TicketStatus, UserRole
from app.models.ticket import Ticket
from app.models.ticket_alert import TicketAlert
from app.repositories.alert_repository import (
    count_alerts,
    create_alert,
    get_alert_by_id,
    get_existing_open_alert,
    list_alerts,
    mark_alert_read,
    mark_all_alerts_read,
)
from app.schemas.alert import (
    RunSlaMonitorResponse,
    TicketAlertListParams,
    TicketAlertListResponse,
    TicketAlertResponse,
)
from app.schemas.pagination import calculate_pages
from app.services.exceptions import NotFoundServiceError, ValidationServiceError

logger = logging.getLogger(__name__)

_VIEW_ROLES = {UserRole.ADMIN, UserRole.ENGINEERING, UserRole.DIRECTOR, UserRole.MANAGER}
_MANAGE_ROLES = {UserRole.ADMIN, UserRole.ENGINEERING}

_FINAL_STATUSES = [TicketStatus.RESOLVED, TicketStatus.CLOSED, TicketStatus.CANCELED]


class AlertPermissionError(ValidationServiceError):
    status_code = 403
    detail = "Insufficient permissions."


class AlertNotFoundError(NotFoundServiceError):
    detail = "Alert not found."


def _to_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def _check_can_view(current_user) -> None:
    if current_user.role not in _VIEW_ROLES:
        raise AlertPermissionError


def _get_unit_id_filter(current_user) -> int | None:
    if current_user.role == UserRole.MANAGER:
        return current_user.unit_id
    return None


def _to_alert_response(alert: TicketAlert) -> TicketAlertResponse:
    return TicketAlertResponse(
        id=alert.id,
        ticket_id=alert.ticket_id,
        ticket_number=alert.ticket.ticket_number,
        unit_code=alert.ticket.unit.code,
        unit_name=alert.ticket.unit.name,
        alert_type=alert.alert_type,
        severity=alert.severity,
        message=alert.message,
        is_read=alert.is_read,
        created_at=alert.created_at,
        read_at=alert.read_at,
    )


def list_alert_records(
    session: Session,
    params: TicketAlertListParams,
    current_user,
) -> TicketAlertListResponse:
    _check_can_view(current_user)
    unit_id = params.unit_id if params.unit_id is not None else _get_unit_id_filter(current_user)

    items = list_alerts(
        session,
        page=params.page,
        page_size=params.page_size,
        is_read=params.is_read,
        alert_type=params.alert_type,
        severity=params.severity,
        ticket_id=params.ticket_id,
        unit_id=unit_id,
    )
    total = count_alerts(
        session,
        is_read=params.is_read,
        alert_type=params.alert_type,
        severity=params.severity,
        ticket_id=params.ticket_id,
        unit_id=unit_id,
    )
    return TicketAlertListResponse(
        items=[_to_alert_response(a) for a in items],
        total=total,
        page=params.page,
        page_size=params.page_size,
        pages=calculate_pages(total, params.page_size),
    )


def mark_alert_read_record(
    session: Session,
    alert_id: int,
    current_user,
) -> TicketAlertResponse:
    _check_can_view(current_user)
    alert = get_alert_by_id(session, alert_id)
    if alert is None:
        raise AlertNotFoundError
    if (
        current_user.role == UserRole.MANAGER
        and alert.ticket.unit_id != current_user.unit_id
    ):
        raise AlertPermissionError
    mark_alert_read(session, alert)
    return _to_alert_response(alert)


def mark_all_read_record(session: Session, current_user) -> int:
    _check_can_view(current_user)
    unit_id = _get_unit_id_filter(current_user)
    return mark_all_alerts_read(session, unit_id=unit_id)


def run_sla_monitoring(session: Session) -> dict:
    settings = get_settings()
    now = datetime.now(UTC)
    due_soon_threshold = now + timedelta(hours=24)
    repeat_cutoff = now - timedelta(hours=settings.sla_alert_repeat_hours)
    lookback_cutoff = now - timedelta(days=settings.sla_monitor_lookback_days)

    checked = 0
    created = 0
    skipped = 0

    # SLA late and due soon: non-final tickets with sla_due_at set
    sla_stmt = (
        select(Ticket)
        .options(selectinload(Ticket.unit))
        .where(Ticket.status.not_in(_FINAL_STATUSES))
        .where(Ticket.sla_due_at.is_not(None))
        .where(Ticket.opened_at >= lookback_cutoff)
    )
    sla_tickets = list(session.scalars(sla_stmt).all())

    for ticket in sla_tickets:
        checked += 1
        sla_due_utc = _to_utc(ticket.sla_due_at)

        if sla_due_utc < now:
            existing = get_existing_open_alert(
                session,
                ticket_id=ticket.id,
                alert_type=AlertType.SLA_LATE,
                since=repeat_cutoff,
            )
            if existing:
                skipped += 1
            else:
                create_alert(
                    session,
                    ticket_id=ticket.id,
                    alert_type=AlertType.SLA_LATE,
                    severity=AlertSeverity.CRITICAL,
                    message=(
                        f"SLA vencido em {sla_due_utc.strftime('%d/%m/%Y %H:%M')} UTC "
                        f"para o chamado {ticket.ticket_number}."
                    ),
                )
                created += 1
                logger.info("Created sla_late alert for ticket %s", ticket.ticket_number)

        elif now < sla_due_utc <= due_soon_threshold:
            existing = get_existing_open_alert(
                session,
                ticket_id=ticket.id,
                alert_type=AlertType.SLA_DUE_SOON,
                since=repeat_cutoff,
            )
            if existing:
                skipped += 1
            else:
                create_alert(
                    session,
                    ticket_id=ticket.id,
                    alert_type=AlertType.SLA_DUE_SOON,
                    severity=AlertSeverity.WARNING,
                    message=(
                        f"SLA vence em menos de 24 horas: "
                        f"{sla_due_utc.strftime('%d/%m/%Y %H:%M')} UTC "
                        f"para o chamado {ticket.ticket_number}."
                    ),
                )
                created += 1
                logger.info("Created sla_due_soon alert for ticket %s", ticket.ticket_number)

    # Execution late: in_progress tickets with expected_resolution_at expired
    exec_stmt = (
        select(Ticket)
        .options(selectinload(Ticket.unit))
        .where(Ticket.status == TicketStatus.IN_PROGRESS)
        .where(Ticket.expected_resolution_at.is_not(None))
        .where(Ticket.opened_at >= lookback_cutoff)
    )
    exec_tickets = list(session.scalars(exec_stmt).all())

    for ticket in exec_tickets:
        checked += 1
        expected_utc = _to_utc(ticket.expected_resolution_at)
        if expected_utc < now:
            existing = get_existing_open_alert(
                session,
                ticket_id=ticket.id,
                alert_type=AlertType.EXECUTION_LATE,
                since=repeat_cutoff,
            )
            if existing:
                skipped += 1
            else:
                create_alert(
                    session,
                    ticket_id=ticket.id,
                    alert_type=AlertType.EXECUTION_LATE,
                    severity=AlertSeverity.WARNING,
                    message=(
                        f"Prazo de execucao vencido em "
                        f"{expected_utc.strftime('%d/%m/%Y %H:%M')} UTC "
                        f"para o chamado {ticket.ticket_number}."
                    ),
                )
                created += 1
                logger.info("Created execution_late alert for ticket %s", ticket.ticket_number)

    session.flush()
    return {
        "checked_tickets": checked,
        "created_alerts": created,
        "skipped_duplicates": skipped,
    }
