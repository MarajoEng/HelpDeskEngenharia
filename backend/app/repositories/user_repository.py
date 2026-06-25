from __future__ import annotations

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.user import User


def _apply_user_filters(
    statement: Select[tuple[User]] | Select[tuple[int]],
    *,
    search: str | None = None,
    role: str | None = None,
    roles: list[str] | tuple[str, ...] | None = None,
    unit_id: int | None = None,
    is_active: bool | None = None,
) -> Select[tuple[User]] | Select[tuple[int]]:
    if search:
        pattern = f"%{search.strip()}%"
        statement = statement.where(
            or_(
                User.name.ilike(pattern),
                User.email.ilike(pattern),
            )
        )

    if role is not None:
        statement = statement.where(User.role == role)
    elif roles:
        statement = statement.where(User.role.in_(roles))

    if unit_id is not None:
        statement = statement.where(User.unit_id == unit_id)

    if is_active is not None:
        statement = statement.where(User.is_active.is_(is_active))

    return statement


def create_user(
    session: Session,
    *,
    name: str,
    email: str,
    password_hash: str,
    role: str,
    unit_id: int | None,
    is_active: bool,
) -> User:
    user = User(
        name=name,
        email=email,
        password_hash=password_hash,
        role=role,
        unit_id=unit_id,
        is_active=is_active,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def get_user_by_email(session: Session, email: str) -> User | None:
    normalized_email = email.strip().lower()
    statement = (
        select(User)
        .options(selectinload(User.unit))
        .where(func.lower(User.email) == normalized_email)
        .limit(1)
    )
    return session.scalar(statement)


def get_user_by_id(session: Session, user_id: int) -> User | None:
    statement = select(User).options(selectinload(User.unit)).where(User.id == user_id).limit(1)
    return session.scalar(statement)


def list_users(
    session: Session,
    *,
    page: int,
    page_size: int,
    search: str | None = None,
    role: str | None = None,
    roles: list[str] | tuple[str, ...] | None = None,
    unit_id: int | None = None,
    is_active: bool | None = None,
    sort: str = "name_asc",
) -> list[User]:
    statement = select(User).options(selectinload(User.unit))
    statement = _apply_user_filters(
        statement,
        search=search,
        role=role,
        roles=roles,
        unit_id=unit_id,
        is_active=is_active,
    )

    if sort == "created_at_desc":
        statement = statement.order_by(User.created_at.desc(), User.id.desc())
    else:
        statement = statement.order_by(User.name.asc(), User.id.asc())

    statement = statement.offset((page - 1) * page_size).limit(page_size)
    return list(session.scalars(statement).all())


def count_users(
    session: Session,
    *,
    search: str | None = None,
    role: str | None = None,
    roles: list[str] | tuple[str, ...] | None = None,
    unit_id: int | None = None,
    is_active: bool | None = None,
) -> int:
    statement = select(func.count()).select_from(User)
    statement = _apply_user_filters(
        statement,
        search=search,
        role=role,
        roles=roles,
        unit_id=unit_id,
        is_active=is_active,
    )
    return int(session.scalar(statement) or 0)


def update_user(session: Session, user: User, **changes: object) -> User:
    for field, value in changes.items():
        setattr(user, field, value)

    session.add(user)
    session.commit()
    session.refresh(user)
    return user
