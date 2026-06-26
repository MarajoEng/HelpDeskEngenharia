from __future__ import annotations

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.database import get_db_session
from app.models.enums import TicketCategory, TicketStatus
from app.models.user import User
from app.schemas.dashboard import DashboardOverviewParams, DashboardOverviewResponse
from app.services.dashboard_service import get_dashboard_overview
from app.services.exceptions import ServiceError

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def _raise_service_error(error: ServiceError) -> None:
    raise HTTPException(status_code=error.status_code, detail=error.detail)


def _build_dashboard_params(
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    unit_id: int | None = Query(default=None, ge=1),
    group_code: str | None = Query(default=None),
    region: str | None = Query(default=None),
    status_filter: TicketStatus | None = Query(default=None, alias="status"),
    category: TicketCategory | None = Query(default=None),
    category_id: int | None = Query(default=None, ge=1),
    priority_id: int | None = Query(default=None, ge=1),
) -> DashboardOverviewParams:
    return DashboardOverviewParams(
        date_from=date_from,
        date_to=date_to,
        unit_id=unit_id,
        group_code=group_code,
        region=region,
        status=status_filter,
        category=category,
        category_id=category_id,
        priority_id=priority_id,
    )


@router.get("/overview", response_model=DashboardOverviewResponse)
def read_dashboard_overview(
    params: Annotated[DashboardOverviewParams, Depends(_build_dashboard_params)],
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> DashboardOverviewResponse:
    try:
        return get_dashboard_overview(session, params, current_user)
    except ServiceError as error:
        _raise_service_error(error)
