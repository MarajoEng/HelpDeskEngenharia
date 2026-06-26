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
    group_code: str | None = None,
    branch_code: str | None = None,
) -> Select[tuple[Unit]] | Select[tuple[int]]:
    if search:
        pattern = f"%{search.strip()}%"
        statement = statement.where(
            or_(
                Unit.code.ilike(pattern),
                Unit.group_code.ilike(pattern),
                Unit.branch_code.ilike(pattern),
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

    if group_code:
        statement = statement.where(Unit.group_code == group_code.strip())

    if branch_code:
        statement = statement.where(Unit.branch_code == branch_code.strip())

    return statement


def create_unit(
    session: Session,
    *,
    code: str,
    group_code: str | None = None,
    branch_code: str | None = None,
    name: str,
    city: str,
    state: str,
    region: str,
    is_active: bool,
) -> Unit:
    unit = Unit(
        code=code,
        group_code=group_code,
        branch_code=branch_code,
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
    group_code: str | None = None,
    branch_code: str | None = None,
    sort: str = "name_asc",
) -> list[Unit]:
    statement = select(Unit)
    statement = _apply_unit_filters(
        statement,
        search=search,
        is_active=is_active,
        state=state,
        region=region,
        group_code=group_code,
        branch_code=branch_code,
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
    group_code: str | None = None,
    branch_code: str | None = None,
) -> int:
    statement = select(func.count()).select_from(Unit)
    statement = _apply_unit_filters(
        statement,
        search=search,
        is_active=is_active,
        state=state,
        region=region,
        group_code=group_code,
        branch_code=branch_code,
    )
    return int(session.scalar(statement) or 0)


def list_unit_groups(session: Session) -> list[dict[str, object]]:
    statement = (
        select(
            Unit.group_code.label("group_code"),
            func.count(Unit.id).label("total_units"),
        )
        .where(Unit.group_code.is_not(None))
        .group_by(Unit.group_code)
        .order_by(Unit.group_code.asc())
    )
    return [{"group_code": row.group_code, "total_units": row.total_units} for row in session.execute(statement).all()]


def update_unit(session: Session, unit: Unit, **changes: object) -> Unit:
    for field, value in changes.items():
        setattr(unit, field, value)

    session.add(unit)
    session.commit()
    session.refresh(unit)
    return unit
