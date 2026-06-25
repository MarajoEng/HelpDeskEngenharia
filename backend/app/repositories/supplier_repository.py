from __future__ import annotations

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session

from app.models.supplier import Supplier


def _apply_supplier_filters(
    statement: Select,
    *,
    search: str | None = None,
    is_active: bool | None = None,
) -> Select:
    if is_active is not None:
        statement = statement.where(Supplier.is_active.is_(is_active))
    if search:
        pattern = f"%{search.strip()}%"
        statement = statement.where(
            or_(
                Supplier.name.ilike(pattern),
                Supplier.document.ilike(pattern),
                Supplier.specialty.ilike(pattern),
            )
        )
    return statement


def create_supplier(session: Session, **payload: object) -> Supplier:
    supplier = Supplier(**payload)
    session.add(supplier)
    session.flush()
    return supplier


def get_supplier_by_id(session: Session, supplier_id: int) -> Supplier | None:
    statement = select(Supplier).where(Supplier.id == supplier_id).limit(1)
    return session.scalar(statement)


def list_suppliers(
    session: Session,
    *,
    page: int,
    page_size: int,
    search: str | None = None,
    is_active: bool | None = None,
    sort: str = "name_asc",
) -> list[Supplier]:
    statement = select(Supplier)
    statement = _apply_supplier_filters(statement, search=search, is_active=is_active)
    if sort == "created_at_desc":
        statement = statement.order_by(Supplier.created_at.desc(), Supplier.id.desc())
    else:
        statement = statement.order_by(Supplier.name.asc(), Supplier.id.asc())
    statement = statement.offset((page - 1) * page_size).limit(page_size)
    return list(session.scalars(statement).all())


def count_suppliers(
    session: Session,
    *,
    search: str | None = None,
    is_active: bool | None = None,
) -> int:
    statement = select(func.count()).select_from(Supplier)
    statement = _apply_supplier_filters(statement, search=search, is_active=is_active)
    return int(session.scalar(statement) or 0)


def update_supplier(session: Session, supplier: Supplier, **changes: object) -> Supplier:
    for field, value in changes.items():
        setattr(supplier, field, value)
    session.add(supplier)
    session.flush()
    return supplier
