from __future__ import annotations

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.database import get_db_session
from app.models.user import User
from app.schemas import (
    TicketCategoryCreate,
    TicketCategoryListResponse,
    TicketCategoryResponse,
    TicketCategoryUpdate,
    TicketConfigurationPageParams,
    TicketCustomFieldCreate,
    TicketCustomFieldListParams,
    TicketCustomFieldListResponse,
    TicketCustomFieldResponse,
    TicketCustomFieldUpdate,
    TicketPriorityCreate,
    TicketPriorityListResponse,
    TicketPriorityResponse,
    TicketPriorityUpdate,
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
from app.services.audit_service import log_action
from app.services.exceptions import ServiceError
from app.services.ticket_configuration_service import (
    create_ticket_category_record,
    create_ticket_custom_field_record,
    create_ticket_priority_record,
    create_ticket_subcategory_record,
    create_ticket_type_record,
    list_admin_ticket_categories,
    list_admin_ticket_custom_fields,
    list_admin_ticket_priorities,
    list_admin_ticket_subcategories,
    list_admin_ticket_types,
    list_public_ticket_categories,
    list_public_ticket_priorities,
    list_public_ticket_subcategories,
    list_public_ticket_types,
    update_ticket_category_record,
    update_ticket_custom_field_record,
    update_ticket_priority_record,
    update_ticket_subcategory_record,
    update_ticket_type_record,
)


router = APIRouter(tags=["ticket-configuration"])


def _raise_service_error(error: ServiceError) -> None:
    raise HTTPException(status_code=error.status_code, detail=error.detail)


def _build_page_params(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: str | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    sort: Literal["display_order_asc", "created_at_desc", "name_asc"] = Query(default="display_order_asc"),
) -> TicketConfigurationPageParams:
    return TicketConfigurationPageParams(
        page=page,
        page_size=page_size,
        search=search,
        is_active=is_active,
        sort=sort,
    )


def _build_subcategory_params(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: str | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    category_id: int | None = Query(default=None, ge=1),
    sort: Literal["display_order_asc", "created_at_desc", "name_asc"] = Query(default="display_order_asc"),
) -> TicketSubcategoryListParams:
    return TicketSubcategoryListParams(
        page=page,
        page_size=page_size,
        search=search,
        is_active=is_active,
        category_id=category_id,
        sort=sort,
    )


def _build_custom_field_params(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: str | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    category_id: int | None = Query(default=None, ge=1),
    subcategory_id: int | None = Query(default=None, ge=1),
    sort: Literal["display_order_asc", "created_at_desc", "name_asc"] = Query(default="display_order_asc"),
) -> TicketCustomFieldListParams:
    return TicketCustomFieldListParams(
        page=page,
        page_size=page_size,
        search=search,
        is_active=is_active,
        category_id=category_id,
        subcategory_id=subcategory_id,
        sort=sort,
    )


@router.get("/ticket-categories", response_model=TicketCategoryListResponse)
def read_ticket_categories(
    params: Annotated[TicketConfigurationPageParams, Depends(_build_page_params)],
    session: Session = Depends(get_db_session),
) -> TicketCategoryListResponse:
    try:
        return list_public_ticket_categories(session, params)
    except ServiceError as error:
        _raise_service_error(error)


@router.get("/ticket-categories/{category_id}/subcategories", response_model=TicketSubcategoryListResponse)
def read_ticket_subcategories(
    category_id: int,
    params: Annotated[TicketConfigurationPageParams, Depends(_build_page_params)],
    session: Session = Depends(get_db_session),
) -> TicketSubcategoryListResponse:
    try:
        return list_public_ticket_subcategories(session, category_id, params)
    except ServiceError as error:
        _raise_service_error(error)


@router.get("/ticket-types", response_model=TicketTypeListResponse)
def read_ticket_types(
    params: Annotated[TicketConfigurationPageParams, Depends(_build_page_params)],
    session: Session = Depends(get_db_session),
) -> TicketTypeListResponse:
    try:
        return list_public_ticket_types(session, params)
    except ServiceError as error:
        _raise_service_error(error)


@router.get("/ticket-priorities", response_model=TicketPriorityListResponse)
def read_ticket_priorities(
    params: Annotated[TicketConfigurationPageParams, Depends(_build_page_params)],
    session: Session = Depends(get_db_session),
) -> TicketPriorityListResponse:
    try:
        return list_public_ticket_priorities(session, params)
    except ServiceError as error:
        _raise_service_error(error)


@router.get("/admin/ticket-categories", response_model=TicketCategoryListResponse)
def read_admin_ticket_categories(
    params: Annotated[TicketConfigurationPageParams, Depends(_build_page_params)],
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> TicketCategoryListResponse:
    try:
        return list_admin_ticket_categories(session, params, current_user)
    except ServiceError as error:
        _raise_service_error(error)


@router.post("/admin/ticket-categories", response_model=TicketCategoryResponse, status_code=status.HTTP_201_CREATED)
def create_ticket_category(
    payload: TicketCategoryCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> TicketCategoryResponse:
    try:
        category = create_ticket_category_record(session, payload, current_user)
    except ServiceError as error:
        _raise_service_error(error)

    log_action(
        session,
        actor_user=current_user,
        action="ticket_category_created",
        entity_type="ticket_category",
        entity_id=category.id,
        request=request,
        metadata={"name": category.name},
    )
    session.commit()
    return category


@router.patch("/admin/ticket-categories/{category_id}", response_model=TicketCategoryResponse)
def patch_ticket_category(
    category_id: int,
    payload: TicketCategoryUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> TicketCategoryResponse:
    try:
        category = update_ticket_category_record(session, category_id, payload, current_user)
    except ServiceError as error:
        _raise_service_error(error)

    log_action(
        session,
        actor_user=current_user,
        action="ticket_category_updated",
        entity_type="ticket_category",
        entity_id=category.id,
        request=request,
        metadata={"name": category.name},
    )
    session.commit()
    return category


@router.get("/admin/ticket-subcategories", response_model=TicketSubcategoryListResponse)
def read_admin_ticket_subcategories(
    params: Annotated[TicketSubcategoryListParams, Depends(_build_subcategory_params)],
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> TicketSubcategoryListResponse:
    try:
        return list_admin_ticket_subcategories(session, params, current_user)
    except ServiceError as error:
        _raise_service_error(error)


@router.post("/admin/ticket-subcategories", response_model=TicketSubcategoryResponse, status_code=status.HTTP_201_CREATED)
def create_ticket_subcategory(
    payload: TicketSubcategoryCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> TicketSubcategoryResponse:
    try:
        subcategory = create_ticket_subcategory_record(session, payload, current_user)
    except ServiceError as error:
        _raise_service_error(error)

    log_action(
        session,
        actor_user=current_user,
        action="ticket_subcategory_created",
        entity_type="ticket_subcategory",
        entity_id=subcategory.id,
        request=request,
        metadata={"name": subcategory.name, "category_id": subcategory.category_id},
    )
    session.commit()
    return subcategory


@router.patch("/admin/ticket-subcategories/{subcategory_id}", response_model=TicketSubcategoryResponse)
def patch_ticket_subcategory(
    subcategory_id: int,
    payload: TicketSubcategoryUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> TicketSubcategoryResponse:
    try:
        subcategory = update_ticket_subcategory_record(session, subcategory_id, payload, current_user)
    except ServiceError as error:
        _raise_service_error(error)

    log_action(
        session,
        actor_user=current_user,
        action="ticket_subcategory_updated",
        entity_type="ticket_subcategory",
        entity_id=subcategory.id,
        request=request,
        metadata={"name": subcategory.name, "category_id": subcategory.category_id},
    )
    session.commit()
    return subcategory


@router.get("/admin/ticket-types", response_model=TicketTypeListResponse)
def read_admin_ticket_types(
    params: Annotated[TicketConfigurationPageParams, Depends(_build_page_params)],
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> TicketTypeListResponse:
    try:
        return list_admin_ticket_types(session, params, current_user)
    except ServiceError as error:
        _raise_service_error(error)


@router.post("/admin/ticket-types", response_model=TicketTypeResponse, status_code=status.HTTP_201_CREATED)
def create_ticket_type(
    payload: TicketTypeCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> TicketTypeResponse:
    try:
        ticket_type = create_ticket_type_record(session, payload, current_user)
    except ServiceError as error:
        _raise_service_error(error)

    log_action(
        session,
        actor_user=current_user,
        action="ticket_type_created",
        entity_type="ticket_type",
        entity_id=ticket_type.id,
        request=request,
        metadata={"name": ticket_type.name},
    )
    session.commit()
    return ticket_type


@router.patch("/admin/ticket-types/{type_id}", response_model=TicketTypeResponse)
def patch_ticket_type(
    type_id: int,
    payload: TicketTypeUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> TicketTypeResponse:
    try:
        ticket_type = update_ticket_type_record(session, type_id, payload, current_user)
    except ServiceError as error:
        _raise_service_error(error)

    log_action(
        session,
        actor_user=current_user,
        action="ticket_type_updated",
        entity_type="ticket_type",
        entity_id=ticket_type.id,
        request=request,
        metadata={"name": ticket_type.name},
    )
    session.commit()
    return ticket_type


@router.get("/admin/ticket-priorities", response_model=TicketPriorityListResponse)
def read_admin_ticket_priorities(
    params: Annotated[TicketConfigurationPageParams, Depends(_build_page_params)],
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> TicketPriorityListResponse:
    try:
        return list_admin_ticket_priorities(session, params, current_user)
    except ServiceError as error:
        _raise_service_error(error)


@router.post("/admin/ticket-priorities", response_model=TicketPriorityResponse, status_code=status.HTTP_201_CREATED)
def create_ticket_priority(
    payload: TicketPriorityCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> TicketPriorityResponse:
    try:
        priority = create_ticket_priority_record(session, payload, current_user)
    except ServiceError as error:
        _raise_service_error(error)

    log_action(
        session,
        actor_user=current_user,
        action="ticket_priority_created",
        entity_type="ticket_priority",
        entity_id=priority.id,
        request=request,
        metadata={"name": priority.name},
    )
    session.commit()
    return priority


@router.get("/admin/ticket-custom-fields", response_model=TicketCustomFieldListResponse)
def read_admin_ticket_custom_fields(
    params: Annotated[TicketCustomFieldListParams, Depends(_build_custom_field_params)],
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> TicketCustomFieldListResponse:
    try:
        return list_admin_ticket_custom_fields(session, params, current_user)
    except ServiceError as error:
        _raise_service_error(error)


@router.post("/admin/ticket-custom-fields", response_model=TicketCustomFieldResponse, status_code=status.HTTP_201_CREATED)
def create_ticket_custom_field(
    payload: TicketCustomFieldCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> TicketCustomFieldResponse:
    try:
        custom_field = create_ticket_custom_field_record(session, payload, current_user)
    except ServiceError as error:
        _raise_service_error(error)

    log_action(
        session,
        actor_user=current_user,
        action="ticket_custom_field_created",
        entity_type="ticket_custom_field",
        entity_id=custom_field.id,
        request=request,
        metadata={"name": custom_field.name, "category_id": custom_field.category_id},
    )
    session.commit()
    return custom_field


@router.patch("/admin/ticket-custom-fields/{custom_field_id}", response_model=TicketCustomFieldResponse)
def patch_ticket_custom_field(
    custom_field_id: int,
    payload: TicketCustomFieldUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> TicketCustomFieldResponse:
    try:
        custom_field = update_ticket_custom_field_record(session, custom_field_id, payload, current_user)
    except ServiceError as error:
        _raise_service_error(error)

    log_action(
        session,
        actor_user=current_user,
        action="ticket_custom_field_updated",
        entity_type="ticket_custom_field",
        entity_id=custom_field.id,
        request=request,
        metadata={"name": custom_field.name, "category_id": custom_field.category_id},
    )
    session.commit()
    return custom_field


@router.patch("/admin/ticket-priorities/{priority_id}", response_model=TicketPriorityResponse)
def patch_ticket_priority(
    priority_id: int,
    payload: TicketPriorityUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> TicketPriorityResponse:
    try:
        priority = update_ticket_priority_record(session, priority_id, payload, current_user)
    except ServiceError as error:
        _raise_service_error(error)

    log_action(
        session,
        actor_user=current_user,
        action="ticket_priority_updated",
        entity_type="ticket_priority",
        entity_id=priority.id,
        request=request,
        metadata={"name": priority.name},
    )
    session.commit()
    return priority
