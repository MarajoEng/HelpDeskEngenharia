from __future__ import annotations

from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.enums import UserRole
from app.models.user import User
from app.repositories.dashboard_repository import (
    get_dashboard_overview_aggregates,
    get_sla_summary_aggregates,
    list_late_tickets_preview,
    list_ticket_distribution_by_category,
    list_ticket_distribution_by_priority,
    list_ticket_distribution_by_severity,
    list_ticket_distribution_by_status,
    list_units_ranking_by_cost,
    list_units_ranking_by_fuel_nozzles,
    list_units_ranking_by_tickets,
)
from app.schemas.dashboard import (
    DashboardOverviewParams,
    DashboardOverviewResponse,
    ExecutiveCards,
    LateTicketsPreviewItem,
    SlaSummary,
    TicketsByCategoryItem,
    TicketsByPriorityItem,
    TicketsBySeverityItem,
    TicketsByStatusItem,
    UnitCostRankingItem,
    UnitFuelNozzlesRankingItem,
    UnitTicketsRankingItem,
)
from app.services.exceptions import ValidationServiceError


class DashboardPermissionError(ValidationServiceError):
    status_code = 403
    detail = "Insufficient permissions."


def _to_float(value: Decimal | float | int | None) -> float:
    if value is None:
        return 0.0
    return round(float(value), 2)


def _safe_rate(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round((numerator / denominator) * 100, 2)


def _enforce_dashboard_permission(current_user: User) -> None:
    if current_user.role == UserRole.SUPPLIER:
        raise DashboardPermissionError
    if current_user.role not in {
        UserRole.ADMIN,
        UserRole.DIRECTOR,
        UserRole.ENGINEERING,
        UserRole.MANAGER,
    }:
        raise DashboardPermissionError


def _scope_dashboard_filters(current_user: User, params: DashboardOverviewParams) -> DashboardOverviewParams:
    if current_user.role != UserRole.MANAGER:
        return params
    if current_user.unit_id is None:
        raise DashboardPermissionError("Manager user must be linked to a unit.")
    if params.unit_id is not None and params.unit_id != current_user.unit_id:
        raise DashboardPermissionError("Manager can only access dashboard data from their own unit.")
    return params.model_copy(update={"unit_id": current_user.unit_id})


def get_dashboard_overview(
    session: Session,
    params: DashboardOverviewParams,
    current_user: User,
) -> DashboardOverviewResponse:
    _enforce_dashboard_permission(current_user)
    scoped_params = _scope_dashboard_filters(current_user, params)

    filter_kwargs = {
        "opened_from": scoped_params.opened_from_datetime(),
        "opened_to": scoped_params.opened_to_datetime(),
        "unit_id": scoped_params.unit_id,
        "group_code": scoped_params.group_code,
        "region": scoped_params.region,
        "status": scoped_params.status,
        "category": scoped_params.category,
        "category_id": scoped_params.category_id,
        "priority_id": scoped_params.priority_id,
    }

    overview_raw = get_dashboard_overview_aggregates(session, **filter_kwargs)
    sla_raw = get_sla_summary_aggregates(session, **filter_kwargs)

    total_with_sla = (
        int(sla_raw["on_track"])
        + int(sla_raw["late"])
        + int(sla_raw["closed_on_time"])
        + int(sla_raw["closed_late"])
    )
    compliance_rate = _safe_rate(
        int(sla_raw["on_track"]) + int(sla_raw["closed_on_time"]),
        total_with_sla,
    )

    executive_cards = ExecutiveCards(
        total_open=int(overview_raw["open_tickets"] or 0),
        total_late=int(overview_raw["late_tickets"] or 0),
        total_critical=int(overview_raw["critical_tickets"] or 0),
        total_in_progress=int(overview_raw["in_progress_tickets"] or 0),
        total_fuel_nozzles_stopped=int(overview_raw["total_fuel_nozzles_stopped"] or 0),
        estimated_daily_loss_total=_to_float(overview_raw["estimated_daily_loss_total"]),
        final_cost_total=_to_float(overview_raw["final_cost_total"]),
        sla_compliance_rate=compliance_rate,
    )

    return DashboardOverviewResponse(
        total_tickets=int(overview_raw["total_tickets"] or 0),
        open_tickets=int(overview_raw["open_tickets"] or 0),
        triage_tickets=int(overview_raw["triage_tickets"] or 0),
        waiting_approval_tickets=int(overview_raw["waiting_approval_tickets"] or 0),
        approved_tickets=int(overview_raw["approved_tickets"] or 0),
        in_progress_tickets=int(overview_raw["in_progress_tickets"] or 0),
        resolved_tickets=int(overview_raw["resolved_tickets"] or 0),
        closed_tickets=int(overview_raw["closed_tickets"] or 0),
        canceled_tickets=int(overview_raw["canceled_tickets"] or 0),
        late_tickets=int(overview_raw["late_tickets"] or 0),
        critical_tickets=int(overview_raw["critical_tickets"] or 0),
        tickets_with_fuel_nozzles_stopped=int(overview_raw["tickets_with_fuel_nozzles_stopped"] or 0),
        total_fuel_nozzles_stopped=int(overview_raw["total_fuel_nozzles_stopped"] or 0),
        estimated_daily_loss_total=_to_float(overview_raw["estimated_daily_loss_total"]),
        estimated_cost_total=_to_float(overview_raw["estimated_cost_total"]),
        approved_cost_total=_to_float(overview_raw["approved_cost_total"]),
        final_cost_total=_to_float(overview_raw["final_cost_total"]),
        average_resolution_hours=_to_float(overview_raw["average_resolution_hours"]),
        average_closure_hours=_to_float(overview_raw["average_closure_hours"]),
        sla_compliance_rate=compliance_rate,
        executive_cards=executive_cards,
        ranking_units_by_tickets=[
            UnitTicketsRankingItem.model_validate(item)
            for item in list_units_ranking_by_tickets(session, **filter_kwargs)
        ],
        ranking_units_by_cost=[
            UnitCostRankingItem(
                unit_id=int(item["unit_id"]),
                unit_code=str(item["unit_code"]),
                unit_name=str(item["unit_name"]),
                estimated_cost_total=_to_float(item["estimated_cost_total"]),
                final_cost_total=_to_float(item["final_cost_total"]),
            )
            for item in list_units_ranking_by_cost(session, **filter_kwargs)
        ],
        ranking_units_by_fuel_nozzles=[
            UnitFuelNozzlesRankingItem(
                unit_id=int(item["unit_id"]),
                unit_code=str(item["unit_code"]),
                unit_name=str(item["unit_name"]),
                total_fuel_nozzles_stopped=int(item["total_fuel_nozzles_stopped"] or 0),
                estimated_daily_loss_total=_to_float(item["estimated_daily_loss_total"]),
            )
            for item in list_units_ranking_by_fuel_nozzles(session, **filter_kwargs)
        ],
        tickets_by_status=[
            TicketsByStatusItem.model_validate(item)
            for item in list_ticket_distribution_by_status(session, **filter_kwargs)
        ],
        tickets_by_category=[
            TicketsByCategoryItem.model_validate(item)
            for item in list_ticket_distribution_by_category(session, **filter_kwargs)
        ],
        tickets_by_priority=[
            TicketsByPriorityItem.model_validate(item)
            for item in list_ticket_distribution_by_priority(session, **filter_kwargs)
        ],
        tickets_by_severity=[
            TicketsBySeverityItem.model_validate(item)
            for item in list_ticket_distribution_by_severity(session, **filter_kwargs)
        ],
        sla_summary=SlaSummary(
            total_with_sla=total_with_sla,
            on_track=int(sla_raw["on_track"]),
            late=int(sla_raw["late"]),
            closed_on_time=int(sla_raw["closed_on_time"]),
            closed_late=int(sla_raw["closed_late"]),
            compliance_rate=compliance_rate,
        ),
        late_tickets_preview=[
            LateTicketsPreviewItem.model_validate(item)
            for item in list_late_tickets_preview(session, **filter_kwargs)
        ],
    )
