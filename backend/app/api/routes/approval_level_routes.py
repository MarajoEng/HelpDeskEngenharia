from __future__ import annotations

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.database import get_db_session
from app.models.user import User
from app.schemas.approval import (
    ApprovalLevelCreate,
    ApprovalLevelListParams,
    ApprovalLevelListResponse,
    ApprovalLevelResponse,
    ApprovalLevelUpdate,
)
from app.services.approval_level_service import (
    create_approval_level_record,
    get_approval_level_record,
    list_approval_level_records,
    update_approval_level_record,
)
from app.services.audit_service import log_action
from app.services.exceptions import ServiceError


router = APIRouter(prefix="/approval-levels", tags=["approval-levels"])


def _raise_service_error(error: ServiceError) -> None:
    raise HTTPException(status_code=error.status_code, detail=error.detail)


def _build_list_params(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: str | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    sort: Literal["name_asc", "created_at_desc"] = Query(default="name_asc"),
) -> ApprovalLevelListParams:
    return ApprovalLevelListParams(
        page=page,
        page_size=page_size,
        search=search,
        is_active=is_active,
        sort=sort,
    )


@router.get("", response_model=ApprovalLevelListResponse)
def read_approval_levels(
    params: Annotated[ApprovalLevelListParams, Depends(_build_list_params)],
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> ApprovalLevelListResponse:
    try:
        return list_approval_level_records(session, params, current_user)
    except ServiceError as error:
        _raise_service_error(error)


@router.post("", response_model=ApprovalLevelResponse, status_code=status.HTTP_201_CREATED)
def create_approval_level_endpoint(
    payload: ApprovalLevelCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> ApprovalLevelResponse:
    try:
        result = create_approval_level_record(session, payload, current_user)
    except ServiceError as error:
        _raise_service_error(error)

    log_action(session, actor_user=current_user, action="approval_level_created", entity_type="approval_level", entity_id=result.id, request=request, metadata={"name": result.name})
    session.commit()
    return result


@router.get("/{approval_level_id}", response_model=ApprovalLevelResponse)
def read_approval_level(
    approval_level_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> ApprovalLevelResponse:
    try:
        return get_approval_level_record(session, approval_level_id, current_user)
    except ServiceError as error:
        _raise_service_error(error)


@router.patch("/{approval_level_id}", response_model=ApprovalLevelResponse)
def patch_approval_level(
    approval_level_id: int,
    payload: ApprovalLevelUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> ApprovalLevelResponse:
    try:
        result = update_approval_level_record(session, approval_level_id, payload, current_user)
    except ServiceError as error:
        _raise_service_error(error)

    log_action(session, actor_user=current_user, action="approval_level_updated", entity_type="approval_level", entity_id=approval_level_id, request=request)
    session.commit()
    return result
