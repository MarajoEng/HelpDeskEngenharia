from __future__ import annotations

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, require_roles
from app.core.database import get_db_session
from app.models.enums import UserRole
from app.models.user import User
from app.schemas import UserCreate, UserListParams, UserListResponse, UserResponse, UserUpdate
from app.services.exceptions import ServiceError
from app.services.user_service import create_user_record, get_user_or_404, list_user_records, update_user_record


router = APIRouter(prefix="/users", tags=["users"])


def _raise_service_error(error: ServiceError) -> None:
    raise HTTPException(status_code=error.status_code, detail=error.detail)


def _build_list_params(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: str | None = Query(default=None),
    role: UserRole | None = Query(default=None),
    unit_id: int | None = Query(default=None, ge=1),
    is_active: bool | None = Query(default=None),
    sort: Literal["name_asc", "created_at_desc"] = Query(default="name_asc"),
) -> UserListParams:
    return UserListParams(
        page=page,
        page_size=page_size,
        search=search,
        role=role,
        unit_id=unit_id,
        is_active=is_active,
        sort=sort,
    )


@router.get("", response_model=UserListResponse)
def read_users(
    params: Annotated[UserListParams, Depends(_build_list_params)],
    _: User = Depends(require_roles(UserRole.ADMIN)),
    session: Session = Depends(get_db_session),
) -> UserListResponse:
    return list_user_records(session, params)


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreate,
    _: User = Depends(require_roles(UserRole.ADMIN)),
    session: Session = Depends(get_db_session),
) -> UserResponse:
    try:
        user = create_user_record(session, payload)
    except ServiceError as error:
        _raise_service_error(error)

    return UserResponse.model_validate(user)


@router.get("/{user_id}", response_model=UserResponse)
def read_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> UserResponse:
    if current_user.role != UserRole.ADMIN and current_user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions.")

    try:
        user = get_user_or_404(session, user_id)
    except ServiceError as error:
        _raise_service_error(error)

    return UserResponse.model_validate(user)


@router.patch("/{user_id}", response_model=UserResponse)
def patch_user(
    user_id: int,
    payload: UserUpdate,
    _: User = Depends(require_roles(UserRole.ADMIN)),
    session: Session = Depends(get_db_session),
) -> UserResponse:
    try:
        user = update_user_record(session, user_id, payload)
    except ServiceError as error:
        _raise_service_error(error)

    return UserResponse.model_validate(user)
