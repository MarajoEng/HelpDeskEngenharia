from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.config import get_settings
from app.core.database import get_db_session
from app.models.enums import PriorityLevel, TicketCategory, TicketSeverity, TicketStatus
from app.models.user import User
from app.schemas.report import (
    CostReportResponse,
    ReportFilters,
    SlaReportResponse,
    SupplierReportResponse,
    TicketReportResponse,
    UnitReportResponse,
)
from app.services.exceptions import ServiceError
from app.services.report_service import (
    export_cost_report_csv,
    export_sla_report_csv,
    export_supplier_report_csv,
    export_ticket_report_csv,
    export_unit_report_csv,
    get_cost_report,
    get_sla_report,
    get_supplier_report,
    get_ticket_report,
    get_unit_report,
)

router = APIRouter(prefix="/reports", tags=["reports"])


def _raise_service_error(error: ServiceError) -> None:
    raise HTTPException(status_code=error.status_code, detail=error.detail)


def _build_report_filters(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    unit_id: int | None = Query(default=None, ge=1),
    region: str | None = Query(default=None),
    status_filter: TicketStatus | None = Query(default=None, alias="status"),
    category: TicketCategory | None = Query(default=None),
    category_id: int | None = Query(default=None, ge=1),
    subcategory_id: int | None = Query(default=None, ge=1),
    type_id: int | None = Query(default=None, ge=1),
    priority: PriorityLevel | None = Query(default=None),
    priority_id: int | None = Query(default=None, ge=1),
    severity: TicketSeverity | None = Query(default=None),
    supplier_id: int | None = Query(default=None, ge=1),
    only_late: bool | None = Query(default=None),
    requires_approval: bool | None = Query(default=None),
    min_estimated_cost: Decimal | None = Query(default=None, ge=0),
    max_estimated_cost: Decimal | None = Query(default=None, ge=0),
) -> ReportFilters:
    return ReportFilters(
        page=page,
        page_size=page_size,
        date_from=date_from,
        date_to=date_to,
        unit_id=unit_id,
        region=region,
        status=status_filter,
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


def _csv_response(filename: str, content: str) -> Response:
    return Response(
        content=content.encode("utf-8"),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/tickets", response_model=TicketReportResponse)
def read_ticket_report(
    filters: Annotated[ReportFilters, Depends(_build_report_filters)],
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> TicketReportResponse:
    try:
        response = get_ticket_report(session, filters, current_user)
        session.commit()
        return response
    except ServiceError as error:
        session.rollback()
        _raise_service_error(error)


@router.get("/costs", response_model=CostReportResponse)
def read_cost_report(
    filters: Annotated[ReportFilters, Depends(_build_report_filters)],
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> CostReportResponse:
    try:
        response = get_cost_report(session, filters, current_user)
        session.commit()
        return response
    except ServiceError as error:
        session.rollback()
        _raise_service_error(error)


@router.get("/sla", response_model=SlaReportResponse)
def read_sla_report(
    filters: Annotated[ReportFilters, Depends(_build_report_filters)],
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> SlaReportResponse:
    try:
        response = get_sla_report(session, filters, current_user)
        session.commit()
        return response
    except ServiceError as error:
        session.rollback()
        _raise_service_error(error)


@router.get("/units", response_model=UnitReportResponse)
def read_unit_report(
    filters: Annotated[ReportFilters, Depends(_build_report_filters)],
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> UnitReportResponse:
    try:
        response = get_unit_report(session, filters, current_user)
        session.commit()
        return response
    except ServiceError as error:
        session.rollback()
        _raise_service_error(error)


@router.get("/suppliers", response_model=SupplierReportResponse)
def read_supplier_report(
    filters: Annotated[ReportFilters, Depends(_build_report_filters)],
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> SupplierReportResponse:
    try:
        response = get_supplier_report(session, filters, current_user)
        session.commit()
        return response
    except ServiceError as error:
        session.rollback()
        _raise_service_error(error)


@router.get("/tickets/export.csv")
def export_ticket_report_endpoint(
    filters: Annotated[ReportFilters, Depends(_build_report_filters)],
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> Response:
    try:
        content = export_ticket_report_csv(
            session,
            filters,
            current_user,
            max_rows=get_settings().report_export_max_rows,
        )
        session.commit()
        return _csv_response("chamados.csv", content)
    except ServiceError as error:
        session.rollback()
        _raise_service_error(error)


@router.get("/costs/export.csv")
def export_cost_report_endpoint(
    filters: Annotated[ReportFilters, Depends(_build_report_filters)],
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> Response:
    try:
        content = export_cost_report_csv(
            session,
            filters,
            current_user,
            max_rows=get_settings().report_export_max_rows,
        )
        session.commit()
        return _csv_response("custos.csv", content)
    except ServiceError as error:
        session.rollback()
        _raise_service_error(error)


@router.get("/sla/export.csv")
def export_sla_report_endpoint(
    filters: Annotated[ReportFilters, Depends(_build_report_filters)],
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> Response:
    try:
        content = export_sla_report_csv(
            session,
            filters,
            current_user,
            max_rows=get_settings().report_export_max_rows,
        )
        session.commit()
        return _csv_response("sla.csv", content)
    except ServiceError as error:
        session.rollback()
        _raise_service_error(error)


@router.get("/units/export.csv")
def export_unit_report_endpoint(
    filters: Annotated[ReportFilters, Depends(_build_report_filters)],
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> Response:
    try:
        content = export_unit_report_csv(
            session,
            filters,
            current_user,
            max_rows=get_settings().report_export_max_rows,
        )
        session.commit()
        return _csv_response("unidades.csv", content)
    except ServiceError as error:
        session.rollback()
        _raise_service_error(error)


@router.get("/suppliers/export.csv")
def export_supplier_report_endpoint(
    filters: Annotated[ReportFilters, Depends(_build_report_filters)],
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> Response:
    try:
        content = export_supplier_report_csv(
            session,
            filters,
            current_user,
            max_rows=get_settings().report_export_max_rows,
        )
        session.commit()
        return _csv_response("fornecedores.csv", content)
    except ServiceError as error:
        session.rollback()
        _raise_service_error(error)
