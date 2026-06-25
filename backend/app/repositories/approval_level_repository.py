from __future__ import annotations

from decimal import Decimal

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session

from app.models.approval_level import ApprovalLevel


def _apply_approval_level_filters(
    statement: Select[tuple[ApprovalLevel]] | Select[tuple[int]],
    *,
    search: str | None = None,
    is_active: bool | None = None,
) -> Select[tuple[ApprovalLevel]] | Select[tuple[int]]:
    if search:
        pattern = f"%{search.strip()}%"
        statement = statement.where(ApprovalLevel.name.ilike(pattern))

    if is_active is not None:
        statement = statement.where(ApprovalLevel.is_active.is_(is_active))

    return statement


def create_approval_level(session: Session, **payload: object) -> ApprovalLevel:
    approval_level = ApprovalLevel(**payload)
    session.add(approval_level)
    session.flush()
    return approval_level


def get_approval_level_by_id(session: Session, approval_level_id: int) -> ApprovalLevel | None:
    statement = select(ApprovalLevel).where(ApprovalLevel.id == approval_level_id).limit(1)
    return session.scalar(statement)


def list_approval_levels(
    session: Session,
    *,
    page: int,
    page_size: int,
    search: str | None = None,
    is_active: bool | None = None,
    sort: str = "name_asc",
) -> list[ApprovalLevel]:
    statement = select(ApprovalLevel)
    statement = _apply_approval_level_filters(statement, search=search, is_active=is_active)

    if sort == "created_at_desc":
        statement = statement.order_by(ApprovalLevel.created_at.desc(), ApprovalLevel.id.desc())
    else:
        statement = statement.order_by(ApprovalLevel.name.asc(), ApprovalLevel.id.asc())

    statement = statement.offset((page - 1) * page_size).limit(page_size)
    return list(session.scalars(statement).all())


def count_approval_levels(
    session: Session,
    *,
    search: str | None = None,
    is_active: bool | None = None,
) -> int:
    statement = select(func.count()).select_from(ApprovalLevel)
    statement = _apply_approval_level_filters(statement, search=search, is_active=is_active)
    return int(session.scalar(statement) or 0)


def update_approval_level(session: Session, approval_level: ApprovalLevel, **changes: object) -> ApprovalLevel:
    for field, value in changes.items():
        setattr(approval_level, field, value)

    session.add(approval_level)
    session.flush()
    return approval_level


def find_overlapping_active_approval_level(
    session: Session,
    *,
    min_amount: Decimal,
    max_amount: Decimal | None,
    exclude_id: int | None = None,
) -> ApprovalLevel | None:
    statement = select(ApprovalLevel).where(ApprovalLevel.is_active.is_(True))

    if exclude_id is not None:
        statement = statement.where(ApprovalLevel.id != exclude_id)

    if max_amount is None:
        statement = statement.where(
            or_(
                ApprovalLevel.max_amount.is_(None),
                ApprovalLevel.max_amount >= min_amount,
            )
        )
    else:
        statement = statement.where(ApprovalLevel.min_amount <= max_amount)
        statement = statement.where(
            or_(
                ApprovalLevel.max_amount.is_(None),
                ApprovalLevel.max_amount >= min_amount,
            )
        )

    statement = statement.order_by(ApprovalLevel.min_amount.asc(), ApprovalLevel.id.asc()).limit(1)
    return session.scalar(statement)


def get_active_approval_level_for_amount(session: Session, amount: Decimal) -> ApprovalLevel | None:
    statement = (
        select(ApprovalLevel)
        .where(
            ApprovalLevel.is_active.is_(True),
            ApprovalLevel.min_amount <= amount,
            or_(ApprovalLevel.max_amount.is_(None), ApprovalLevel.max_amount >= amount),
        )
        .order_by(ApprovalLevel.min_amount.desc(), ApprovalLevel.id.desc())
        .limit(1)
    )
    return session.scalar(statement)
