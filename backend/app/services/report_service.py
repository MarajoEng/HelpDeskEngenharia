from __future__ import annotations

import csv
from io import StringIO
from typing import Any

from sqlalchemy.orm import Session

from app.models.enums import UserRole
from app.models.user import User
from app.schemas.pagination import calculate_pages
from app.schemas.report import (
    CostReportItem,
    CostReportResponse,
    ReportFilters,
    SlaReportItem,
    SlaReportResponse,
    SupplierReportItem,
    SupplierReportResponse,
    TicketReportItem,
    TicketReportResponse,
    UnitReportItem,
    UnitReportResponse,
)
from app.repositories.report_repository import (
    count_cost_report,
    count_sla_report,
    count_supplier_report,
    count_ticket_report,
    count_unit_report,
    export_cost_report_rows,
    export_sla_report_rows,
    export_supplier_report_rows,
    export_ticket_report_rows,
    export_unit_report_rows,
    list_cost_report,
    list_sla_report,
    list_supplier_report,
    list_ticket_report,
    list_unit_report,
)
from app.services.audit_service import log_action
from app.services.exceptions import ValidationServiceError


class ReportPermissionError(ValidationServiceError):
    status_code = 403
    detail = "Insufficient permissions."


class ReportExportLimitError(ValidationServiceError):
    detail = "A exportacao excede o limite configurado para esta operacao."


def _enforce_report_permission(current_user: User) -> None:
    if current_user.role == UserRole.SUPPLIER:
        raise ReportPermissionError
    if current_user.role not in {
        UserRole.ADMIN,
        UserRole.DIRECTOR,
        UserRole.ENGINEERING,
        UserRole.MANAGER,
    }:
        raise ReportPermissionError


def _scope_report_filters(current_user: User, filters: ReportFilters) -> ReportFilters:
    if current_user.role != UserRole.MANAGER:
        return filters
    if current_user.unit_id is None:
        raise ReportPermissionError("Manager user must be linked to a unit.")
    if filters.unit_id is not None and filters.unit_id != current_user.unit_id:
        raise ReportPermissionError("Manager can only access report data from their own unit.")
    return filters.model_copy(update={"unit_id": current_user.unit_id})


def _build_filter_kwargs(filters: ReportFilters) -> dict[str, object]:
    return {
        "opened_from": filters.opened_from_datetime(),
        "opened_to": filters.opened_to_datetime(),
        "unit_id": filters.unit_id,
        "region": filters.region,
        "status": filters.status,
        "category": filters.category,
        "category_id": filters.category_id,
        "subcategory_id": filters.subcategory_id,
        "type_id": filters.type_id,
        "priority": filters.priority,
        "priority_id": filters.priority_id,
        "severity": filters.severity,
        "supplier_id": filters.supplier_id,
        "only_late": filters.only_late,
        "requires_approval": filters.requires_approval,
        "min_estimated_cost": filters.min_estimated_cost,
        "max_estimated_cost": filters.max_estimated_cost,
    }


def _audit_report_view(
    session: Session,
    *,
    current_user: User,
    report_type: str,
    filters: ReportFilters,
    total: int,
    page_count: int,
) -> None:
    log_action(
        session,
        actor_user=current_user,
        action="report_viewed",
        entity_type="report",
        metadata={
            "report_type": report_type,
            "filters": filters.to_audit_metadata(),
            "total_items": total,
            "returned_items": page_count,
        },
    )


def _audit_report_export(
    session: Session,
    *,
    current_user: User,
    report_type: str,
    filters: ReportFilters,
    exported_count: int,
) -> None:
    log_action(
        session,
        actor_user=current_user,
        action="report_exported",
        entity_type="report",
        metadata={
            "report_type": report_type,
            "filters": filters.to_audit_metadata(),
            "exported_items": exported_count,
        },
    )


def get_ticket_report(session: Session, filters: ReportFilters, current_user: User) -> TicketReportResponse:
    _enforce_report_permission(current_user)
    scoped_filters = _scope_report_filters(current_user, filters)
    filter_kwargs = _build_filter_kwargs(scoped_filters)
    items = [TicketReportItem.model_validate(item) for item in list_ticket_report(session, page=scoped_filters.page, page_size=scoped_filters.page_size, **filter_kwargs)]
    total = count_ticket_report(session, **filter_kwargs)
    _audit_report_view(
        session,
        current_user=current_user,
        report_type="tickets",
        filters=scoped_filters,
        total=total,
        page_count=len(items),
    )
    return TicketReportResponse(
        items=items,
        total=total,
        page=scoped_filters.page,
        page_size=scoped_filters.page_size,
        pages=calculate_pages(total, scoped_filters.page_size),
    )


def get_cost_report(session: Session, filters: ReportFilters, current_user: User) -> CostReportResponse:
    _enforce_report_permission(current_user)
    scoped_filters = _scope_report_filters(current_user, filters)
    filter_kwargs = _build_filter_kwargs(scoped_filters)
    items = [CostReportItem.model_validate(item) for item in list_cost_report(session, page=scoped_filters.page, page_size=scoped_filters.page_size, **filter_kwargs)]
    total = count_cost_report(session, **filter_kwargs)
    _audit_report_view(session, current_user=current_user, report_type="costs", filters=scoped_filters, total=total, page_count=len(items))
    return CostReportResponse(
        items=items,
        total=total,
        page=scoped_filters.page,
        page_size=scoped_filters.page_size,
        pages=calculate_pages(total, scoped_filters.page_size),
    )


def get_sla_report(session: Session, filters: ReportFilters, current_user: User) -> SlaReportResponse:
    _enforce_report_permission(current_user)
    scoped_filters = _scope_report_filters(current_user, filters)
    filter_kwargs = _build_filter_kwargs(scoped_filters)
    items = [SlaReportItem.model_validate(item) for item in list_sla_report(session, page=scoped_filters.page, page_size=scoped_filters.page_size, **filter_kwargs)]
    total = count_sla_report(session, **filter_kwargs)
    _audit_report_view(session, current_user=current_user, report_type="sla", filters=scoped_filters, total=total, page_count=len(items))
    return SlaReportResponse(
        items=items,
        total=total,
        page=scoped_filters.page,
        page_size=scoped_filters.page_size,
        pages=calculate_pages(total, scoped_filters.page_size),
    )


def get_unit_report(session: Session, filters: ReportFilters, current_user: User) -> UnitReportResponse:
    _enforce_report_permission(current_user)
    scoped_filters = _scope_report_filters(current_user, filters)
    filter_kwargs = _build_filter_kwargs(scoped_filters)
    items = [UnitReportItem.model_validate(item) for item in list_unit_report(session, page=scoped_filters.page, page_size=scoped_filters.page_size, **filter_kwargs)]
    total = count_unit_report(session, **filter_kwargs)
    _audit_report_view(session, current_user=current_user, report_type="units", filters=scoped_filters, total=total, page_count=len(items))
    return UnitReportResponse(
        items=items,
        total=total,
        page=scoped_filters.page,
        page_size=scoped_filters.page_size,
        pages=calculate_pages(total, scoped_filters.page_size),
    )


def get_supplier_report(session: Session, filters: ReportFilters, current_user: User) -> SupplierReportResponse:
    _enforce_report_permission(current_user)
    scoped_filters = _scope_report_filters(current_user, filters)
    filter_kwargs = _build_filter_kwargs(scoped_filters)
    items = [SupplierReportItem.model_validate(item) for item in list_supplier_report(session, page=scoped_filters.page, page_size=scoped_filters.page_size, **filter_kwargs)]
    total = count_supplier_report(session, **filter_kwargs)
    _audit_report_view(session, current_user=current_user, report_type="suppliers", filters=scoped_filters, total=total, page_count=len(items))
    return SupplierReportResponse(
        items=items,
        total=total,
        page=scoped_filters.page,
        page_size=scoped_filters.page_size,
        pages=calculate_pages(total, scoped_filters.page_size),
    )


def _serialize_csv_value(value: Any) -> Any:
    if hasattr(value, "value"):
        return value.value
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


def _write_csv(headers: list[str], rows: list[dict[str, Any]]) -> str:
    buffer = StringIO()
    writer = csv.DictWriter(buffer, fieldnames=headers)
    writer.writeheader()
    for row in rows:
        writer.writerow({header: _serialize_csv_value(row.get(header)) for header in headers})
    return buffer.getvalue()


def _guard_export_limit(total: int, max_rows: int) -> None:
    if total > max_rows:
        raise ReportExportLimitError(
            f"A exportacao excede o limite de {max_rows} linhas. Refine os filtros e tente novamente."
        )


def export_ticket_report_csv(
    session: Session,
    filters: ReportFilters,
    current_user: User,
    *,
    max_rows: int,
) -> str:
    _enforce_report_permission(current_user)
    scoped_filters = _scope_report_filters(current_user, filters)
    filter_kwargs = _build_filter_kwargs(scoped_filters)
    total = count_ticket_report(session, **filter_kwargs)
    _guard_export_limit(total, max_rows)
    rows = export_ticket_report_rows(session, limit=max_rows, **filter_kwargs)
    _audit_report_export(session, current_user=current_user, report_type="tickets", filters=scoped_filters, exported_count=len(rows))
    headers = [
        "ticket_number",
        "unit_code",
        "unit_name",
        "status",
        "category",
        "category_id",
        "category_name",
        "subcategory_id",
        "subcategory_name",
        "type_id",
        "type_name",
        "priority",
        "priority_id",
        "priority_name",
        "priority_color",
        "priority_weight",
        "severity",
        "opened_by_user_name",
        "assigned_to_user_name",
        "supplier_name",
        "opened_at",
        "resolved_at",
        "closed_at",
        "sla_due_at",
        "is_late",
        "estimated_cost",
        "approved_cost",
        "final_cost",
        "fuel_nozzles_stopped",
        "requires_approval",
    ]
    return _write_csv(headers, rows)


def export_cost_report_csv(
    session: Session,
    filters: ReportFilters,
    current_user: User,
    *,
    max_rows: int,
) -> str:
    _enforce_report_permission(current_user)
    scoped_filters = _scope_report_filters(current_user, filters)
    filter_kwargs = _build_filter_kwargs(scoped_filters)
    total = count_cost_report(session, **filter_kwargs)
    _guard_export_limit(total, max_rows)
    rows = export_cost_report_rows(session, limit=max_rows, **filter_kwargs)
    _audit_report_export(session, current_user=current_user, report_type="costs", filters=scoped_filters, exported_count=len(rows))
    headers = [
        "unit_code",
        "unit_name",
        "category",
        "category_id",
        "category_name",
        "supplier_name",
        "estimated_cost_total",
        "approved_cost_total",
        "final_cost_total",
        "total_tickets",
        "average_ticket_cost",
    ]
    return _write_csv(headers, rows)


def export_sla_report_csv(
    session: Session,
    filters: ReportFilters,
    current_user: User,
    *,
    max_rows: int,
) -> str:
    _enforce_report_permission(current_user)
    scoped_filters = _scope_report_filters(current_user, filters)
    filter_kwargs = _build_filter_kwargs(scoped_filters)
    total = count_sla_report(session, **filter_kwargs)
    _guard_export_limit(total, max_rows)
    rows = export_sla_report_rows(session, limit=max_rows, **filter_kwargs)
    _audit_report_export(session, current_user=current_user, report_type="sla", filters=scoped_filters, exported_count=len(rows))
    headers = [
        "unit_code",
        "unit_name",
        "total_with_sla",
        "on_track",
        "late",
        "closed_on_time",
        "closed_late",
        "compliance_rate",
        "average_resolution_hours",
        "average_closure_hours",
    ]
    return _write_csv(headers, rows)


def export_unit_report_csv(
    session: Session,
    filters: ReportFilters,
    current_user: User,
    *,
    max_rows: int,
) -> str:
    _enforce_report_permission(current_user)
    scoped_filters = _scope_report_filters(current_user, filters)
    filter_kwargs = _build_filter_kwargs(scoped_filters)
    total = count_unit_report(session, **filter_kwargs)
    _guard_export_limit(total, max_rows)
    rows = export_unit_report_rows(session, limit=max_rows, **filter_kwargs)
    _audit_report_export(session, current_user=current_user, report_type="units", filters=scoped_filters, exported_count=len(rows))
    headers = [
        "unit_code",
        "unit_name",
        "region",
        "total_tickets",
        "critical_tickets",
        "late_tickets",
        "in_progress_tickets",
        "closed_tickets",
        "final_cost_total",
        "total_fuel_nozzles_stopped",
        "estimated_daily_loss_total",
    ]
    return _write_csv(headers, rows)


def export_supplier_report_csv(
    session: Session,
    filters: ReportFilters,
    current_user: User,
    *,
    max_rows: int,
) -> str:
    _enforce_report_permission(current_user)
    scoped_filters = _scope_report_filters(current_user, filters)
    filter_kwargs = _build_filter_kwargs(scoped_filters)
    total = count_supplier_report(session, **filter_kwargs)
    _guard_export_limit(total, max_rows)
    rows = export_supplier_report_rows(session, limit=max_rows, **filter_kwargs)
    _audit_report_export(session, current_user=current_user, report_type="suppliers", filters=scoped_filters, exported_count=len(rows))
    headers = [
        "supplier_name",
        "total_tickets",
        "in_progress_tickets",
        "resolved_tickets",
        "closed_tickets",
        "final_cost_total",
        "average_execution_hours",
        "late_execution_tickets",
    ]
    return _write_csv(headers, rows)
