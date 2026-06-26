from __future__ import annotations

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.ticket_category import TicketCategoryConfig
from app.models.ticket_category_type import TicketCategoryTypeLink
from app.models.ticket_custom_field import TicketCustomField
from app.models.ticket_priority import TicketPriorityConfig
from app.models.ticket_subcategory import TicketSubcategoryConfig
from app.models.ticket_type import TicketTypeConfig


def _apply_named_filters(
    statement: Select,
    *,
    model,
    search: str | None = None,
    is_active: bool | None = None,
) -> Select:
    if search:
        pattern = f"%{search.strip()}%"
        statement = statement.where(
            or_(
                model.name.ilike(pattern),
                model.description.ilike(pattern),
            )
        )

    if is_active is not None:
        statement = statement.where(model.is_active.is_(is_active))

    return statement


def _apply_sort(statement: Select, *, model, sort: str) -> Select:
    if sort == "created_at_desc":
        return statement.order_by(model.created_at.desc(), model.id.desc())
    if sort == "name_asc":
        return statement.order_by(model.name.asc(), model.id.asc())
    return statement.order_by(model.display_order.asc(), model.name.asc(), model.id.asc())


def create_ticket_category(session: Session, **payload: object) -> TicketCategoryConfig:
    category = TicketCategoryConfig(**payload)
    session.add(category)
    session.flush()
    return category


def get_ticket_category_by_id(session: Session, category_id: int) -> TicketCategoryConfig | None:
    statement = (
        select(TicketCategoryConfig)
        .options(
            selectinload(TicketCategoryConfig.category_types).selectinload(TicketCategoryTypeLink.ticket_type)
        )
        .where(TicketCategoryConfig.id == category_id)
        .limit(1)
    )
    return session.scalar(statement)


def get_ticket_category_by_name(session: Session, name: str) -> TicketCategoryConfig | None:
    statement = (
        select(TicketCategoryConfig)
        .where(func.lower(TicketCategoryConfig.name) == name.strip().lower())
        .limit(1)
    )
    return session.scalar(statement)


def list_ticket_categories_by_ids(session: Session, category_ids: list[int]) -> list[TicketCategoryConfig]:
    if not category_ids:
        return []
    statement = select(TicketCategoryConfig).where(TicketCategoryConfig.id.in_(category_ids))
    return list(session.scalars(statement).all())


def list_ticket_categories(
    session: Session,
    *,
    page: int,
    page_size: int,
    search: str | None = None,
    is_active: bool | None = None,
    sort: str = "display_order_asc",
) -> list[TicketCategoryConfig]:
    statement = select(TicketCategoryConfig).options(
        selectinload(TicketCategoryConfig.category_types).selectinload(TicketCategoryTypeLink.ticket_type)
    )
    statement = _apply_named_filters(statement, model=TicketCategoryConfig, search=search, is_active=is_active)
    statement = _apply_sort(statement, model=TicketCategoryConfig, sort=sort)
    statement = statement.offset((page - 1) * page_size).limit(page_size)
    return list(session.scalars(statement).all())


def count_ticket_categories(
    session: Session,
    *,
    search: str | None = None,
    is_active: bool | None = None,
) -> int:
    statement = select(func.count()).select_from(TicketCategoryConfig)
    statement = _apply_named_filters(statement, model=TicketCategoryConfig, search=search, is_active=is_active)
    return int(session.scalar(statement) or 0)


def update_ticket_category(session: Session, category: TicketCategoryConfig, **changes: object) -> TicketCategoryConfig:
    for field, value in changes.items():
        setattr(category, field, value)
    session.add(category)
    session.flush()
    return category


def replace_ticket_category_types(session: Session, category: TicketCategoryConfig, type_ids: list[int]) -> TicketCategoryConfig:
    current_by_type_id = {link.type_id: link for link in category.category_types}
    category.category_types = [
        current_by_type_id[type_id] if type_id in current_by_type_id else TicketCategoryTypeLink(type_id=type_id)
        for type_id in type_ids
    ]
    session.add(category)
    session.flush()
    return category


def create_ticket_subcategory(session: Session, **payload: object) -> TicketSubcategoryConfig:
    subcategory = TicketSubcategoryConfig(**payload)
    session.add(subcategory)
    session.flush()
    return subcategory


def get_ticket_subcategory_by_id(session: Session, subcategory_id: int) -> TicketSubcategoryConfig | None:
    statement = (
        select(TicketSubcategoryConfig)
        .options(selectinload(TicketSubcategoryConfig.category))
        .where(TicketSubcategoryConfig.id == subcategory_id)
        .limit(1)
    )
    return session.scalar(statement)


def get_ticket_subcategory_by_name(
    session: Session,
    *,
    category_id: int,
    name: str,
) -> TicketSubcategoryConfig | None:
    statement = (
        select(TicketSubcategoryConfig)
        .where(
            TicketSubcategoryConfig.category_id == category_id,
            func.lower(TicketSubcategoryConfig.name) == name.strip().lower(),
        )
        .limit(1)
    )
    return session.scalar(statement)


def list_ticket_subcategories(
    session: Session,
    *,
    page: int,
    page_size: int,
    category_id: int | None = None,
    search: str | None = None,
    is_active: bool | None = None,
    sort: str = "display_order_asc",
) -> list[TicketSubcategoryConfig]:
    statement = select(TicketSubcategoryConfig).options(selectinload(TicketSubcategoryConfig.category))
    statement = _apply_named_filters(statement, model=TicketSubcategoryConfig, search=search, is_active=is_active)
    if category_id is not None:
        statement = statement.where(TicketSubcategoryConfig.category_id == category_id)
    statement = _apply_sort(statement, model=TicketSubcategoryConfig, sort=sort)
    statement = statement.offset((page - 1) * page_size).limit(page_size)
    return list(session.scalars(statement).all())


def count_ticket_subcategories(
    session: Session,
    *,
    category_id: int | None = None,
    search: str | None = None,
    is_active: bool | None = None,
) -> int:
    statement = select(func.count()).select_from(TicketSubcategoryConfig)
    statement = _apply_named_filters(statement, model=TicketSubcategoryConfig, search=search, is_active=is_active)
    if category_id is not None:
        statement = statement.where(TicketSubcategoryConfig.category_id == category_id)
    return int(session.scalar(statement) or 0)


def update_ticket_subcategory(
    session: Session,
    subcategory: TicketSubcategoryConfig,
    **changes: object,
) -> TicketSubcategoryConfig:
    for field, value in changes.items():
        setattr(subcategory, field, value)
    session.add(subcategory)
    session.flush()
    return subcategory


def create_ticket_type(session: Session, **payload: object) -> TicketTypeConfig:
    ticket_type = TicketTypeConfig(**payload)
    session.add(ticket_type)
    session.flush()
    return ticket_type


def get_ticket_type_by_id(session: Session, type_id: int) -> TicketTypeConfig | None:
    statement = select(TicketTypeConfig).where(TicketTypeConfig.id == type_id).limit(1)
    return session.scalar(statement)


def get_ticket_type_by_name(session: Session, name: str) -> TicketTypeConfig | None:
    statement = (
        select(TicketTypeConfig)
        .where(func.lower(TicketTypeConfig.name) == name.strip().lower())
        .limit(1)
    )
    return session.scalar(statement)


def list_ticket_types_by_ids(session: Session, type_ids: list[int]) -> list[TicketTypeConfig]:
    if not type_ids:
        return []
    statement = select(TicketTypeConfig).where(TicketTypeConfig.id.in_(type_ids))
    return list(session.scalars(statement).all())


def list_ticket_types(
    session: Session,
    *,
    page: int,
    page_size: int,
    search: str | None = None,
    is_active: bool | None = None,
    sort: str = "display_order_asc",
) -> list[TicketTypeConfig]:
    statement = select(TicketTypeConfig)
    statement = _apply_named_filters(statement, model=TicketTypeConfig, search=search, is_active=is_active)
    statement = _apply_sort(statement, model=TicketTypeConfig, sort=sort)
    statement = statement.offset((page - 1) * page_size).limit(page_size)
    return list(session.scalars(statement).all())


def count_ticket_types(
    session: Session,
    *,
    search: str | None = None,
    is_active: bool | None = None,
) -> int:
    statement = select(func.count()).select_from(TicketTypeConfig)
    statement = _apply_named_filters(statement, model=TicketTypeConfig, search=search, is_active=is_active)
    return int(session.scalar(statement) or 0)


def update_ticket_type(session: Session, ticket_type: TicketTypeConfig, **changes: object) -> TicketTypeConfig:
    for field, value in changes.items():
        setattr(ticket_type, field, value)
    session.add(ticket_type)
    session.flush()
    return ticket_type


def create_ticket_priority(session: Session, **payload: object) -> TicketPriorityConfig:
    priority = TicketPriorityConfig(**payload)
    session.add(priority)
    session.flush()
    return priority


def get_ticket_priority_by_id(session: Session, priority_id: int) -> TicketPriorityConfig | None:
    statement = select(TicketPriorityConfig).where(TicketPriorityConfig.id == priority_id).limit(1)
    return session.scalar(statement)


def get_ticket_priority_by_name(session: Session, name: str) -> TicketPriorityConfig | None:
    statement = (
        select(TicketPriorityConfig)
        .where(func.lower(TicketPriorityConfig.name) == name.strip().lower())
        .limit(1)
    )
    return session.scalar(statement)


def list_ticket_priorities(
    session: Session,
    *,
    page: int,
    page_size: int,
    search: str | None = None,
    is_active: bool | None = None,
    sort: str = "display_order_asc",
) -> list[TicketPriorityConfig]:
    statement = select(TicketPriorityConfig)
    statement = _apply_named_filters(statement, model=TicketPriorityConfig, search=search, is_active=is_active)
    statement = _apply_sort(statement, model=TicketPriorityConfig, sort=sort)
    statement = statement.offset((page - 1) * page_size).limit(page_size)
    return list(session.scalars(statement).all())


def count_ticket_priorities(
    session: Session,
    *,
    search: str | None = None,
    is_active: bool | None = None,
) -> int:
    statement = select(func.count()).select_from(TicketPriorityConfig)
    statement = _apply_named_filters(statement, model=TicketPriorityConfig, search=search, is_active=is_active)
    return int(session.scalar(statement) or 0)


def update_ticket_priority(
    session: Session,
    priority: TicketPriorityConfig,
    **changes: object,
) -> TicketPriorityConfig:
    for field, value in changes.items():
        setattr(priority, field, value)
    session.add(priority)
    session.flush()
    return priority


def create_ticket_custom_field(session: Session, **payload: object) -> TicketCustomField:
    field = TicketCustomField(**payload)
    session.add(field)
    session.flush()
    return field


def get_ticket_custom_field_by_id(session: Session, custom_field_id: int) -> TicketCustomField | None:
    statement = (
        select(TicketCustomField)
        .options(
            selectinload(TicketCustomField.category),
            selectinload(TicketCustomField.subcategory),
        )
        .where(TicketCustomField.id == custom_field_id)
        .limit(1)
    )
    return session.scalar(statement)


def get_ticket_custom_field_by_name(
    session: Session,
    *,
    category_id: int,
    subcategory_id: int | None,
    name: str,
) -> TicketCustomField | None:
    statement = (
        select(TicketCustomField)
        .where(
            TicketCustomField.category_id == category_id,
            TicketCustomField.subcategory_id.is_(subcategory_id)
            if subcategory_id is None
            else TicketCustomField.subcategory_id == subcategory_id,
            func.lower(TicketCustomField.name) == name.strip().lower(),
        )
        .limit(1)
    )
    return session.scalar(statement)


def list_ticket_custom_fields(
    session: Session,
    *,
    page: int,
    page_size: int,
    category_id: int | None = None,
    subcategory_id: int | None = None,
    search: str | None = None,
    is_active: bool | None = None,
    sort: str = "display_order_asc",
) -> list[TicketCustomField]:
    statement = select(TicketCustomField).options(
        selectinload(TicketCustomField.category),
        selectinload(TicketCustomField.subcategory),
    )
    statement = _apply_named_filters(statement, model=TicketCustomField, search=search, is_active=is_active)
    if category_id is not None:
        statement = statement.where(TicketCustomField.category_id == category_id)
    if subcategory_id is not None:
        statement = statement.where(TicketCustomField.subcategory_id == subcategory_id)
    statement = _apply_sort(statement, model=TicketCustomField, sort=sort)
    statement = statement.offset((page - 1) * page_size).limit(page_size)
    return list(session.scalars(statement).all())


def count_ticket_custom_fields(
    session: Session,
    *,
    category_id: int | None = None,
    subcategory_id: int | None = None,
    search: str | None = None,
    is_active: bool | None = None,
) -> int:
    statement = select(func.count()).select_from(TicketCustomField)
    statement = _apply_named_filters(statement, model=TicketCustomField, search=search, is_active=is_active)
    if category_id is not None:
        statement = statement.where(TicketCustomField.category_id == category_id)
    if subcategory_id is not None:
        statement = statement.where(TicketCustomField.subcategory_id == subcategory_id)
    return int(session.scalar(statement) or 0)


def list_active_ticket_custom_fields_for_scope(
    session: Session,
    *,
    category_id: int,
    subcategory_id: int | None = None,
) -> list[TicketCustomField]:
    statement = (
        select(TicketCustomField)
        .options(
            selectinload(TicketCustomField.category),
            selectinload(TicketCustomField.subcategory),
        )
        .where(
            TicketCustomField.category_id == category_id,
            TicketCustomField.is_active.is_(True),
            or_(
                TicketCustomField.subcategory_id.is_(None),
                TicketCustomField.subcategory_id == subcategory_id,
            )
            if subcategory_id is not None
            else TicketCustomField.subcategory_id.is_(None),
        )
        .order_by(TicketCustomField.display_order.asc(), TicketCustomField.label.asc(), TicketCustomField.id.asc())
    )
    return list(session.scalars(statement).all())


def update_ticket_custom_field(
    session: Session,
    custom_field: TicketCustomField,
    **changes: object,
) -> TicketCustomField:
    for field, value in changes.items():
        setattr(custom_field, field, value)
    session.add(custom_field)
    session.flush()
    return custom_field
