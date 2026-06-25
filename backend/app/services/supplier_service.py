from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.enums import UserRole
from app.models.user import User
from app.repositories.supplier_repository import (
    count_suppliers,
    create_supplier,
    get_supplier_by_id,
    list_suppliers,
    update_supplier,
)
from app.schemas.pagination import calculate_pages
from app.schemas.supplier import SupplierCreate, SupplierListParams, SupplierListResponse, SupplierResponse, SupplierUpdate
from app.services.exceptions import NotFoundServiceError, ValidationServiceError

_VIEW_ROLES = {UserRole.ADMIN, UserRole.ENGINEERING, UserRole.DIRECTOR}
_MANAGE_ROLES = {UserRole.ADMIN}


class SupplierNotFoundError(NotFoundServiceError):
    detail = "Supplier not found."


class SupplierPermissionError(ValidationServiceError):
    status_code = 403
    detail = "Insufficient permissions."


def _to_supplier_response(supplier) -> SupplierResponse:
    return SupplierResponse.model_validate(supplier)


def list_supplier_records(session: Session, params: SupplierListParams, current_user: User) -> SupplierListResponse:
    if current_user.role not in _VIEW_ROLES:
        raise SupplierPermissionError

    total = count_suppliers(session, search=params.search, is_active=params.is_active)
    items = list_suppliers(
        session,
        page=params.page,
        page_size=params.page_size,
        search=params.search,
        is_active=params.is_active,
        sort=params.sort,
    )
    return SupplierListResponse(
        items=[_to_supplier_response(s) for s in items],
        total=total,
        page=params.page,
        page_size=params.page_size,
        pages=calculate_pages(total, params.page_size),
    )


def create_supplier_record(session: Session, payload: SupplierCreate, current_user: User) -> SupplierResponse:
    if current_user.role not in _MANAGE_ROLES:
        raise SupplierPermissionError

    supplier = create_supplier(
        session,
        name=payload.name,
        document=payload.document,
        phone=payload.phone,
        email=payload.email,
        specialty=payload.specialty,
        is_active=payload.is_active,
    )
    session.commit()
    persisted = get_supplier_by_id(session, supplier.id)
    if persisted is None:
        raise SupplierNotFoundError
    return _to_supplier_response(persisted)


def update_supplier_record(
    session: Session,
    supplier_id: int,
    payload: SupplierUpdate,
    current_user: User,
) -> SupplierResponse:
    if current_user.role not in _MANAGE_ROLES:
        raise SupplierPermissionError

    supplier = get_supplier_by_id(session, supplier_id)
    if supplier is None:
        raise SupplierNotFoundError

    changes = payload.model_dump(exclude_unset=True)
    if changes:
        update_supplier(session, supplier, **changes)

    session.commit()
    persisted = get_supplier_by_id(session, supplier_id)
    if persisted is None:
        raise SupplierNotFoundError
    return _to_supplier_response(persisted)
