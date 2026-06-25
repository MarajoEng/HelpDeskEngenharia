from __future__ import annotations

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, require_roles
from app.core.database import get_db_session
from app.models.enums import UserRole
from app.models.user import User
from app.schemas import UnitCreate, UnitListParams, UnitListResponse, UnitResponse, UnitUpdate
from app.services.audit_service import log_action
from app.services.exceptions import ServiceError
from app.services.unit_service import create_unit_record, get_unit_or_404, list_unit_records, update_unit_record


router = APIRouter(prefix="/units", tags=["units"])


def _raise_service_error(error: ServiceError) -> None:
    raise HTTPException(status_code=error.status_code, detail=error.detail)


def _build_list_params(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: str | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    state: str | None = Query(default=None, min_length=2, max_length=2),
    region: str | None = Query(default=None),
    sort: Literal["name_asc", "created_at_desc"] = Query(default="name_asc"),
) -> UnitListParams:
    return UnitListParams(
        page=page,
        page_size=page_size,
        search=search,
        is_active=is_active,
        state=state,
        region=region,
        sort=sort,
    )


@router.get("", response_model=UnitListResponse)
def read_units(
    params: Annotated[UnitListParams, Depends(_build_list_params)],
    _: User = Depends(require_roles(UserRole.ADMIN, UserRole.ENGINEERING, UserRole.DIRECTOR)),
    session: Session = Depends(get_db_session),
) -> UnitListResponse:
    return list_unit_records(session, params)


@router.post("", response_model=UnitResponse, status_code=status.HTTP_201_CREATED)
def create_unit(
    payload: UnitCreate,
    request: Request,
    actor: User = Depends(require_roles(UserRole.ADMIN)),
    session: Session = Depends(get_db_session),
) -> UnitResponse:
    try:
        unit = create_unit_record(session, payload)
    except ServiceError as error:
        _raise_service_error(error)

    log_action(session, actor_user=actor, action="unit_created", entity_type="unit", entity_id=unit.id, request=request, metadata={"code": unit.code, "name": unit.name})
    session.commit()
    return UnitResponse.model_validate(unit)


@router.get("/{unit_id}", response_model=UnitResponse)
def read_unit(
    unit_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> UnitResponse:
    try:
        unit = get_unit_or_404(session, unit_id)
    except ServiceError as error:
        _raise_service_error(error)

    if current_user.role not in {UserRole.ADMIN, UserRole.ENGINEERING, UserRole.DIRECTOR, UserRole.MANAGER}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions.")

    if current_user.role == UserRole.MANAGER and current_user.unit_id != unit.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions.")

    return UnitResponse.model_validate(unit)


@router.patch("/{unit_id}", response_model=UnitResponse)
def patch_unit(
    unit_id: int,
    payload: UnitUpdate,
    request: Request,
    actor: User = Depends(require_roles(UserRole.ADMIN)),
    session: Session = Depends(get_db_session),
) -> UnitResponse:
    try:
        unit = update_unit_record(session, unit_id, payload)
    except ServiceError as error:
        _raise_service_error(error)

    log_action(session, actor_user=actor, action="unit_updated", entity_type="unit", entity_id=unit.id, request=request, metadata={"code": unit.code})
    session.commit()
    return UnitResponse.model_validate(unit)
