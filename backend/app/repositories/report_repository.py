from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import Float, case, cast, func, select
from sqlalchemy.orm import Session, aliased
from sqlalchemy.sql import Select, Subquery

from app.models.enums import PriorityLevel, TicketCategory, TicketStatus
from app.models.supplier import Supplier
from app.models.ticket import Ticket
from app.models.ticket_category import TicketCategoryConfig
from app.models.ticket_priority import TicketPriorityConfig
from app.models.ticket_subcategory import TicketSubcategoryConfig
from app.models.ticket_type import TicketTypeConfig
from app.models.unit import Unit
from app.models.user import User

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


def _apply_report_filters(
    statement: Select,
    *,
    opened_from: datetime | None = None,
    opened_to: datetime | None = None,
    unit_id: int | None = None,
    group_code: str | None = None,
    branch_code: str | None = None,
    region: str | None = None,
    status: str | None = None,
    category: str | None = None,
    category_id: int | None = None,
    subcategory_id: int | None = None,
    type_id: int | None = None,
    priority: str | None = None,
    priority_id: int | None = None,
    severity: str | None = None,
    supplier_id: int | None = None,
    only_late: bool | None = None,
    requires_approval: bool | None = None,
    min_estimated_cost: Decimal | None = None,
    max_estimated_cost: Decimal | None = None,
) -> Select:
    if opened_from is not None:
        statement = statement.where(Ticket.opened_at >= opened_from)
    if opened_to is not None:
        statement = statement.where(Ticket.opened_at <= opened_to)
    if unit_id is not None:
        statement = statement.where(Ticket.unit_id == unit_id)
    if group_code is not None:
        statement = statement.where(Unit.group_code == group_code)
    if branch_code is not None:
        statement = statement.where(Unit.branch_code == branch_code)
    if region:
        statement = statement.where(Unit.region.ilike(f"%{region}%"))
    if status is not None:
        statement = statement.where(Ticket.status == status)
    if category is not None:
        statement = statement.where(Ticket.category == category)
    if category_id is not None:
        statement = statement.where(Ticket.category_id == category_id)
    if subcategory_id is not None:
        statement = statement.where(Ticket.subcategory_id == subcategory_id)
    if type_id is not None:
        statement = statement.where(Ticket.type_id == type_id)
    if priority is not None:
        statement = statement.where(Ticket.priority == priority)
    if priority_id is not None:
        statement = statement.where(Ticket.priority_id == priority_id)
    if severity is not None:
        statement = statement.where(Ticket.severity == severity)
    if supplier_id is not None:
        statement = statement.where(Ticket.supplier_id == supplier_id)
    if requires_approval is not None:
        statement = statement.where(Ticket.requires_approval.is_(requires_approval))
    if min_estimated_cost is not None:
        statement = statement.where(Ticket.estimated_cost >= min_estimated_cost)
    if max_estimated_cost is not None:
        statement = statement.where(Ticket.estimated_cost <= max_estimated_cost)
    if only_late:
        now = datetime.now(UTC)
        statement = statement.where(
            Ticket.sla_due_at.is_not(None),
            Ticket.sla_due_at < now,
            Ticket.status.notin_(_CURRENT_LATE_EXCLUDED_STATUSES),
        )
    return statement


def _build_ticket_report_subquery(
    session: Session,
    *,
    opened_from: datetime | None = None,
    opened_to: datetime | None = None,
    unit_id: int | None = None,
    group_code: str | None = None,
    branch_code: str | None = None,
    region: str | None = None,
    status: str | None = None,
    category: str | None = None,
    category_id: int | None = None,
    subcategory_id: int | None = None,
    type_id: int | None = None,
    priority: str | None = None,
    priority_id: int | None = None,
    severity: str | None = None,
    supplier_id: int | None = None,
    only_late: bool | None = None,
    requires_approval: bool | None = None,
    min_estimated_cost: Decimal | None = None,
    max_estimated_cost: Decimal | None = None,
) -> Subquery:
    opened_by_user = aliased(User)
    assigned_to_user = aliased(User)
    now = datetime.now(UTC)

    statement = (
        select(
            Ticket.id.label("id"),
            Ticket.ticket_number.label("ticket_number"),
            Ticket.unit_id.label("unit_id"),
            Unit.code.label("unit_code"),
            Unit.name.label("unit_name"),
            Unit.region.label("region"),
            Ticket.status.label("status"),
            Ticket.category_id.label("category_id"),
            Ticket.subcategory_id.label("subcategory_id"),
            Ticket.type_id.label("type_id"),
            Ticket.category.label("category"),
            func.coalesce(TicketCategoryConfig.name, _legacy_category_name_expr(Ticket.category)).label("category_name"),
            TicketSubcategoryConfig.name.label("subcategory_name"),
            TicketTypeConfig.name.label("type_name"),
            Ticket.priority_id.label("priority_id"),
            Ticket.priority.label("priority"),
            func.coalesce(TicketPriorityConfig.name, _legacy_priority_name_expr(Ticket.priority)).label("priority_name"),
            TicketPriorityConfig.color.label("priority_color"),
            TicketPriorityConfig.weight.label("priority_weight"),
            Ticket.severity.label("severity"),
            Ticket.opened_by_user_id.label("opened_by_user_id"),
            opened_by_user.name.label("opened_by_user_name"),
            Ticket.assigned_to_user_id.label("assigned_to_user_id"),
            assigned_to_user.name.label("assigned_to_user_name"),
            Ticket.supplier_id.label("supplier_id"),
            Supplier.name.label("supplier_name"),
            Ticket.opened_at.label("opened_at"),
            Ticket.started_at.label("started_at"),
            Ticket.resolved_at.label("resolved_at"),
            Ticket.closed_at.label("closed_at"),
            Ticket.sla_due_at.label("sla_due_at"),
            Ticket.expected_resolution_at.label("expected_resolution_at"),
            Ticket.estimated_daily_loss.label("estimated_daily_loss"),
            Ticket.estimated_cost.label("estimated_cost"),
            Ticket.approved_cost.label("approved_cost"),
            Ticket.final_cost.label("final_cost"),
            Ticket.fuel_nozzles_stopped.label("fuel_nozzles_stopped"),
            Ticket.requires_approval.label("requires_approval"),
            case(
                (
                    Ticket.sla_due_at.is_not(None)
                    & (Ticket.sla_due_at < now)
                    & Ticket.status.notin_(_CURRENT_LATE_EXCLUDED_STATUSES),
                    True,
                ),
                else_=False,
            ).label("is_late"),
            case(
                (
                    Ticket.expected_resolution_at.is_not(None)
                    & (
                        (
                            Ticket.status == TicketStatus.IN_PROGRESS
                        )
                        & (Ticket.expected_resolution_at < now)
                    ),
                    True,
                ),
                (
                    Ticket.expected_resolution_at.is_not(None)
                    & (func.coalesce(Ticket.closed_at, Ticket.resolved_at) > Ticket.expected_resolution_at),
                    True,
                ),
                else_=False,
            ).label("is_execution_late"),
        )
        .select_from(Ticket)
        .join(Unit, Unit.id == Ticket.unit_id)
        .join(opened_by_user, opened_by_user.id == Ticket.opened_by_user_id)
        .outerjoin(assigned_to_user, assigned_to_user.id == Ticket.assigned_to_user_id)
        .outerjoin(Supplier, Supplier.id == Ticket.supplier_id)
        .outerjoin(TicketCategoryConfig, TicketCategoryConfig.id == Ticket.category_id)
        .outerjoin(TicketSubcategoryConfig, TicketSubcategoryConfig.id == Ticket.subcategory_id)
        .outerjoin(TicketTypeConfig, TicketTypeConfig.id == Ticket.type_id)
        .outerjoin(TicketPriorityConfig, TicketPriorityConfig.id == Ticket.priority_id)
    )

    statement = _apply_report_filters(
        statement,
        opened_from=opened_from,
        opened_to=opened_to,
        unit_id=unit_id,
        group_code=group_code,
        branch_code=branch_code,
        region=region,
        status=status,
        category=category,
        category_id=category_id,
        subcategory_id=subcategory_id,
        type_id=type_id,
        priority=priority,
        priority_id=priority_id,
        severity=severity,
        supplier_id=supplier_id,
        only_late=only_late,
        requires_approval=requires_approval,
        min_estimated_cost=min_estimated_cost,
        max_estimated_cost=max_estimated_cost,
    )
    return statement.subquery()


def _count_rows_from_subquery(session: Session, subquery: Subquery) -> int:
    statement = select(func.count()).select_from(subquery)
    return int(session.scalar(statement) or 0)


def list_ticket_report(
    session: Session,
    *,
    page: int,
    page_size: int,
    **filters,
) -> list[dict[str, object]]:
    tickets = _build_ticket_report_subquery(session, **filters)
    statement = (
        select(tickets)
        .order_by(tickets.c.opened_at.desc(), tickets.c.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return [dict(row) for row in session.execute(statement).mappings().all()]


def count_ticket_report(session: Session, **filters) -> int:
    tickets = _build_ticket_report_subquery(session, **filters)
    return _count_rows_from_subquery(session, tickets)


def export_ticket_report_rows(session: Session, *, limit: int, **filters) -> list[dict[str, object]]:
    tickets = _build_ticket_report_subquery(session, **filters)
    statement = (
        select(tickets)
        .order_by(tickets.c.opened_at.desc(), tickets.c.id.desc())
        .limit(limit)
    )
    return [dict(row) for row in session.execute(statement).mappings().all()]


def _cost_group_statement(session: Session, tickets: Subquery) -> Select:
    final_cost_total = func.coalesce(func.sum(tickets.c.final_cost), 0)
    total_tickets = func.count(tickets.c.id)
    average_ticket_cost = cast(
        case(
            (total_tickets > 0, final_cost_total / cast(total_tickets, Float)),
            else_=0,
        ),
        Float,
    )
    return (
        select(
            tickets.c.unit_id.label("unit_id"),
            tickets.c.unit_code.label("unit_code"),
            tickets.c.unit_name.label("unit_name"),
            tickets.c.category_id.label("category_id"),
            tickets.c.category.label("category"),
            tickets.c.category_name.label("category_name"),
            tickets.c.supplier_id.label("supplier_id"),
            tickets.c.supplier_name.label("supplier_name"),
            func.coalesce(func.sum(tickets.c.estimated_cost), 0).label("estimated_cost_total"),
            func.coalesce(func.sum(tickets.c.approved_cost), 0).label("approved_cost_total"),
            final_cost_total.label("final_cost_total"),
            total_tickets.label("total_tickets"),
            average_ticket_cost.label("average_ticket_cost"),
        )
        .group_by(
            tickets.c.unit_id,
            tickets.c.unit_code,
            tickets.c.unit_name,
            tickets.c.category_id,
            tickets.c.category,
            tickets.c.category_name,
            tickets.c.supplier_id,
            tickets.c.supplier_name,
        )
    )


def list_cost_report(
    session: Session,
    *,
    page: int,
    page_size: int,
    **filters,
) -> list[dict[str, object]]:
    tickets = _build_ticket_report_subquery(session, **filters)
    grouped = (
        _cost_group_statement(session, tickets)
        .order_by(
            func.coalesce(func.sum(tickets.c.final_cost), 0).desc(),
            func.count(tickets.c.id).desc(),
            tickets.c.unit_name.asc(),
        )
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return [dict(row) for row in session.execute(grouped).mappings().all()]


def count_cost_report(session: Session, **filters) -> int:
    tickets = _build_ticket_report_subquery(session, **filters)
    grouped = _cost_group_statement(session, tickets).subquery()
    return _count_rows_from_subquery(session, grouped)


def export_cost_report_rows(session: Session, *, limit: int, **filters) -> list[dict[str, object]]:
    tickets = _build_ticket_report_subquery(session, **filters)
    grouped = (
        _cost_group_statement(session, tickets)
        .order_by(
            func.coalesce(func.sum(tickets.c.final_cost), 0).desc(),
            func.count(tickets.c.id).desc(),
            tickets.c.unit_name.asc(),
        )
        .limit(limit)
    )
    return [dict(row) for row in session.execute(grouped).mappings().all()]


def _sla_group_statement(session: Session, tickets: Subquery) -> Select:
    closure_reference = func.coalesce(tickets.c.closed_at, tickets.c.resolved_at)
    resolution_hours = _hours_diff_expr(session, tickets.c.opened_at, tickets.c.resolved_at)
    closure_hours = _hours_diff_expr(session, tickets.c.resolved_at, tickets.c.closed_at)

    total_with_sla = func.sum(case((tickets.c.sla_due_at.is_not(None), 1), else_=0))
    on_track = func.sum(
        case(
            (
                tickets.c.sla_due_at.is_not(None)
                & tickets.c.status.notin_(_FINAL_SLA_STATUSES)
                & (tickets.c.sla_due_at >= datetime.now(UTC)),
                1,
            ),
            else_=0,
        )
    )
    late = func.sum(
        case(
            (
                tickets.c.sla_due_at.is_not(None)
                & tickets.c.status.notin_(_FINAL_SLA_STATUSES)
                & (tickets.c.sla_due_at < datetime.now(UTC)),
                1,
            ),
            else_=0,
        )
    )
    closed_on_time = func.sum(
        case(
            (
                tickets.c.sla_due_at.is_not(None)
                & tickets.c.status.in_(_FINAL_SLA_STATUSES)
                & closure_reference.is_not(None)
                & (closure_reference <= tickets.c.sla_due_at),
                1,
            ),
            else_=0,
        )
    )
    closed_late = func.sum(
        case(
            (
                tickets.c.sla_due_at.is_not(None)
                & tickets.c.status.in_(_FINAL_SLA_STATUSES)
                & closure_reference.is_not(None)
                & (closure_reference > tickets.c.sla_due_at),
                1,
            ),
            else_=0,
        )
    )

    compliance_rate = cast(
        case(
            (
                total_with_sla > 0,
                ((on_track + closed_on_time) * 100.0) / cast(total_with_sla, Float),
            ),
            else_=0.0,
        ),
        Float,
    )

    return (
        select(
            tickets.c.unit_id.label("unit_id"),
            tickets.c.unit_code.label("unit_code"),
            tickets.c.unit_name.label("unit_name"),
            total_with_sla.label("total_with_sla"),
            on_track.label("on_track"),
            late.label("late"),
            closed_on_time.label("closed_on_time"),
            closed_late.label("closed_late"),
            compliance_rate.label("compliance_rate"),
            cast(
                func.coalesce(
                    func.avg(case((tickets.c.resolved_at.is_not(None), resolution_hours), else_=None)),
                    0.0,
                ),
                Float,
            ).label("average_resolution_hours"),
            cast(
                func.coalesce(
                    func.avg(
                        case(
                            (
                                tickets.c.resolved_at.is_not(None) & tickets.c.closed_at.is_not(None),
                                closure_hours,
                            ),
                            else_=None,
                        )
                    ),
                    0.0,
                ),
                Float,
            ).label("average_closure_hours"),
        )
        .group_by(tickets.c.unit_id, tickets.c.unit_code, tickets.c.unit_name)
    )


def list_sla_report(session: Session, *, page: int, page_size: int, **filters) -> list[dict[str, object]]:
    tickets = _build_ticket_report_subquery(session, **filters)
    statement = (
        _sla_group_statement(session, tickets)
        .order_by(tickets.c.unit_name.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return [dict(row) for row in session.execute(statement).mappings().all()]


def count_sla_report(session: Session, **filters) -> int:
    tickets = _build_ticket_report_subquery(session, **filters)
    grouped = _sla_group_statement(session, tickets).subquery()
    return _count_rows_from_subquery(session, grouped)


def export_sla_report_rows(session: Session, *, limit: int, **filters) -> list[dict[str, object]]:
    tickets = _build_ticket_report_subquery(session, **filters)
    statement = _sla_group_statement(session, tickets).order_by(tickets.c.unit_name.asc()).limit(limit)
    return [dict(row) for row in session.execute(statement).mappings().all()]


def _unit_group_statement(tickets: Subquery) -> Select:
    return (
        select(
            tickets.c.unit_id.label("unit_id"),
            tickets.c.unit_code.label("unit_code"),
            tickets.c.unit_name.label("unit_name"),
            tickets.c.region.label("region"),
            func.count(tickets.c.id).label("total_tickets"),
            func.sum(case((tickets.c.severity == "critical", 1), else_=0)).label("critical_tickets"),
            func.sum(case((tickets.c.is_late.is_(True), 1), else_=0)).label("late_tickets"),
            func.sum(case((tickets.c.status == TicketStatus.IN_PROGRESS, 1), else_=0)).label("in_progress_tickets"),
            func.sum(case((tickets.c.status == TicketStatus.CLOSED, 1), else_=0)).label("closed_tickets"),
            func.coalesce(func.sum(tickets.c.final_cost), 0).label("final_cost_total"),
            func.coalesce(
                func.sum(case((tickets.c.fuel_nozzles_stopped.is_not(None), tickets.c.fuel_nozzles_stopped), else_=0)),
                0,
            ).label("total_fuel_nozzles_stopped"),
            func.coalesce(func.sum(tickets.c.estimated_daily_loss), 0).label("estimated_daily_loss_total"),
        )
        .group_by(tickets.c.unit_id, tickets.c.unit_code, tickets.c.unit_name, tickets.c.region)
    )


def list_unit_report(session: Session, *, page: int, page_size: int, **filters) -> list[dict[str, object]]:
    tickets = _build_ticket_report_subquery(session, **filters)
    statement = (
        _unit_group_statement(tickets)
        .order_by(func.count(tickets.c.id).desc(), tickets.c.unit_name.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return [dict(row) for row in session.execute(statement).mappings().all()]


def count_unit_report(session: Session, **filters) -> int:
    tickets = _build_ticket_report_subquery(session, **filters)
    grouped = _unit_group_statement(tickets).subquery()
    return _count_rows_from_subquery(session, grouped)


def export_unit_report_rows(session: Session, *, limit: int, **filters) -> list[dict[str, object]]:
    tickets = _build_ticket_report_subquery(session, **filters)
    statement = (
        _unit_group_statement(tickets)
        .order_by(func.count(tickets.c.id).desc(), tickets.c.unit_name.asc())
        .limit(limit)
    )
    return [dict(row) for row in session.execute(statement).mappings().all()]


def _supplier_group_statement(session: Session, tickets: Subquery) -> Select:
    execution_end = func.coalesce(tickets.c.resolved_at, tickets.c.closed_at)
    execution_hours = _hours_diff_expr(session, tickets.c.started_at, execution_end)
    return (
        select(
            tickets.c.supplier_id.label("supplier_id"),
            tickets.c.supplier_name.label("supplier_name"),
            func.count(tickets.c.id).label("total_tickets"),
            func.sum(case((tickets.c.status == TicketStatus.IN_PROGRESS, 1), else_=0)).label("in_progress_tickets"),
            func.sum(case((tickets.c.status == TicketStatus.RESOLVED, 1), else_=0)).label("resolved_tickets"),
            func.sum(case((tickets.c.status == TicketStatus.CLOSED, 1), else_=0)).label("closed_tickets"),
            func.coalesce(func.sum(tickets.c.final_cost), 0).label("final_cost_total"),
            cast(
                func.coalesce(
                    func.avg(
                        case(
                            (
                                tickets.c.started_at.is_not(None) & execution_end.is_not(None),
                                execution_hours,
                            ),
                            else_=None,
                        )
                    ),
                    0.0,
                ),
                Float,
            ).label("average_execution_hours"),
            func.sum(case((tickets.c.is_execution_late.is_(True), 1), else_=0)).label("late_execution_tickets"),
        )
        .where(tickets.c.supplier_id.is_not(None))
        .group_by(tickets.c.supplier_id, tickets.c.supplier_name)
    )


def list_supplier_report(session: Session, *, page: int, page_size: int, **filters) -> list[dict[str, object]]:
    tickets = _build_ticket_report_subquery(session, **filters)
    statement = (
        _supplier_group_statement(session, tickets)
        .order_by(func.count(tickets.c.id).desc(), tickets.c.supplier_name.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return [dict(row) for row in session.execute(statement).mappings().all()]


def count_supplier_report(session: Session, **filters) -> int:
    tickets = _build_ticket_report_subquery(session, **filters)
    grouped = _supplier_group_statement(session, tickets).subquery()
    return _count_rows_from_subquery(session, grouped)


def export_supplier_report_rows(session: Session, *, limit: int, **filters) -> list[dict[str, object]]:
    tickets = _build_ticket_report_subquery(session, **filters)
    statement = (
        _supplier_group_statement(session, tickets)
        .order_by(func.count(tickets.c.id).desc(), tickets.c.supplier_name.asc())
        .limit(limit)
    )
    return [dict(row) for row in session.execute(statement).mappings().all()]
