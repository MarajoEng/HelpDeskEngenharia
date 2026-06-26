from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.unit import Unit
from app.repositories.unit_repository import count_units, create_unit, get_unit_by_code, get_unit_by_id, list_unit_groups, list_units, update_unit
from app.schemas import UnitCreate, UnitListParams, UnitListResponse, UnitResponse, UnitUpdate
from app.schemas.unit import UnitGroupResponse
from app.schemas.pagination import calculate_pages
from app.services.exceptions import ConflictServiceError, NotFoundServiceError


class UnitNotFoundError(NotFoundServiceError):
    detail = "Unit not found."


class DuplicateUnitCodeError(ConflictServiceError):
    detail = "Unit code already exists."


def _normalize_code(code: str) -> str:
    return code.strip().upper()


def get_unit_or_404(session: Session, unit_id: int) -> Unit:
    unit = get_unit_by_id(session, unit_id)
    if unit is None:
        raise UnitNotFoundError
    return unit


def create_unit_record(session: Session, payload: UnitCreate) -> Unit:
    normalized_code = _normalize_code(payload.code)
    if get_unit_by_code(session, normalized_code) is not None:
        raise DuplicateUnitCodeError

    return create_unit(
        session,
        code=normalized_code,
        group_code=payload.group_code,
        branch_code=payload.branch_code,
        name=payload.name,
        city=payload.city,
        state=payload.state,
        region=payload.region,
        is_active=payload.is_active,
    )


def list_unit_records(session: Session, params: UnitListParams) -> UnitListResponse:
    total = count_units(
        session,
        search=params.search,
        is_active=params.is_active,
        state=params.state,
        region=params.region,
        group_code=params.group_code,
        branch_code=params.branch_code,
    )
    items = list_units(
        session,
        page=params.page,
        page_size=params.page_size,
        search=params.search,
        is_active=params.is_active,
        state=params.state,
        region=params.region,
        group_code=params.group_code,
        branch_code=params.branch_code,
        sort=params.sort,
    )
    return UnitListResponse(
        items=[UnitResponse.model_validate(unit) for unit in items],
        total=total,
        page=params.page,
        page_size=params.page_size,
        pages=calculate_pages(total, params.page_size),
    )


def list_unit_group_records(session: Session) -> list[UnitGroupResponse]:
    rows = list_unit_groups(session)
    return [UnitGroupResponse(group_code=row["group_code"], total_units=row["total_units"]) for row in rows]


def update_unit_record(session: Session, unit_id: int, payload: UnitUpdate) -> Unit:
    unit = get_unit_or_404(session, unit_id)
    changes = payload.model_dump(exclude_unset=True)

    # Recompute code when group_code or branch_code are updated
    new_group = changes.get("group_code", unit.group_code)
    new_branch = changes.get("branch_code", unit.branch_code)
    if ("group_code" in changes or "branch_code" in changes) and new_group and new_branch:
        changes.setdefault("code", f"{new_group}-{new_branch}")

    if "code" in changes:
        normalized_code = _normalize_code(changes["code"])
        existing_unit = get_unit_by_code(session, normalized_code)
        if existing_unit is not None and existing_unit.id != unit.id:
            raise DuplicateUnitCodeError
        changes["code"] = normalized_code

    if not changes:
        return unit

    return update_unit(session, unit, **changes)
