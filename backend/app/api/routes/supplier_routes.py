from __future__ import annotations

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.database import get_db_session
from app.models.user import User
from app.schemas.supplier import SupplierCreate, SupplierListParams, SupplierListResponse, SupplierResponse, SupplierUpdate
from app.services.exceptions import ServiceError
from app.services.supplier_service import create_supplier_record, list_supplier_records, update_supplier_record

router = APIRouter(prefix="/suppliers", tags=["suppliers"])


def _raise_service_error(error: ServiceError) -> None:
    raise HTTPException(status_code=error.status_code, detail=error.detail)


def _build_list_params(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: str | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    sort: Literal["name_asc", "created_at_desc"] = Query(default="name_asc"),
) -> SupplierListParams:
    return SupplierListParams(
        page=page,
        page_size=page_size,
        search=search,
        is_active=is_active,
        sort=sort,
    )


@router.get("", response_model=SupplierListResponse)
def read_suppliers(
    params: Annotated[SupplierListParams, Depends(_build_list_params)],
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> SupplierListResponse:
    try:
        return list_supplier_records(session, params, current_user)
    except ServiceError as error:
        _raise_service_error(error)


@router.post("", response_model=SupplierResponse, status_code=status.HTTP_201_CREATED)
def create_supplier(
    payload: SupplierCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> SupplierResponse:
    try:
        return create_supplier_record(session, payload, current_user)
    except ServiceError as error:
        _raise_service_error(error)


@router.patch("/{supplier_id}", response_model=SupplierResponse)
def patch_supplier(
    supplier_id: int,
    payload: SupplierUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> SupplierResponse:
    try:
        return update_supplier_record(session, supplier_id, payload, current_user)
    except ServiceError as error:
        _raise_service_error(error)
