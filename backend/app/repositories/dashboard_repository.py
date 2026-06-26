from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import Float, case, func, select
from sqlalchemy.orm import Session
from sqlalchemy.sql import Select, Subquery

from app.models.enums import PriorityLevel, TicketCategory, TicketStatus
from app.models.ticket import Ticket
from app.models.ticket_category import TicketCategoryConfig
from app.models.ticket_priority import TicketPriorityConfig
from app.models.unit import Unit

_CURRENT_LATE_EXCLUDED_STATUSES = (
    TicketStatus.RESOLVED,
    TicketStatus.CLOSED,
    TicketStatus.CANCELED,
)
_FINAL_SLA_STATUSES = (
    TicketStatus.RESOLVED,
    TicketStatus.CLOSED,
    TicketStatus.CANCELED,
)

_CATEGORY_LABELS = {
    TicketCategory.FUEL_PUMP: "Fuel Pump",
    TicketCategory.FUEL_NOZZLE: "Fuel Nozzle",
    TicketCategory.ELECTRICAL: "Electrical",
    TicketCategory.PLUMBING: "Plumbing",
    TicketCategory.LEAK: "Leak",
    TicketCategory.STRUCTURE: "Structure",
    TicketCategory.ROOF: "Roof",
    TicketCategory.PAVEMENT: "Pavement",
    TicketCategory.ENVIRONMENTAL_RISK: "Environmental Risk",
    TicketCategory.OTHER: "Other",
}

_PRIORITY_LABELS = {
    PriorityLevel.LOW: "Baixa",
    PriorityLevel.MEDIUM: "Media",
    PriorityLevel.HIGH: "Alta",
    PriorityLevel.CRITICAL: "Critica",
}


def _legacy_category_name_expr(column):
    return case(*((column == key, value) for key, value in _CATEGORY_LABELS.items()), else_=column)


def _legacy_priority_name_expr(column):
    return case(*((column == key, value) for key, value in _PRIORITY_LABELS.items()), else_=column)


def _hours_diff_expr(session: Session, start_column, end_column):
    dialect = session.bind.dialect.name if session.bind is not None else ""
    if dialect == "sqlite":
        return (func.julianday(end_column) - func.julianday(start_column)) * 24.0
    return func.extract("epoch", end_column - start_column) / 3600.0


def _build_filtered_ticket_subquery(
    *,
    session: Session,
    opened_from: datetime | None = None,
    opened_to: datetime | None = None,
    unit_id: int | None = None,
    group_code: str | None = None,
    region: str | None = None,
    status: str | None = None,
    category: str | None = None,
    category_id: int | None = None,
    priority_id: int | None = None,
) -> Subquery:
    statement: Select = (
        select(
            Ticket.id.label("id"),
            Ticket.ticket_number.label("ticket_number"),
            Ticket.unit_id.label("unit_id"),
            Unit.code.label("unit_code"),
            Unit.name.label("unit_name"),
            Unit.region.label("region"),
            Ticket.title.label("title"),
            Ticket.status.label("status"),
            Ticket.category_id.label("category_id"),
            Ticket.category.label("category"),
            func.coalesce(TicketCategoryConfig.name, _legacy_category_name_expr(Ticket.category)).label("category_name"),
            Ticket.priority_id.label("priority_id"),
            Ticket.priority.label("priority"),
            func.coalesce(TicketPriorityConfig.name, _legacy_priority_name_expr(Ticket.priority)).label("priority_name"),
            TicketPriorityConfig.color.label("priority_color"),
            TicketPriorityConfig.weight.label("priority_weight"),
            Ticket.severity.label("severity"),
            Ticket.sla_due_at.label("sla_due_at"),
            Ticket.opened_at.label("opened_at"),
            Ticket.resolved_at.label("resolved_at"),
            Ticket.closed_at.label("closed_at"),
            Ticket.fuel_nozzles_stopped.label("fuel_nozzles_stopped"),
            Ticket.estimated_daily_loss.label("estimated_daily_loss"),
            Ticket.estimated_cost.label("estimated_cost"),
            Ticket.approved_cost.label("approved_cost"),
            Ticket.final_cost.label("final_cost"),
        )
        .select_from(Ticket)
        .join(Unit, Unit.id == Ticket.unit_id)
        .outerjoin(TicketCategoryConfig, TicketCategoryConfig.id == Ticket.category_id)
        .outerjoin(TicketPriorityConfig, TicketPriorityConfig.id == Ticket.priority_id)
    )

    if opened_from is not None:
        statement = statement.where(func.date(Ticket.opened_at) >= opened_from.date().isoformat())
    if opened_to is not None:
        statement = statement.where(func.date(Ticket.opened_at) <= opened_to.date().isoformat())
    if unit_id is not None:
        statement = statement.where(Ticket.unit_id == unit_id)
    if group_code is not None:
        statement = statement.where(Unit.group_code == group_code)
    if region:
        statement = statement.where(Unit.region.ilike(f"%{region.strip()}%"))
    if status is not None:
        statement = statement.where(Ticket.status == status)
    if category is not None:
        statement = statement.where(Ticket.category == category)
    if category_id is not None:
        statement = statement.where(Ticket.category_id == category_id)
    if priority_id is not None:
        statement = statement.where(Ticket.priority_id == priority_id)

    return statement.subquery()


def get_dashboard_overview_aggregates(
    session: Session,
    *,
    opened_from: datetime | None = None,
    opened_to: datetime | None = None,
    unit_id: int | None = None,
    group_code: str | None = None,
    region: str | None = None,
    status: str | None = None,
    category: str | None = None,
    category_id: int | None = None,
    priority_id: int | None = None,
) -> dict[str, object]:
    tickets = _build_filtered_ticket_subquery(
        session=session,
        opened_from=opened_from,
        opened_to=opened_to,
        unit_id=unit_id,
        group_code=group_code,
        region=region,
        status=status,
        category=category,
        category_id=category_id,
        priority_id=priority_id,
    )
    now = datetime.now(UTC)
    resolution_hours_expr = _hours_diff_expr(session, tickets.c.opened_at, tickets.c.resolved_at)
    closure_hours_expr = _hours_diff_expr(session, tickets.c.resolved_at, tickets.c.closed_at)

    statement = select(
        func.count(tickets.c.id).label("total_tickets"),
        func.sum(case((tickets.c.status == TicketStatus.OPEN, 1), else_=0)).label("open_tickets"),
        func.sum(case((tickets.c.status == TicketStatus.TRIAGE, 1), else_=0)).label("triage_tickets"),
        func.sum(case((tickets.c.status == TicketStatus.WAITING_APPROVAL, 1), else_=0)).label("waiting_approval_tickets"),
        func.sum(case((tickets.c.status == TicketStatus.APPROVED, 1), else_=0)).label("approved_tickets"),
        func.sum(case((tickets.c.status == TicketStatus.IN_PROGRESS, 1), else_=0)).label("in_progress_tickets"),
        func.sum(case((tickets.c.status == TicketStatus.RESOLVED, 1), else_=0)).label("resolved_tickets"),
        func.sum(case((tickets.c.status == TicketStatus.CLOSED, 1), else_=0)).label("closed_tickets"),
        func.sum(case((tickets.c.status == TicketStatus.CANCELED, 1), else_=0)).label("canceled_tickets"),
        func.sum(
            case(
                (
                    tickets.c.sla_due_at.is_not(None)
                    & (tickets.c.sla_due_at < now)
                    & tickets.c.status.notin_(_CURRENT_LATE_EXCLUDED_STATUSES),
                    1,
                ),
                else_=0,
            )
        ).label("late_tickets"),
        func.sum(case((tickets.c.severity == "critical", 1), else_=0)).label("critical_tickets"),
        func.sum(case((tickets.c.fuel_nozzles_stopped > 0, 1), else_=0)).label("tickets_with_fuel_nozzles_stopped"),
        func.coalesce(
            func.sum(case((tickets.c.fuel_nozzles_stopped > 0, tickets.c.fuel_nozzles_stopped), else_=0)),
            0,
        ).label("total_fuel_nozzles_stopped"),
        func.coalesce(func.sum(tickets.c.estimated_daily_loss), 0).label("estimated_daily_loss_total"),
        func.coalesce(func.sum(tickets.c.estimated_cost), 0).label("estimated_cost_total"),
        func.coalesce(func.sum(tickets.c.approved_cost), 0).label("approved_cost_total"),
        func.coalesce(func.sum(tickets.c.final_cost), 0).label("final_cost_total"),
        func.coalesce(
            func.avg(case((tickets.c.resolved_at.is_not(None), resolution_hours_expr), else_=None)),
            0.0,
        ).label("average_resolution_hours"),
        func.coalesce(
            func.avg(
                case(
                    (
                        tickets.c.resolved_at.is_not(None) & tickets.c.closed_at.is_not(None),
                        closure_hours_expr,
                    ),
                    else_=None,
                )
            ),
            0.0,
        ).label("average_closure_hours"),
    )

    row = session.execute(statement).mappings().one()
    return dict(row)


def list_units_ranking_by_tickets(
    session: Session,
    *,
    opened_from: datetime | None = None,
    opened_to: datetime | None = None,
    unit_id: int | None = None,
    group_code: str | None = None,
    region: str | None = None,
    status: str | None = None,
    category: str | None = None,
    category_id: int | None = None,
    priority_id: int | None = None,
    limit: int = 10,
) -> list[dict[str, object]]:
    tickets = _build_filtered_ticket_subquery(
        session=session,
        opened_from=opened_from,
        opened_to=opened_to,
        unit_id=unit_id,
        group_code=group_code,
        region=region,
        status=status,
        category=category,
        category_id=category_id,
        priority_id=priority_id,
    )
    now = datetime.now(UTC)
    statement = (
        select(
            tickets.c.unit_id,
            tickets.c.unit_code,
            tickets.c.unit_name,
            func.count(tickets.c.id).label("total_tickets"),
            func.sum(
                case(
                    (
                        tickets.c.sla_due_at.is_not(None)
                        & (tickets.c.sla_due_at < now)
                        & tickets.c.status.notin_(_CURRENT_LATE_EXCLUDED_STATUSES),
                        1,
                    ),
                    else_=0,
                )
            ).label("late_tickets"),
            func.sum(case((tickets.c.severity == "critical", 1), else_=0)).label("critical_tickets"),
        )
        .group_by(tickets.c.unit_id, tickets.c.unit_code, tickets.c.unit_name)
        .order_by(
            func.count(tickets.c.id).desc(),
            func.sum(
                case(
                    (
                        tickets.c.sla_due_at.is_not(None)
                        & (tickets.c.sla_due_at < now)
                        & tickets.c.status.notin_(_CURRENT_LATE_EXCLUDED_STATUSES),
                        1,
                    ),
                    else_=0,
                )
            ).desc(),
            func.sum(case((tickets.c.severity == "critical", 1), else_=0)).desc(),
            tickets.c.unit_name.asc(),
        )
        .limit(limit)
    )
    return [dict(row) for row in session.execute(statement).mappings().all()]


def list_units_ranking_by_cost(
    session: Session,
    *,
    opened_from: datetime | None = None,
    opened_to: datetime | None = None,
    unit_id: int | None = None,
    group_code: str | None = None,
    region: str | None = None,
    status: str | None = None,
    category: str | None = None,
    category_id: int | None = None,
    priority_id: int | None = None,
    limit: int = 10,
) -> list[dict[str, object]]:
    tickets = _build_filtered_ticket_subquery(
        session=session,
        opened_from=opened_from,
        opened_to=opened_to,
        unit_id=unit_id,
        group_code=group_code,
        region=region,
        status=status,
        category=category,
        category_id=category_id,
        priority_id=priority_id,
    )
    estimated_cost_total = func.coalesce(func.sum(tickets.c.estimated_cost), 0)
    final_cost_total = func.coalesce(func.sum(tickets.c.final_cost), 0)
    statement = (
        select(
            tickets.c.unit_id,
            tickets.c.unit_code,
            tickets.c.unit_name,
            estimated_cost_total.label("estimated_cost_total"),
            final_cost_total.label("final_cost_total"),
        )
        .group_by(tickets.c.unit_id, tickets.c.unit_code, tickets.c.unit_name)
        .order_by(final_cost_total.desc(), estimated_cost_total.desc(), tickets.c.unit_name.asc())
        .limit(limit)
    )
    return [dict(row) for row in session.execute(statement).mappings().all()]


def list_units_ranking_by_fuel_nozzles(
    session: Session,
    *,
    opened_from: datetime | None = None,
    opened_to: datetime | None = None,
    unit_id: int | None = None,
    group_code: str | None = None,
    region: str | None = None,
    status: str | None = None,
    category: str | None = None,
    category_id: int | None = None,
    priority_id: int | None = None,
    limit: int = 10,
) -> list[dict[str, object]]:
    tickets = _build_filtered_ticket_subquery(
        session=session,
        opened_from=opened_from,
        opened_to=opened_to,
        unit_id=unit_id,
        group_code=group_code,
        region=region,
        status=status,
        category=category,
        category_id=category_id,
        priority_id=priority_id,
    )
    total_fuel_nozzles = func.coalesce(
        func.sum(case((tickets.c.fuel_nozzles_stopped > 0, tickets.c.fuel_nozzles_stopped), else_=0)),
        0,
    )
    estimated_daily_loss_total = func.coalesce(func.sum(tickets.c.estimated_daily_loss), 0)
    statement = (
        select(
            tickets.c.unit_id,
            tickets.c.unit_code,
            tickets.c.unit_name,
            total_fuel_nozzles.label("total_fuel_nozzles_stopped"),
            estimated_daily_loss_total.label("estimated_daily_loss_total"),
        )
        .group_by(tickets.c.unit_id, tickets.c.unit_code, tickets.c.unit_name)
        .order_by(total_fuel_nozzles.desc(), estimated_daily_loss_total.desc(), tickets.c.unit_name.asc())
        .limit(limit)
    )
    return [dict(row) for row in session.execute(statement).mappings().all()]


def list_ticket_distribution_by_status(
    session: Session,
    *,
    opened_from: datetime | None = None,
    opened_to: datetime | None = None,
    unit_id: int | None = None,
    group_code: str | None = None,
    region: str | None = None,
    status: str | None = None,
    category: str | None = None,
    category_id: int | None = None,
    priority_id: int | None = None,
) -> list[dict[str, object]]:
    tickets = _build_filtered_ticket_subquery(
        session=session,
        opened_from=opened_from,
        opened_to=opened_to,
        unit_id=unit_id,
        group_code=group_code,
        region=region,
        status=status,
        category=category,
        category_id=category_id,
        priority_id=priority_id,
    )
    statement = (
        select(tickets.c.status.label("status"), func.count(tickets.c.id).label("total"))
        .group_by(tickets.c.status)
        .order_by(func.count(tickets.c.id).desc(), tickets.c.status.asc())
    )
    return [dict(row) for row in session.execute(statement).mappings().all()]


def list_ticket_distribution_by_category(
    session: Session,
    *,
    opened_from: datetime | None = None,
    opened_to: datetime | None = None,
    unit_id: int | None = None,
    group_code: str | None = None,
    region: str | None = None,
    status: str | None = None,
    category: str | None = None,
    category_id: int | None = None,
    priority_id: int | None = None,
) -> list[dict[str, object]]:
    tickets = _build_filtered_ticket_subquery(
        session=session,
        opened_from=opened_from,
        opened_to=opened_to,
        unit_id=unit_id,
        group_code=group_code,
        region=region,
        status=status,
        category=category,
        category_id=category_id,
        priority_id=priority_id,
    )
    statement = (
        select(
            tickets.c.category_id.label("category_id"),
            tickets.c.category.label("category"),
            tickets.c.category_name.label("category_name"),
            func.count(tickets.c.id).label("total"),
        )
        .group_by(tickets.c.category_id, tickets.c.category, tickets.c.category_name)
        .order_by(func.count(tickets.c.id).desc(), tickets.c.category_name.asc())
    )
    return [dict(row) for row in session.execute(statement).mappings().all()]


def list_ticket_distribution_by_priority(
    session: Session,
    *,
    opened_from: datetime | None = None,
    opened_to: datetime | None = None,
    unit_id: int | None = None,
    group_code: str | None = None,
    region: str | None = None,
    status: str | None = None,
    category: str | None = None,
    category_id: int | None = None,
    priority_id: int | None = None,
) -> list[dict[str, object]]:
    tickets = _build_filtered_ticket_subquery(
        session=session,
        opened_from=opened_from,
        opened_to=opened_to,
        unit_id=unit_id,
        group_code=group_code,
        region=region,
        status=status,
        category=category,
        category_id=category_id,
        priority_id=priority_id,
    )
    statement = (
        select(
            tickets.c.priority_id.label("priority_id"),
            tickets.c.priority.label("priority"),
            tickets.c.priority_name.label("priority_name"),
            tickets.c.priority_color.label("priority_color"),
            tickets.c.priority_weight.label("priority_weight"),
            func.count(tickets.c.id).label("total"),
        )
        .group_by(
            tickets.c.priority_id,
            tickets.c.priority,
            tickets.c.priority_name,
            tickets.c.priority_color,
            tickets.c.priority_weight,
        )
        .order_by(func.count(tickets.c.id).desc(), tickets.c.priority_name.asc())
    )
    return [dict(row) for row in session.execute(statement).mappings().all()]


def list_ticket_distribution_by_severity(
    session: Session,
    *,
    opened_from: datetime | None = None,
    opened_to: datetime | None = None,
    unit_id: int | None = None,
    group_code: str | None = None,
    region: str | None = None,
    status: str | None = None,
    category: str | None = None,
    category_id: int | None = None,
    priority_id: int | None = None,
) -> list[dict[str, object]]:
    tickets = _build_filtered_ticket_subquery(
        session=session,
        opened_from=opened_from,
        opened_to=opened_to,
        unit_id=unit_id,
        group_code=group_code,
        region=region,
        status=status,
        category=category,
        category_id=category_id,
        priority_id=priority_id,
    )
    statement = (
        select(tickets.c.severity.label("severity"), func.count(tickets.c.id).label("total"))
        .group_by(tickets.c.severity)
        .order_by(func.count(tickets.c.id).desc(), tickets.c.severity.asc())
    )
    return [dict(row) for row in session.execute(statement).mappings().all()]


def get_sla_summary_aggregates(
    session: Session,
    *,
    opened_from: datetime | None = None,
    opened_to: datetime | None = None,
    unit_id: int | None = None,
    group_code: str | None = None,
    region: str | None = None,
    status: str | None = None,
    category: str | None = None,
    category_id: int | None = None,
    priority_id: int | None = None,
) -> dict[str, object]:
    tickets = _build_filtered_ticket_subquery(
        session=session,
        opened_from=opened_from,
        opened_to=opened_to,
        unit_id=unit_id,
        group_code=group_code,
        region=region,
        status=status,
        category=category,
        category_id=category_id,
        priority_id=priority_id,
    )
    now = datetime.now(UTC)
    effective_end = func.coalesce(tickets.c.closed_at, tickets.c.resolved_at)
    statement = select(
        func.sum(
            case(
                (
                    tickets.c.sla_due_at.is_not(None)
                    & tickets.c.status.notin_(_FINAL_SLA_STATUSES)
                    & (tickets.c.sla_due_at >= now),
                    1,
                ),
                else_=0,
            )
        ).label("on_track"),
        func.sum(
            case(
                (
                    tickets.c.sla_due_at.is_not(None)
                    & tickets.c.status.notin_(_FINAL_SLA_STATUSES)
                    & (tickets.c.sla_due_at < now),
                    1,
                ),
                else_=0,
            )
        ).label("late"),
        func.sum(
            case(
                (
                    tickets.c.sla_due_at.is_not(None)
                    & tickets.c.status.in_(_FINAL_SLA_STATUSES)
                    & effective_end.is_not(None)
                    & (effective_end <= tickets.c.sla_due_at),
                    1,
                ),
                else_=0,
            )
        ).label("closed_on_time"),
        func.sum(
            case(
                (
                    tickets.c.sla_due_at.is_not(None)
                    & tickets.c.status.in_(_FINAL_SLA_STATUSES)
                    & effective_end.is_not(None)
                    & (effective_end > tickets.c.sla_due_at),
                    1,
                ),
                else_=0,
            )
        ).label("closed_late"),
    )
    row = dict(session.execute(statement).mappings().one())
    return {
        "on_track": row.get("on_track") or 0,
        "late": row.get("late") or 0,
        "closed_on_time": row.get("closed_on_time") or 0,
        "closed_late": row.get("closed_late") or 0,
    }


def list_late_tickets_preview(
    session: Session,
    *,
    opened_from: datetime | None = None,
    opened_to: datetime | None = None,
    unit_id: int | None = None,
    group_code: str | None = None,
    region: str | None = None,
    status: str | None = None,
    category: str | None = None,
    category_id: int | None = None,
    priority_id: int | None = None,
    limit: int = 10,
) -> list[dict[str, object]]:
    tickets = _build_filtered_ticket_subquery(
        session=session,
        opened_from=opened_from,
        opened_to=opened_to,
        unit_id=unit_id,
        group_code=group_code,
        region=region,
        status=status,
        category=category,
        category_id=category_id,
        priority_id=priority_id,
    )
    now = datetime.now(UTC)
    statement = (
        select(
            tickets.c.id,
            tickets.c.ticket_number,
            tickets.c.unit_code,
            tickets.c.unit_name,
            tickets.c.title,
            tickets.c.status,
            tickets.c.priority_id,
            tickets.c.priority,
            tickets.c.priority_name,
            tickets.c.priority_color,
            tickets.c.priority_weight,
            tickets.c.severity,
            tickets.c.sla_due_at,
            tickets.c.opened_at,
        )
        .where(
            tickets.c.sla_due_at.is_not(None),
            tickets.c.sla_due_at < now,
            tickets.c.status.notin_(_CURRENT_LATE_EXCLUDED_STATUSES),
        )
        .order_by(tickets.c.sla_due_at.asc(), tickets.c.opened_at.asc(), tickets.c.id.asc())
        .limit(limit)
    )
    return [dict(row) for row in session.execute(statement).mappings().all()]
