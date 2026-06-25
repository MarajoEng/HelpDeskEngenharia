from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.approval_level import ApprovalLevel
from app.models.enums import UserRole
from app.models.user import User
from app.repositories.approval_level_repository import (
    count_approval_levels,
    create_approval_level,
    find_overlapping_active_approval_level,
    get_approval_level_by_id,
    list_approval_levels,
    update_approval_level,
)
from app.schemas.approval import (
    ApprovalLevelCreate,
    ApprovalLevelListParams,
    ApprovalLevelListResponse,
    ApprovalLevelResponse,
    ApprovalLevelUpdate,
)
from app.schemas.pagination import calculate_pages
from app.services.exceptions import ConflictServiceError, NotFoundServiceError, ValidationServiceError


class ApprovalLevelNotFoundError(NotFoundServiceError):
    detail = "Approval level not found."


class ApprovalLevelPermissionError(ValidationServiceError):
    status_code = 403
    detail = "Insufficient permissions."


class ApprovalLevelRangeConflictError(ConflictServiceError):
    detail = "Active approval level range overlaps an existing active range."


def _can_view_approval_levels(current_user: User) -> bool:
    return current_user.role in {UserRole.ADMIN, UserRole.ENGINEERING, UserRole.DIRECTOR}


def _enforce_view_permission(current_user: User) -> None:
    if not _can_view_approval_levels(current_user):
        raise ApprovalLevelPermissionError


def _enforce_admin_permission(current_user: User) -> None:
    if current_user.role != UserRole.ADMIN:
        raise ApprovalLevelPermissionError


def _ensure_non_overlapping_range(
    session: Session,
    *,
    min_amount,
    max_amount,
    is_active: bool,
    exclude_id: int | None = None,
) -> None:
    if not is_active:
        return

    overlap = find_overlapping_active_approval_level(
        session,
        min_amount=min_amount,
        max_amount=max_amount,
        exclude_id=exclude_id,
    )
    if overlap is not None:
        raise ApprovalLevelRangeConflictError


def get_approval_level_or_404(session: Session, approval_level_id: int) -> ApprovalLevel:
    approval_level = get_approval_level_by_id(session, approval_level_id)
    if approval_level is None:
        raise ApprovalLevelNotFoundError
    return approval_level


def create_approval_level_record(
    session: Session,
    payload: ApprovalLevelCreate,
    current_user: User,
) -> ApprovalLevelResponse:
    _enforce_admin_permission(current_user)
    _ensure_non_overlapping_range(
        session,
        min_amount=payload.min_amount,
        max_amount=payload.max_amount,
        is_active=payload.is_active,
    )

    approval_level = create_approval_level(
        session,
        name=payload.name,
        min_amount=payload.min_amount,
        max_amount=payload.max_amount,
        allowed_roles=[role.value for role in payload.allowed_roles],
        is_active=payload.is_active,
    )
    session.commit()
    return ApprovalLevelResponse.model_validate(approval_level)


def list_approval_level_records(
    session: Session,
    params: ApprovalLevelListParams,
    current_user: User,
) -> ApprovalLevelListResponse:
    _enforce_view_permission(current_user)

    total = count_approval_levels(session, search=params.search, is_active=params.is_active)
    items = list_approval_levels(
        session,
        page=params.page,
        page_size=params.page_size,
        search=params.search,
        is_active=params.is_active,
        sort=params.sort,
    )
    return ApprovalLevelListResponse(
        items=[ApprovalLevelResponse.model_validate(item) for item in items],
        total=total,
        page=params.page,
        page_size=params.page_size,
        pages=calculate_pages(total, params.page_size),
    )


def get_approval_level_record(
    session: Session,
    approval_level_id: int,
    current_user: User,
) -> ApprovalLevelResponse:
    _enforce_view_permission(current_user)
    approval_level = get_approval_level_or_404(session, approval_level_id)
    return ApprovalLevelResponse.model_validate(approval_level)


def update_approval_level_record(
    session: Session,
    approval_level_id: int,
    payload: ApprovalLevelUpdate,
    current_user: User,
) -> ApprovalLevelResponse:
    _enforce_admin_permission(current_user)
    approval_level = get_approval_level_or_404(session, approval_level_id)
    changes = payload.model_dump(exclude_unset=True)
    if not changes:
        return ApprovalLevelResponse.model_validate(approval_level)

    next_min_amount = changes.get("min_amount", approval_level.min_amount)
    next_max_amount = changes.get("max_amount", approval_level.max_amount)
    next_is_active = changes.get("is_active", approval_level.is_active)

    if next_max_amount is not None and next_max_amount < next_min_amount:
        raise ValidationServiceError("max_amount must be greater than or equal to min_amount.")

    _ensure_non_overlapping_range(
        session,
        min_amount=next_min_amount,
        max_amount=next_max_amount,
        is_active=next_is_active,
        exclude_id=approval_level.id,
    )

    if "allowed_roles" in changes and changes["allowed_roles"] is not None:
        changes["allowed_roles"] = [role.value for role in changes["allowed_roles"]]

    updated = update_approval_level(session, approval_level, **changes)
    session.commit()
    return ApprovalLevelResponse.model_validate(updated)
