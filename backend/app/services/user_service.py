from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.enums import UserRole
from app.models.user import User
from app.repositories.unit_repository import get_unit_by_id
from app.repositories.user_repository import count_users, create_user, get_user_by_email, get_user_by_id, list_users, update_user
from app.schemas import UserCreate, UserListParams, UserListResponse, UserResponse, UserUpdate
from app.schemas.pagination import calculate_pages
from app.services.exceptions import ConflictServiceError, NotFoundServiceError, ValidationServiceError


class UserNotFoundError(NotFoundServiceError):
    detail = "User not found."


class DuplicateUserEmailError(ConflictServiceError):
    detail = "User email already exists."


class InvalidUserUnitError(ValidationServiceError):
    detail = "Provided unit does not exist."


class InvalidUserRoleConfigurationError(ValidationServiceError):
    detail = "Manager must have unit_id."


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _ensure_role_configuration(role: UserRole, unit_id: int | None) -> None:
    if role == UserRole.MANAGER and unit_id is None:
        raise InvalidUserRoleConfigurationError


def _ensure_unit_exists(session: Session, unit_id: int | None) -> None:
    if unit_id is None:
        return

    if get_unit_by_id(session, unit_id) is None:
        raise InvalidUserUnitError


def get_user_or_404(session: Session, user_id: int) -> User:
    user = get_user_by_id(session, user_id)
    if user is None:
        raise UserNotFoundError
    return user


def create_user_record(session: Session, payload: UserCreate) -> User:
    normalized_email = _normalize_email(payload.email)
    if get_user_by_email(session, normalized_email) is not None:
        raise DuplicateUserEmailError

    _ensure_role_configuration(payload.role, payload.unit_id)
    _ensure_unit_exists(session, payload.unit_id)

    return create_user(
        session,
        name=payload.name,
        email=normalized_email,
        password_hash=hash_password(payload.password),
        role=payload.role,
        unit_id=payload.unit_id,
        is_active=payload.is_active,
    )


def list_user_records(session: Session, params: UserListParams) -> UserListResponse:
    total = count_users(
        session,
        search=params.search,
        role=params.role,
        unit_id=params.unit_id,
        is_active=params.is_active,
    )
    items = list_users(
        session,
        page=params.page,
        page_size=params.page_size,
        search=params.search,
        role=params.role,
        unit_id=params.unit_id,
        is_active=params.is_active,
        sort=params.sort,
    )
    return UserListResponse(
        items=[UserResponse.model_validate(user) for user in items],
        total=total,
        page=params.page,
        page_size=params.page_size,
        pages=calculate_pages(total, params.page_size),
    )


def update_user_record(session: Session, user_id: int, payload: UserUpdate) -> User:
    user = get_user_or_404(session, user_id)
    changes = payload.model_dump(exclude_unset=True)

    next_role = changes.get("role", user.role)
    next_unit_id = changes.get("unit_id", user.unit_id)

    _ensure_role_configuration(next_role, next_unit_id)
    _ensure_unit_exists(session, next_unit_id)

    if "email" in changes:
        normalized_email = _normalize_email(changes["email"])
        existing_user = get_user_by_email(session, normalized_email)
        if existing_user is not None and existing_user.id != user.id:
            raise DuplicateUserEmailError
        changes["email"] = normalized_email

    if "password" in changes:
        changes["password_hash"] = hash_password(changes.pop("password"))

    if not changes:
        return user

    return update_user(session, user, **changes)
