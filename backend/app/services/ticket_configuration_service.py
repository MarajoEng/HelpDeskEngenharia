from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.enums import PriorityLevel, TicketCategory, UserRole
from app.models.user import User
from app.repositories.ticket_configuration_repository import (
    count_ticket_categories,
    count_ticket_custom_fields,
    count_ticket_priorities,
    count_ticket_status_transitions,
    count_ticket_statuses,
    count_ticket_subcategories,
    count_ticket_types,
    create_ticket_category,
    create_ticket_custom_field,
    create_ticket_priority,
    create_ticket_status,
    create_ticket_status_transition,
    create_ticket_subcategory,
    create_ticket_type,
    get_ticket_category_by_id,
    get_ticket_category_by_name,
    get_ticket_custom_field_by_id,
    get_ticket_custom_field_by_name,
    get_ticket_priority_by_id,
    get_ticket_priority_by_name,
    get_ticket_status_by_id,
    get_ticket_status_by_name,
    get_ticket_status_transition_by_id,
    get_ticket_status_transition,
    get_ticket_subcategory_by_id,
    get_ticket_subcategory_by_name,
    get_ticket_type_by_id,
    get_ticket_type_by_name,
    list_active_ticket_custom_fields_for_scope,
    list_ticket_categories,
    list_ticket_custom_fields,
    list_ticket_priorities,
    list_ticket_status_transitions,
    list_ticket_statuses,
    list_ticket_subcategories,
    list_ticket_types,
    list_ticket_types_by_ids,
    replace_ticket_category_types,
    update_ticket_category,
    update_ticket_custom_field,
    update_ticket_priority,
    update_ticket_status,
    update_ticket_status_transition,
    update_ticket_subcategory,
    update_ticket_type,
)
from app.schemas.pagination import calculate_pages
from app.schemas.ticket_configuration import (
    TicketCategoryCreate,
    TicketCategoryListResponse,
    TicketCategoryResponse,
    TicketCategoryUpdate,
    TicketCustomFieldCreate,
    TicketCustomFieldListParams,
    TicketCustomFieldListResponse,
    TicketCustomFieldOption,
    TicketCustomFieldResponse,
    TicketCustomFieldUpdate,
    TicketFormSchemaResponse,
    TicketConfigurationPageParams,
    TicketPriorityCreate,
    TicketPriorityListResponse,
    TicketPriorityResponse,
    TicketPriorityUpdate,
    TicketStatusCreate,
    TicketStatusListResponse,
    TicketStatusResponse,
    TicketStatusTransitionCreate,
    TicketStatusTransitionListParams,
    TicketStatusTransitionListResponse,
    TicketStatusTransitionResponse,
    TicketStatusTransitionUpdate,
    TicketStatusUpdate,
    TicketSubcategoryCreate,
    TicketSubcategoryListParams,
    TicketSubcategoryListResponse,
    TicketSubcategoryResponse,
    TicketSubcategoryUpdate,
    TicketTypeCreate,
    TicketTypeListResponse,
    TicketTypeResponse,
    TicketTypeUpdate,
)
from app.services.exceptions import ConflictServiceError, NotFoundServiceError, ValidationServiceError


class TicketConfigurationPermissionError(ValidationServiceError):
    status_code = 403
    detail = "Insufficient permissions."


class TicketCategoryNotFoundError(NotFoundServiceError):
    detail = "Ticket category not found."


class TicketSubcategoryNotFoundError(NotFoundServiceError):
    detail = "Ticket subcategory not found."


class TicketTypeNotFoundError(NotFoundServiceError):
    detail = "Ticket type not found."


class TicketPriorityNotFoundError(NotFoundServiceError):
    detail = "Ticket priority not found."


class TicketCustomFieldNotFoundError(NotFoundServiceError):
    detail = "Ticket custom field not found."


class TicketStatusNotFoundError(NotFoundServiceError):
    detail = "Ticket status not found."


class TicketStatusTransitionNotFoundError(NotFoundServiceError):
    detail = "Ticket status transition not found."


class DuplicateTicketCategoryError(ConflictServiceError):
    detail = "Ticket category name already exists."


class DuplicateTicketSubcategoryError(ConflictServiceError):
    detail = "Ticket subcategory name already exists for this category."


class DuplicateTicketTypeError(ConflictServiceError):
    detail = "Ticket type name already exists."


class DuplicateTicketPriorityError(ConflictServiceError):
    detail = "Ticket priority name already exists."


class DuplicateTicketCustomFieldError(ConflictServiceError):
    detail = "Ticket custom field name already exists for this scope."


class DuplicateTicketStatusError(ConflictServiceError):
    detail = "Ticket status name already exists."


class DuplicateTicketStatusTransitionError(ConflictServiceError):
    detail = "Ticket status transition already exists."


def _ensure_admin(current_user: User) -> None:
    if current_user.role != UserRole.ADMIN:
        raise TicketConfigurationPermissionError


def _build_category_response(category, *, only_active_type_ids: bool) -> TicketCategoryResponse:
    type_ids: list[int] = []
    for link in category.category_types:
        if link.ticket_type is None:
            continue
        if only_active_type_ids and not link.ticket_type.is_active:
            continue
        type_ids.append(link.type_id)

    return TicketCategoryResponse(
        id=category.id,
        name=category.name,
        legacy_value=category.legacy_value,
        description=category.description,
        is_active=category.is_active,
        display_order=category.display_order,
        requires_attachment=category.requires_attachment,
        requires_location=category.requires_location,
        type_ids=sorted(type_ids),
        created_at=category.created_at,
        updated_at=category.updated_at,
    )


def _build_subcategory_response(subcategory) -> TicketSubcategoryResponse:
    return TicketSubcategoryResponse(
        id=subcategory.id,
        category_id=subcategory.category_id,
        category_name=subcategory.category.name,
        name=subcategory.name,
        description=subcategory.description,
        is_active=subcategory.is_active,
        display_order=subcategory.display_order,
        created_at=subcategory.created_at,
        updated_at=subcategory.updated_at,
    )


def _build_type_response(ticket_type) -> TicketTypeResponse:
    return TicketTypeResponse(
        id=ticket_type.id,
        name=ticket_type.name,
        description=ticket_type.description,
        is_active=ticket_type.is_active,
        display_order=ticket_type.display_order,
        created_at=ticket_type.created_at,
        updated_at=ticket_type.updated_at,
    )


def _build_priority_response(priority) -> TicketPriorityResponse:
    return TicketPriorityResponse(
        id=priority.id,
        name=priority.name,
        legacy_value=priority.legacy_value,
        description=priority.description,
        color=priority.color,
        weight=priority.weight,
        sla_hours=priority.sla_hours,
        requires_reason=priority.requires_reason,
        is_active=priority.is_active,
        display_order=priority.display_order,
        created_at=priority.created_at,
        updated_at=priority.updated_at,
    )


def _build_status_response(status) -> TicketStatusResponse:
    return TicketStatusResponse(
        id=status.id,
        name=status.name,
        legacy_value=status.legacy_value,
        description=status.description,
        color=status.color,
        is_initial=status.is_initial,
        is_final=status.is_final,
        pauses_sla=status.pauses_sla,
        allows_reopen=status.allows_reopen,
        is_active=status.is_active,
        display_order=status.display_order,
        created_at=status.created_at,
        updated_at=status.updated_at,
    )


def _build_transition_response(transition) -> TicketStatusTransitionResponse:
    return TicketStatusTransitionResponse(
        id=transition.id,
        from_status_id=transition.from_status_id,
        from_status_name=transition.from_status.name if transition.from_status else "",
        to_status_id=transition.to_status_id,
        to_status_name=transition.to_status.name if transition.to_status else "",
        to_status_color=transition.to_status.color if transition.to_status else "#475569",
        requires_comment=transition.requires_comment,
        requires_attachment=transition.requires_attachment,
        allowed_roles_json=transition.allowed_roles_json,
        is_active=transition.is_active,
        created_at=transition.created_at,
        updated_at=transition.updated_at,
    )


def _sorted_options(options: list[dict] | None) -> list[TicketCustomFieldOption]:
    parsed = [TicketCustomFieldOption.model_validate(option) for option in (options or [])]
    return sorted(parsed, key=lambda option: (option.display_order, option.label.lower(), option.value))


def _build_custom_field_response(field) -> TicketCustomFieldResponse:
    return TicketCustomFieldResponse(
        id=field.id,
        category_id=field.category_id,
        category_name=field.category.name if field.category else "",
        subcategory_id=field.subcategory_id,
        subcategory_name=field.subcategory.name if field.subcategory else None,
        name=field.name,
        label=field.label,
        description=field.description,
        field_type=field.field_type,
        is_required=field.is_required,
        is_active=field.is_active,
        display_order=field.display_order,
        placeholder=field.placeholder,
        help_text=field.help_text,
        validation_json=field.validation_json,
        options=_sorted_options(field.options_json),
        created_at=field.created_at,
        updated_at=field.updated_at,
    )


def _get_ticket_category_or_404(session: Session, category_id: int):
    category = get_ticket_category_by_id(session, category_id)
    if category is None:
        raise TicketCategoryNotFoundError
    return category


def _get_ticket_subcategory_or_404(session: Session, subcategory_id: int):
    subcategory = get_ticket_subcategory_by_id(session, subcategory_id)
    if subcategory is None:
        raise TicketSubcategoryNotFoundError
    return subcategory


def _get_ticket_type_or_404(session: Session, type_id: int):
    ticket_type = get_ticket_type_by_id(session, type_id)
    if ticket_type is None:
        raise TicketTypeNotFoundError
    return ticket_type


def _get_ticket_priority_or_404(session: Session, priority_id: int):
    priority = get_ticket_priority_by_id(session, priority_id)
    if priority is None:
        raise TicketPriorityNotFoundError
    return priority


def _get_ticket_custom_field_or_404(session: Session, custom_field_id: int):
    custom_field = get_ticket_custom_field_by_id(session, custom_field_id)
    if custom_field is None:
        raise TicketCustomFieldNotFoundError
    return custom_field


def _get_ticket_status_or_404(session: Session, status_id: int):
    status = get_ticket_status_by_id(session, status_id)
    if status is None:
        raise TicketStatusNotFoundError
    return status


def _get_ticket_status_transition_or_404(session: Session, transition_id: int):
    transition = get_ticket_status_transition_by_id(session, transition_id)
    if transition is None:
        raise TicketStatusTransitionNotFoundError
    return transition


def _validate_subcategory_scope(session: Session, category_id: int, subcategory_id: int | None):
    if subcategory_id is None:
        return None
    subcategory = _get_ticket_subcategory_or_404(session, subcategory_id)
    if subcategory.category_id != category_id:
        raise ValidationServiceError("Ticket custom field subcategory must belong to the selected category.")
    return subcategory


def _normalize_custom_field_options(field_type: str, options: list[TicketCustomFieldOption] | None) -> list[dict]:
    if field_type != "select":
        return []
    normalized = sorted(options or [], key=lambda option: (option.display_order, option.label.lower(), option.value))
    if not normalized:
        raise ValidationServiceError("Select custom fields must have at least one option.")
    values = [option.value for option in normalized]
    if len(values) != len(set(values)):
        raise ValidationServiceError("Select custom field options must have unique values.")
    return [option.model_dump() for option in normalized]


def _validate_type_ids(session: Session, type_ids: list[int]) -> list[int]:
    if not type_ids:
        return []

    existing_types = list_ticket_types_by_ids(session, type_ids)
    existing_ids = {ticket_type.id for ticket_type in existing_types}
    missing_ids = sorted(set(type_ids) - existing_ids)
    if missing_ids:
        raise ValidationServiceError(f"Unknown ticket type ids: {', '.join(str(item) for item in missing_ids)}.")
    return type_ids


def _validate_category_id(session: Session, category_id: int):
    return _get_ticket_category_or_404(session, category_id)


def _infer_category_legacy_value(name: str) -> str:
    normalized = name.strip().lower()
    mapping = {
        "bombas de combustivel": TicketCategory.FUEL_PUMP.value,
        "bomba de combustivel": TicketCategory.FUEL_PUMP.value,
        "bicos de combustivel": TicketCategory.FUEL_NOZZLE.value,
        "bico de abastecimento": TicketCategory.FUEL_NOZZLE.value,
        "eletrica": TicketCategory.ELECTRICAL.value,
        "hidraulica": TicketCategory.PLUMBING.value,
        "vazamentos": TicketCategory.LEAK.value,
        "vazamento": TicketCategory.LEAK.value,
        "estrutura": TicketCategory.STRUCTURE.value,
        "cobertura": TicketCategory.ROOF.value,
        "pavimento": TicketCategory.PAVEMENT.value,
        "risco ambiental": TicketCategory.ENVIRONMENTAL_RISK.value,
        "outros": TicketCategory.OTHER.value,
        "outro": TicketCategory.OTHER.value,
    }
    return mapping.get(normalized, TicketCategory.OTHER.value)


def _infer_priority_legacy_value(name: str, weight: int) -> str:
    normalized = name.strip().lower()
    mapping = {
        "baixa": PriorityLevel.LOW.value,
        "media": PriorityLevel.MEDIUM.value,
        "média": PriorityLevel.MEDIUM.value,
        "alta": PriorityLevel.HIGH.value,
        "critica": PriorityLevel.CRITICAL.value,
        "crítica": PriorityLevel.CRITICAL.value,
    }
    if normalized in mapping:
        return mapping[normalized]
    if weight >= 40:
        return PriorityLevel.CRITICAL.value
    if weight >= 30:
        return PriorityLevel.HIGH.value
    if weight >= 20:
        return PriorityLevel.MEDIUM.value
    return PriorityLevel.LOW.value


def list_public_ticket_categories(
    session: Session,
    params: TicketConfigurationPageParams,
) -> TicketCategoryListResponse:
    total = count_ticket_categories(session, search=params.search, is_active=True)
    items = list_ticket_categories(
        session,
        page=params.page,
        page_size=params.page_size,
        search=params.search,
        is_active=True,
        sort=params.sort,
    )
    return TicketCategoryListResponse(
        items=[_build_category_response(item, only_active_type_ids=True) for item in items],
        total=total,
        page=params.page,
        page_size=params.page_size,
        pages=calculate_pages(total, params.page_size),
    )


def list_admin_ticket_categories(
    session: Session,
    params: TicketConfigurationPageParams,
    current_user: User,
) -> TicketCategoryListResponse:
    _ensure_admin(current_user)
    total = count_ticket_categories(session, search=params.search, is_active=params.is_active)
    items = list_ticket_categories(
        session,
        page=params.page,
        page_size=params.page_size,
        search=params.search,
        is_active=params.is_active,
        sort=params.sort,
    )
    return TicketCategoryListResponse(
        items=[_build_category_response(item, only_active_type_ids=False) for item in items],
        total=total,
        page=params.page,
        page_size=params.page_size,
        pages=calculate_pages(total, params.page_size),
    )


def create_ticket_category_record(
    session: Session,
    payload: TicketCategoryCreate,
    current_user: User,
) -> TicketCategoryResponse:
    _ensure_admin(current_user)

    if get_ticket_category_by_name(session, payload.name) is not None:
        raise DuplicateTicketCategoryError

    type_ids = _validate_type_ids(session, payload.type_ids)
    category = create_ticket_category(
        session,
        name=payload.name,
        legacy_value=_infer_category_legacy_value(payload.name),
        description=payload.description,
        is_active=payload.is_active,
        display_order=payload.display_order,
        requires_attachment=payload.requires_attachment,
        requires_location=payload.requires_location,
    )
    replace_ticket_category_types(session, category, type_ids)
    session.refresh(category)
    return _build_category_response(category, only_active_type_ids=False)


def update_ticket_category_record(
    session: Session,
    category_id: int,
    payload: TicketCategoryUpdate,
    current_user: User,
) -> TicketCategoryResponse:
    _ensure_admin(current_user)

    category = _get_ticket_category_or_404(session, category_id)
    changes = payload.model_dump(exclude_unset=True)
    type_ids = changes.pop("type_ids", None)

    if "name" in changes and changes["name"] is not None:
        existing_category = get_ticket_category_by_name(session, changes["name"])
        if existing_category is not None and existing_category.id != category.id:
            raise DuplicateTicketCategoryError
        changes["legacy_value"] = _infer_category_legacy_value(changes["name"])

    if changes:
        update_ticket_category(session, category, **changes)

    if type_ids is not None:
        replace_ticket_category_types(session, category, _validate_type_ids(session, type_ids))

    session.refresh(category)
    return _build_category_response(category, only_active_type_ids=False)


def list_public_ticket_subcategories(
    session: Session,
    category_id: int,
    params: TicketConfigurationPageParams,
) -> TicketSubcategoryListResponse:
    category = _get_ticket_category_or_404(session, category_id)
    if not category.is_active:
        raise TicketCategoryNotFoundError

    total = count_ticket_subcategories(
        session,
        category_id=category_id,
        search=params.search,
        is_active=True,
    )
    items = list_ticket_subcategories(
        session,
        page=params.page,
        page_size=params.page_size,
        category_id=category_id,
        search=params.search,
        is_active=True,
        sort=params.sort,
    )
    return TicketSubcategoryListResponse(
        items=[_build_subcategory_response(item) for item in items],
        total=total,
        page=params.page,
        page_size=params.page_size,
        pages=calculate_pages(total, params.page_size),
    )


def list_admin_ticket_subcategories(
    session: Session,
    params: TicketSubcategoryListParams,
    current_user: User,
) -> TicketSubcategoryListResponse:
    _ensure_admin(current_user)

    if params.category_id is not None:
        _validate_category_id(session, params.category_id)

    total = count_ticket_subcategories(
        session,
        category_id=params.category_id,
        search=params.search,
        is_active=params.is_active,
    )
    items = list_ticket_subcategories(
        session,
        page=params.page,
        page_size=params.page_size,
        category_id=params.category_id,
        search=params.search,
        is_active=params.is_active,
        sort=params.sort,
    )
    return TicketSubcategoryListResponse(
        items=[_build_subcategory_response(item) for item in items],
        total=total,
        page=params.page,
        page_size=params.page_size,
        pages=calculate_pages(total, params.page_size),
    )


def create_ticket_subcategory_record(
    session: Session,
    payload: TicketSubcategoryCreate,
    current_user: User,
) -> TicketSubcategoryResponse:
    _ensure_admin(current_user)
    _validate_category_id(session, payload.category_id)

    if get_ticket_subcategory_by_name(session, category_id=payload.category_id, name=payload.name) is not None:
        raise DuplicateTicketSubcategoryError

    subcategory = create_ticket_subcategory(
        session,
        category_id=payload.category_id,
        name=payload.name,
        description=payload.description,
        is_active=payload.is_active,
        display_order=payload.display_order,
    )
    session.refresh(subcategory)
    return _build_subcategory_response(subcategory)


def update_ticket_subcategory_record(
    session: Session,
    subcategory_id: int,
    payload: TicketSubcategoryUpdate,
    current_user: User,
) -> TicketSubcategoryResponse:
    _ensure_admin(current_user)
    subcategory = _get_ticket_subcategory_or_404(session, subcategory_id)
    changes = payload.model_dump(exclude_unset=True)

    next_category_id = changes.get("category_id", subcategory.category_id)
    next_name = changes.get("name", subcategory.name)
    _validate_category_id(session, next_category_id)

    existing = get_ticket_subcategory_by_name(session, category_id=next_category_id, name=next_name)
    if existing is not None and existing.id != subcategory.id:
        raise DuplicateTicketSubcategoryError

    if changes:
        update_ticket_subcategory(session, subcategory, **changes)

    session.refresh(subcategory)
    return _build_subcategory_response(subcategory)


def list_public_ticket_types(
    session: Session,
    params: TicketConfigurationPageParams,
) -> TicketTypeListResponse:
    total = count_ticket_types(session, search=params.search, is_active=True)
    items = list_ticket_types(
        session,
        page=params.page,
        page_size=params.page_size,
        search=params.search,
        is_active=True,
        sort=params.sort,
    )
    return TicketTypeListResponse(
        items=[_build_type_response(item) for item in items],
        total=total,
        page=params.page,
        page_size=params.page_size,
        pages=calculate_pages(total, params.page_size),
    )


def list_admin_ticket_types(
    session: Session,
    params: TicketConfigurationPageParams,
    current_user: User,
) -> TicketTypeListResponse:
    _ensure_admin(current_user)
    total = count_ticket_types(session, search=params.search, is_active=params.is_active)
    items = list_ticket_types(
        session,
        page=params.page,
        page_size=params.page_size,
        search=params.search,
        is_active=params.is_active,
        sort=params.sort,
    )
    return TicketTypeListResponse(
        items=[_build_type_response(item) for item in items],
        total=total,
        page=params.page,
        page_size=params.page_size,
        pages=calculate_pages(total, params.page_size),
    )


def create_ticket_type_record(
    session: Session,
    payload: TicketTypeCreate,
    current_user: User,
) -> TicketTypeResponse:
    _ensure_admin(current_user)
    if get_ticket_type_by_name(session, payload.name) is not None:
        raise DuplicateTicketTypeError

    ticket_type = create_ticket_type(
        session,
        name=payload.name,
        description=payload.description,
        is_active=payload.is_active,
        display_order=payload.display_order,
    )
    session.refresh(ticket_type)
    return _build_type_response(ticket_type)


def update_ticket_type_record(
    session: Session,
    type_id: int,
    payload: TicketTypeUpdate,
    current_user: User,
) -> TicketTypeResponse:
    _ensure_admin(current_user)
    ticket_type = _get_ticket_type_or_404(session, type_id)
    changes = payload.model_dump(exclude_unset=True)

    if "name" in changes and changes["name"] is not None:
        existing = get_ticket_type_by_name(session, changes["name"])
        if existing is not None and existing.id != ticket_type.id:
            raise DuplicateTicketTypeError

    if changes:
        update_ticket_type(session, ticket_type, **changes)
    session.refresh(ticket_type)
    return _build_type_response(ticket_type)


def list_public_ticket_priorities(
    session: Session,
    params: TicketConfigurationPageParams,
) -> TicketPriorityListResponse:
    total = count_ticket_priorities(session, search=params.search, is_active=True)
    items = list_ticket_priorities(
        session,
        page=params.page,
        page_size=params.page_size,
        search=params.search,
        is_active=True,
        sort=params.sort,
    )
    return TicketPriorityListResponse(
        items=[_build_priority_response(item) for item in items],
        total=total,
        page=params.page,
        page_size=params.page_size,
        pages=calculate_pages(total, params.page_size),
    )


def list_admin_ticket_priorities(
    session: Session,
    params: TicketConfigurationPageParams,
    current_user: User,
) -> TicketPriorityListResponse:
    _ensure_admin(current_user)
    total = count_ticket_priorities(session, search=params.search, is_active=params.is_active)
    items = list_ticket_priorities(
        session,
        page=params.page,
        page_size=params.page_size,
        search=params.search,
        is_active=params.is_active,
        sort=params.sort,
    )
    return TicketPriorityListResponse(
        items=[_build_priority_response(item) for item in items],
        total=total,
        page=params.page,
        page_size=params.page_size,
        pages=calculate_pages(total, params.page_size),
    )


def create_ticket_priority_record(
    session: Session,
    payload: TicketPriorityCreate,
    current_user: User,
) -> TicketPriorityResponse:
    _ensure_admin(current_user)
    if get_ticket_priority_by_name(session, payload.name) is not None:
        raise DuplicateTicketPriorityError

    priority = create_ticket_priority(
        session,
        name=payload.name,
        legacy_value=_infer_priority_legacy_value(payload.name, payload.weight),
        description=payload.description,
        color=payload.color,
        weight=payload.weight,
        sla_hours=payload.sla_hours,
        requires_reason=payload.requires_reason,
        is_active=payload.is_active,
        display_order=payload.display_order,
    )
    session.refresh(priority)
    return _build_priority_response(priority)


def update_ticket_priority_record(
    session: Session,
    priority_id: int,
    payload: TicketPriorityUpdate,
    current_user: User,
) -> TicketPriorityResponse:
    _ensure_admin(current_user)
    priority = _get_ticket_priority_or_404(session, priority_id)
    changes = payload.model_dump(exclude_unset=True)

    if "name" in changes and changes["name"] is not None:
        existing = get_ticket_priority_by_name(session, changes["name"])
        if existing is not None and existing.id != priority.id:
            raise DuplicateTicketPriorityError
    if "name" in changes or "weight" in changes:
        next_name = changes.get("name", priority.name)
        next_weight = int(changes.get("weight", priority.weight))
        changes["legacy_value"] = _infer_priority_legacy_value(next_name, next_weight)

    if changes:
        update_ticket_priority(session, priority, **changes)
    session.refresh(priority)
    return _build_priority_response(priority)


def list_public_ticket_statuses(
    session: Session,
    params: TicketConfigurationPageParams,
) -> TicketStatusListResponse:
    total = count_ticket_statuses(session, search=params.search, is_active=True)
    items = list_ticket_statuses(
        session,
        page=params.page,
        page_size=params.page_size,
        search=params.search,
        is_active=True,
        sort=params.sort,
    )
    return TicketStatusListResponse(
        items=[_build_status_response(item) for item in items],
        total=total,
        page=params.page,
        page_size=params.page_size,
        pages=calculate_pages(total, params.page_size),
    )


def list_admin_ticket_statuses(
    session: Session,
    params: TicketConfigurationPageParams,
    current_user: User,
) -> TicketStatusListResponse:
    _ensure_admin(current_user)
    total = count_ticket_statuses(session, search=params.search, is_active=params.is_active)
    items = list_ticket_statuses(
        session,
        page=params.page,
        page_size=params.page_size,
        search=params.search,
        is_active=params.is_active,
        sort=params.sort,
    )
    return TicketStatusListResponse(
        items=[_build_status_response(item) for item in items],
        total=total,
        page=params.page,
        page_size=params.page_size,
        pages=calculate_pages(total, params.page_size),
    )


def create_ticket_status_record(
    session: Session,
    payload: TicketStatusCreate,
    current_user: User,
) -> TicketStatusResponse:
    _ensure_admin(current_user)
    if get_ticket_status_by_name(session, payload.name) is not None:
        raise DuplicateTicketStatusError

    status = create_ticket_status(session, **payload.model_dump())
    session.refresh(status)
    return _build_status_response(status)


def update_ticket_status_record(
    session: Session,
    status_id: int,
    payload: TicketStatusUpdate,
    current_user: User,
) -> TicketStatusResponse:
    _ensure_admin(current_user)
    status = _get_ticket_status_or_404(session, status_id)
    changes = payload.model_dump(exclude_unset=True)

    if "name" in changes and changes["name"] is not None:
        existing = get_ticket_status_by_name(session, changes["name"])
        if existing is not None and existing.id != status.id:
            raise DuplicateTicketStatusError

    if changes:
        update_ticket_status(session, status, **changes)
    session.refresh(status)
    return _build_status_response(status)


def list_admin_ticket_status_transitions(
    session: Session,
    params: TicketStatusTransitionListParams,
    current_user: User,
) -> TicketStatusTransitionListResponse:
    _ensure_admin(current_user)
    if params.from_status_id is not None:
        _get_ticket_status_or_404(session, params.from_status_id)

    total = count_ticket_status_transitions(
        session,
        from_status_id=params.from_status_id,
        is_active=params.is_active,
    )
    items = list_ticket_status_transitions(
        session,
        page=params.page,
        page_size=params.page_size,
        from_status_id=params.from_status_id,
        is_active=params.is_active,
    )
    return TicketStatusTransitionListResponse(
        items=[_build_transition_response(item) for item in items],
        total=total,
        page=params.page,
        page_size=params.page_size,
        pages=calculate_pages(total, params.page_size),
    )


def _validate_transition_payload(
    session: Session,
    *,
    from_status_id: int,
    to_status_id: int,
    current_transition_id: int | None = None,
) -> None:
    if from_status_id == to_status_id:
        raise ValidationServiceError("Transition target must be different from the source status.")
    _get_ticket_status_or_404(session, from_status_id)
    _get_ticket_status_or_404(session, to_status_id)
    existing = get_ticket_status_transition(session, from_status_id=from_status_id, to_status_id=to_status_id)
    if existing is not None and existing.id != current_transition_id:
        raise DuplicateTicketStatusTransitionError


def create_ticket_status_transition_record(
    session: Session,
    payload: TicketStatusTransitionCreate,
    current_user: User,
) -> TicketStatusTransitionResponse:
    _ensure_admin(current_user)
    _validate_transition_payload(
        session,
        from_status_id=payload.from_status_id,
        to_status_id=payload.to_status_id,
    )
    transition = create_ticket_status_transition(session, **payload.model_dump())
    session.refresh(transition)
    return _build_transition_response(transition)


def update_ticket_status_transition_record(
    session: Session,
    transition_id: int,
    payload: TicketStatusTransitionUpdate,
    current_user: User,
) -> TicketStatusTransitionResponse:
    _ensure_admin(current_user)
    transition = _get_ticket_status_transition_or_404(session, transition_id)
    changes = payload.model_dump(exclude_unset=True)

    next_from_status_id = changes.get("from_status_id", transition.from_status_id)
    next_to_status_id = changes.get("to_status_id", transition.to_status_id)
    if "from_status_id" in changes or "to_status_id" in changes:
        _validate_transition_payload(
            session,
            from_status_id=next_from_status_id,
            to_status_id=next_to_status_id,
            current_transition_id=transition.id,
        )

    if changes:
        update_ticket_status_transition(session, transition, **changes)
    session.refresh(transition)
    return _build_transition_response(transition)


def list_admin_ticket_custom_fields(
    session: Session,
    params: TicketCustomFieldListParams,
    current_user: User,
) -> TicketCustomFieldListResponse:
    _ensure_admin(current_user)
    total = count_ticket_custom_fields(
        session,
        category_id=params.category_id,
        subcategory_id=params.subcategory_id,
        search=params.search,
        is_active=params.is_active,
    )
    items = list_ticket_custom_fields(
        session,
        page=params.page,
        page_size=params.page_size,
        category_id=params.category_id,
        subcategory_id=params.subcategory_id,
        search=params.search,
        is_active=params.is_active,
        sort=params.sort,
    )
    return TicketCustomFieldListResponse(
        items=[_build_custom_field_response(item) for item in items],
        total=total,
        page=params.page,
        page_size=params.page_size,
        pages=calculate_pages(total, params.page_size),
    )


def create_ticket_custom_field_record(
    session: Session,
    payload: TicketCustomFieldCreate,
    current_user: User,
) -> TicketCustomFieldResponse:
    _ensure_admin(current_user)
    _get_ticket_category_or_404(session, payload.category_id)
    _validate_subcategory_scope(session, payload.category_id, payload.subcategory_id)
    if get_ticket_custom_field_by_name(
        session,
        category_id=payload.category_id,
        subcategory_id=payload.subcategory_id,
        name=payload.name,
    ):
        raise DuplicateTicketCustomFieldError
    custom_field = create_ticket_custom_field(
        session,
        category_id=payload.category_id,
        subcategory_id=payload.subcategory_id,
        name=payload.name,
        label=payload.label,
        description=payload.description,
        field_type=payload.field_type,
        is_required=payload.is_required,
        is_active=payload.is_active,
        display_order=payload.display_order,
        placeholder=payload.placeholder,
        help_text=payload.help_text,
        validation_json=payload.validation_json,
        options_json=_normalize_custom_field_options(payload.field_type, payload.options),
    )
    session.refresh(custom_field)
    return _build_custom_field_response(custom_field)


def update_ticket_custom_field_record(
    session: Session,
    custom_field_id: int,
    payload: TicketCustomFieldUpdate,
    current_user: User,
) -> TicketCustomFieldResponse:
    _ensure_admin(current_user)
    custom_field = _get_ticket_custom_field_or_404(session, custom_field_id)
    changes = payload.model_dump(exclude_unset=True)
    next_category_id = changes.get("category_id", custom_field.category_id)
    next_subcategory_id = changes.get("subcategory_id", custom_field.subcategory_id)
    next_field_type = changes.get("field_type", custom_field.field_type)
    if "category_id" in changes:
        _get_ticket_category_or_404(session, next_category_id)
    if "subcategory_id" in changes or "category_id" in changes:
        _validate_subcategory_scope(session, next_category_id, next_subcategory_id)
    if "name" in changes and changes["name"] is not None:
        existing = get_ticket_custom_field_by_name(
            session,
            category_id=next_category_id,
            subcategory_id=next_subcategory_id,
            name=changes["name"],
        )
        if existing is not None and existing.id != custom_field.id:
            raise DuplicateTicketCustomFieldError
    if "options" in changes:
        changes["options_json"] = _normalize_custom_field_options(next_field_type, payload.options)
        changes.pop("options", None)
    elif "field_type" in changes and next_field_type != "select":
        changes["options_json"] = []
    elif "field_type" in changes and next_field_type == "select":
        changes["options_json"] = _normalize_custom_field_options(next_field_type, _sorted_options(custom_field.options_json))
    update_ticket_custom_field(session, custom_field, **changes)
    session.refresh(custom_field)
    return _build_custom_field_response(custom_field)


def get_ticket_form_schema(
    session: Session,
    *,
    category_id: int,
    subcategory_id: int | None = None,
) -> TicketFormSchemaResponse:
    category = _get_ticket_category_or_404(session, category_id)
    if not category.is_active:
        raise TicketCategoryNotFoundError
    if subcategory_id is not None:
        subcategory = _validate_subcategory_scope(session, category_id, subcategory_id)
        if subcategory is not None and not subcategory.is_active:
            raise TicketSubcategoryNotFoundError
    fields = list_active_ticket_custom_fields_for_scope(
        session,
        category_id=category_id,
        subcategory_id=subcategory_id,
    )
    return TicketFormSchemaResponse(
        category_id=category_id,
        subcategory_id=subcategory_id,
        fields=[_build_custom_field_response(field) for field in fields],
    )
