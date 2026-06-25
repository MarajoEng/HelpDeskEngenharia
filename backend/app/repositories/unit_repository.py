from __future__ import annotations

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session

from app.models.unit import Unit


def _apply_unit_filters(
    statement: Select[tuple[Unit]] | Select[tuple[int]],
    *,
    search: str | None = None,
    is_active: bool | None = None,
    state: str | None = None,
    region: str | None = None,
) -> Select[tuple[Unit]] | Select[tuple[int]]:
    if search:
        pattern = f"%{search.strip()}%"
        statement = statement.where(
            or_(
                Unit.code.ilike(pattern),
                Unit.name.ilike(pattern),
                Unit.city.ilike(pattern),
                Unit.region.ilike(pattern),
            )
        )

    if is_active is not None:
        statement = statement.where(Unit.is_active.is_(is_active))

    if state:
        statement = statement.where(Unit.state == state.strip().upper())

    if region:
        statement = statement.where(Unit.region.ilike(f"%{region.strip()}%"))

    return statement


def create_unit(
    session: Session,
    *,
    code: str,
    name: str,
    city: str,
    state: str,
    region: str,
    is_active: bool,
) -> Unit:
    unit = Unit(
        code=code,
        name=name,
        city=city,
        state=state,
        region=region,
        is_active=is_active,
    )
    session.add(unit)
    session.commit()
    session.refresh(unit)
    return unit


def get_unit_by_id(session: Session, unit_id: int) -> Unit | None:
    statement = select(Unit).where(Unit.id == unit_id).limit(1)
    return session.scalar(statement)


def get_unit_by_code(session: Session, code: str) -> Unit | None:
    statement = select(Unit).where(Unit.code == code).limit(1)
    return session.scalar(statement)


def list_units(
    session: Session,
    *,
    page: int,
    page_size: int,
    search: str | None = None,
    is_active: bool | None = None,
    state: str | None = None,
    region: str | None = None,
    sort: str = "name_asc",
) -> list[Unit]:
    statement = select(Unit)
    statement = _apply_unit_filters(
        statement,
        search=search,
        is_active=is_active,
        state=state,
        region=region,
    )

    if sort == "created_at_desc":
        statement = statement.order_by(Unit.created_at.desc(), Unit.id.desc())
    else:
        statement = statement.order_by(Unit.name.asc(), Unit.id.asc())

    statement = statement.offset((page - 1) * page_size).limit(page_size)
    return list(session.scalars(statement).all())


def count_units(
    session: Session,
    *,
    search: str | None = None,
    is_active: bool | None = None,
    state: str | None = None,
    region: str | None = None,
) -> int:
    statement = select(func.count()).select_from(Unit)
    statement = _apply_unit_filters(
        statement,
        search=search,
        is_active=is_active,
        state=state,
        region=region,
    )
    return int(session.scalar(statement) or 0)


def update_unit(session: Session, unit: Unit, **changes: object) -> Unit:
    for field, value in changes.items():
        setattr(unit, field, value)

    session.add(unit)
    session.commit()
    session.refresh(unit)
    return unit
