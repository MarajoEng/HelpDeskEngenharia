from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.enums import PriorityLevel, TicketCategory, TicketStatus, UserRole
from app.models.ticket import Ticket
from app.models.ticket_attachment import TicketAttachment
from app.models.ticket_category import TicketCategoryConfig
from app.models.ticket_priority import TicketPriorityConfig
from app.models.ticket_status import TicketStatusConfig, TicketStatusTransitionConfig
from app.models.ticket_subcategory import TicketSubcategoryConfig
from app.models.ticket_type import TicketTypeConfig
from app.models.user import User
from app.repositories.attachment_repository import count_attachments_by_ticket_and_type
from app.repositories.supplier_repository import get_supplier_by_id as get_supplier
from app.repositories.ticket_configuration_repository import (
    get_ticket_category_by_id as get_ticket_config_category_by_id,
    get_ticket_priority_by_id as get_ticket_config_priority_by_id,
    get_ticket_subcategory_by_id as get_ticket_config_subcategory_by_id,
    get_ticket_type_by_id as get_ticket_config_type_by_id,
    get_initial_ticket_status,
    get_ticket_status_by_id as get_ticket_config_status_by_id,
    get_ticket_status_by_legacy_value,
    get_ticket_status_transition,
    list_ticket_status_transitions,
    list_active_ticket_custom_fields_for_scope,
)
from app.repositories.ticket_repository import (
    count_tickets,
    create_ticket,
    create_ticket_custom_field_value,
    create_ticket_history,
    get_ticket_by_id,
    get_ticket_detail_by_id,
    get_ticket_for_update,
    list_tickets,
    update_ticket,
)
from app.repositories.unit_repository import get_unit_by_id
from app.repositories.user_repository import count_users, get_user_by_id, list_users
from app.schemas import TicketCreate, TicketListParams, TicketListResponse, TicketResponse, TicketTriageRequest
from app.schemas.attachment import TicketAttachmentResponse
from app.schemas.approval import ApprovalResponse
from app.schemas.pagination import calculate_pages
from app.schemas.ticket import (
    TicketCloseRequest,
    TicketAvailableTransitionResponse,
    TicketAvailableTransitionsResponse,
    TicketCustomFieldValueResponse,
    TicketDetailResponse,
    TicketHistoryResponse,
    TicketIndicators,
    TicketProgressUpdateRequest,
    TicketResolveRequest,
    TicketStartExecutionRequest,
    TicketSupplierSummary,
    TicketTransitionRequest,
    TicketUnitSummary,
    TicketUserSummary,
)
from app.schemas.user import UserListParams, UserListResponse, UserResponse
from app.services.exceptions import ConflictServiceError, NotFoundServiceError, ValidationServiceError

_FINAL_STATUSES = {TicketStatus.RESOLVED, TicketStatus.CLOSED, TicketStatus.CANCELED}
_TRIAGE_ALLOWED_STATUSES = {TicketStatus.OPEN, TicketStatus.WAITING_UNIT, TicketStatus.TRIAGE}
_CLOSING_ATTACHMENT_TYPE = "closing_evidence"


class TicketNotFoundError(NotFoundServiceError):
    detail = "Ticket not found."


class TicketPermissionError(ValidationServiceError):
    status_code = 403
    detail = "Insufficient permissions."


class InvalidTicketUnitError(ValidationServiceError):
    detail = "Provided unit does not exist."


class InactiveTicketUnitError(ValidationServiceError):
    detail = "Provided unit is inactive."


class AssignedUserNotFoundError(ValidationServiceError):
    detail = "Assigned user not found."


class AssignedUserInactiveError(ValidationServiceError):
    detail = "Assigned user must be active."


class AssignedUserRoleError(ValidationServiceError):
    detail = "Assigned user must have admin or engineering role."


class TicketTriageTransitionError(ConflictServiceError):
    detail = "Ticket cannot be triaged from the current status."


class TicketExecutionTransitionError(ConflictServiceError):
    detail = "Ticket cannot start execution from the current status."


class TicketProgressTransitionError(ConflictServiceError):
    detail = "Ticket must be in progress to update progress."


class TicketResolveTransitionError(ConflictServiceError):
    detail = "Ticket cannot be resolved from the current status."


class TicketCloseTransitionError(ConflictServiceError):
    detail = "Ticket cannot be closed from the current status."


class TicketConfiguredTransitionError(ConflictServiceError):
    detail = "Ticket status transition is not allowed."


class TicketTransitionCommentRequiredError(ValidationServiceError):
    detail = "Comment is required for this status transition."


class TicketTransitionAttachmentRequiredError(ValidationServiceError):
    detail = "Attachment is required for this status transition."


class MissingClosingEvidenceError(ValidationServiceError):
    detail = "At least one closing evidence attachment is required before resolving the ticket."


class SupplierNotFoundError(ValidationServiceError):
    detail = "Supplier not found."


class SupplierInactiveError(ValidationServiceError):
    detail = "Supplier must be active."


class TicketCategoryConfigNotFoundError(ValidationServiceError):
    detail = "Ticket category configuration not found."


class TicketCategoryConfigInactiveError(ValidationServiceError):
    detail = "Ticket category configuration must be active."


class TicketSubcategoryConfigNotFoundError(ValidationServiceError):
    detail = "Ticket subcategory configuration not found."


class TicketSubcategoryConfigInactiveError(ValidationServiceError):
    detail = "Ticket subcategory configuration must be active."


class TicketSubcategoryCategoryMismatchError(ValidationServiceError):
    detail = "Ticket subcategory does not belong to the selected category."


class TicketTypeConfigNotFoundError(ValidationServiceError):
    detail = "Ticket type configuration not found."


class TicketTypeConfigInactiveError(ValidationServiceError):
    detail = "Ticket type configuration must be active."


class TicketTypeCategoryMismatchError(ValidationServiceError):
    detail = "Ticket type is not allowed for the selected category."


class TicketPriorityConfigNotFoundError(ValidationServiceError):
    detail = "Ticket priority configuration not found."


class TicketPriorityConfigInactiveError(ValidationServiceError):
    detail = "Ticket priority configuration must be active."


def _custom_field_options(field) -> list[dict[str, Any]]:
    options = field.options_json or []
    return sorted(options, key=lambda option: (option.get("display_order", 0), option.get("label", "")))


def _is_empty_custom_field_value(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def _custom_field_display_value(field, value: Any) -> str | None:
    if value is None:
        return None
    if field.field_type == "boolean":
        return "Sim" if value is True else "Nao"
    if field.field_type == "select":
        for option in _custom_field_options(field):
            if option.get("value") == value:
                return str(option.get("label") or value)
    if isinstance(value, date):
        return value.isoformat()
    return str(value)


def _to_custom_field_value_response(value) -> TicketCustomFieldValueResponse | None:
    field = value.custom_field
    if field is None:
        return None

    typed_value: Any = None
    if field.field_type in {"text", "textarea", "select"}:
        typed_value = value.value_text
    elif field.field_type == "number":
        typed_value = value.value_number
    elif field.field_type == "boolean":
        typed_value = value.value_boolean
    elif field.field_type == "date":
        typed_value = value.value_date
    else:
        typed_value = value.value_json

    return TicketCustomFieldValueResponse(
        id=value.id,
        custom_field_id=field.id,
        name=field.name,
        label=field.label,
        field_type=field.field_type,
        value=typed_value,
        display_value=_custom_field_display_value(field, typed_value),
        is_active=field.is_active,
    )


def _normalize_custom_field_submissions(custom_fields: Any) -> dict[int, Any]:
    if custom_fields is None:
        return {}

    normalized: dict[int, Any] = {}
    if isinstance(custom_fields, dict):
        for raw_field_id, value in custom_fields.items():
            try:
                field_id = int(raw_field_id)
            except (TypeError, ValueError) as exc:
                raise ValidationServiceError("Custom field id must be numeric.") from exc
            normalized[field_id] = value
        return normalized

    for item in custom_fields:
        field_id = item.field_id if hasattr(item, "field_id") else item.get("field_id")
        value = item.value if hasattr(item, "value") else item.get("value")
        normalized[int(field_id)] = value
    return normalized


def _validate_custom_field_value(field, value: Any) -> dict[str, Any] | None:
    if _is_empty_custom_field_value(value):
        if field.is_required:
            raise ValidationServiceError(f"Custom field '{field.label}' is required.")
        return None

    if field.field_type in {"text", "textarea"}:
        return {"value_text": str(value).strip()}

    if field.field_type == "select":
        selected_value = str(value).strip()
        active_values = {
            str(option.get("value"))
            for option in _custom_field_options(field)
            if option.get("is_active", True) is True
        }
        if selected_value not in active_values:
            raise ValidationServiceError(f"Custom field '{field.label}' has an invalid option.")
        return {"value_text": selected_value}

    if field.field_type == "number":
        try:
            return {"value_number": Decimal(str(value))}
        except (InvalidOperation, ValueError) as exc:
            raise ValidationServiceError(f"Custom field '{field.label}' must be a valid number.") from exc

    if field.field_type == "boolean":
        if not isinstance(value, bool):
            raise ValidationServiceError(f"Custom field '{field.label}' must be true or false.")
        return {"value_boolean": value}

    if field.field_type == "date":
        if isinstance(value, date) and not isinstance(value, datetime):
            parsed_date = value
        elif isinstance(value, str):
            try:
                parsed_date = date.fromisoformat(value)
            except ValueError as exc:
                raise ValidationServiceError(f"Custom field '{field.label}' must be a valid date.") from exc
        else:
            raise ValidationServiceError(f"Custom field '{field.label}' must be a valid date.")
        return {"value_date": parsed_date}

    return {"value_json": value}


def _persist_ticket_custom_fields(
    session: Session,
    *,
    ticket_id: int,
    category_id: int | None,
    subcategory_id: int | None,
    custom_fields: Any,
) -> None:
    if category_id is None:
        if custom_fields:
            raise ValidationServiceError("Custom fields require a configured category.")
        return

    active_fields = list_active_ticket_custom_fields_for_scope(
        session,
        category_id=category_id,
        subcategory_id=subcategory_id,
    )
    active_by_id = {field.id: field for field in active_fields}
    submitted_values = _normalize_custom_field_submissions(custom_fields)

    unknown_field_ids = set(submitted_values) - set(active_by_id)
    if unknown_field_ids:
        raise ValidationServiceError("Custom field does not belong to the selected category or subcategory.")

    for field in active_fields:
        value_payload = _validate_custom_field_value(field, submitted_values.get(field.id))
        if value_payload is None:
            continue
        create_ticket_custom_field_value(
            session,
            ticket_id=ticket_id,
            custom_field_id=field.id,
            **value_payload,
        )


def _to_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def _calculate_estimated_loss_total(
    fuel_nozzles_stopped: int | None,
    estimated_daily_loss: Decimal | None,
) -> Decimal | None:
    if fuel_nozzles_stopped is None or estimated_daily_loss is None or fuel_nozzles_stopped <= 0:
        return None
    return estimated_daily_loss * Decimal(fuel_nozzles_stopped)


def _hours_between(start: datetime | None, end: datetime | None) -> float | None:
    if start is None or end is None:
        return None
    return round((_to_utc(end) - _to_utc(start)).total_seconds() / 3600, 2)


def _build_ticket_number(ticket_id: int, opened_at: datetime) -> str:
    return f"ENG-{opened_at.strftime('%Y%m%d')}-{ticket_id:06d}"


def _build_attachment_download_url(attachment_id: int) -> str:
    return f"/attachments/{attachment_id}/download"


def _to_attachment_response(attachment: TicketAttachment) -> TicketAttachmentResponse:
    return TicketAttachmentResponse(
        id=attachment.id,
        ticket_id=attachment.ticket_id,
        uploaded_by_user_id=attachment.uploaded_by_user_id,
        uploaded_by_user_name=attachment.uploaded_by_user.name if attachment.uploaded_by_user else None,
        file_url=_build_attachment_download_url(attachment.id),
        file_type=attachment.file_type,
        attachment_type=attachment.attachment_type,
        created_at=attachment.created_at,
    )


def _fallback_category_name(ticket: Ticket) -> str:
    if ticket.configured_category is not None:
        return ticket.configured_category.name
    return ticket.category.value.replace("_", " ").title()


def _fallback_priority_name(ticket: Ticket) -> str:
    if ticket.configured_priority is not None:
        return ticket.configured_priority.name

    mapping = {
        PriorityLevel.LOW: "Baixa",
        PriorityLevel.MEDIUM: "Media",
        PriorityLevel.HIGH: "Alta",
        PriorityLevel.CRITICAL: "Critica",
    }
    return mapping[ticket.priority]


def _legacy_status_from_config(status: TicketStatusConfig | None, fallback: TicketStatus) -> TicketStatus:
    if status is None or not status.legacy_value:
        return fallback
    try:
        return TicketStatus(status.legacy_value)
    except ValueError:
        return fallback


def _fallback_status_name(ticket: Ticket) -> str:
    if ticket.configured_status is not None:
        return ticket.configured_status.name
    mapping = {
        TicketStatus.OPEN: "Aberto",
        TicketStatus.TRIAGE: "Triagem",
        TicketStatus.WAITING_APPROVAL: "Aguardando aprovacao",
        TicketStatus.APPROVED: "Aprovado",
        TicketStatus.REJECTED: "Rejeitado",
        TicketStatus.IN_PROGRESS: "Em atendimento",
        TicketStatus.WAITING_SUPPLIER: "Aguardando fornecedor",
        TicketStatus.WAITING_UNIT: "Aguardando unidade",
        TicketStatus.RESOLVED: "Resolvido",
        TicketStatus.CLOSED: "Fechado",
        TicketStatus.CANCELED: "Cancelado",
    }
    return mapping.get(ticket.status, ticket.status.value)


def _fallback_status_color(ticket: Ticket) -> str:
    if ticket.configured_status is not None:
        return ticket.configured_status.color
    mapping = {
        TicketStatus.OPEN: "#2563eb",
        TicketStatus.TRIAGE: "#7c3aed",
        TicketStatus.WAITING_APPROVAL: "#d97706",
        TicketStatus.APPROVED: "#059669",
        TicketStatus.REJECTED: "#dc2626",
        TicketStatus.IN_PROGRESS: "#0891b2",
        TicketStatus.WAITING_SUPPLIER: "#9333ea",
        TicketStatus.WAITING_UNIT: "#ca8a04",
        TicketStatus.RESOLVED: "#16a34a",
        TicketStatus.CLOSED: "#475569",
        TicketStatus.CANCELED: "#991b1b",
    }
    return mapping.get(ticket.status, "#475569")


def _resolve_current_configured_status(session: Session, ticket: Ticket) -> TicketStatusConfig | None:
    if ticket.status_id is not None:
        status = ticket.configured_status or get_ticket_config_status_by_id(session, ticket.status_id)
        if status is not None:
            return status
    return get_ticket_status_by_legacy_value(session, ticket.status.value)


def _resolve_configured_status_by_legacy(session: Session, status: TicketStatus) -> TicketStatusConfig | None:
    return get_ticket_status_by_legacy_value(session, status.value)


def _count_ticket_attachments(session: Session, ticket_id: int) -> int:
    return int(
        session.scalar(
            select(func.count()).select_from(TicketAttachment).where(TicketAttachment.ticket_id == ticket_id)
        )
        or 0
    )


def _role_is_allowed(transition: TicketStatusTransitionConfig, current_user: User) -> bool:
    allowed_roles = transition.allowed_roles_json or []
    if not allowed_roles:
        return True
    return current_user.role.value in {role.strip().lower() for role in allowed_roles}


def _validate_configured_transition(
    session: Session,
    *,
    ticket: Ticket,
    to_status: TicketStatus,
    current_user: User,
    comment: str | None,
) -> TicketStatusConfig | None:
    from_config = _resolve_current_configured_status(session, ticket)
    to_config = _resolve_configured_status_by_legacy(session, to_status)
    if from_config is None or to_config is None:
        return to_config

    transition = get_ticket_status_transition(
        session,
        from_status_id=from_config.id,
        to_status_id=to_config.id,
    )
    if transition is None or not transition.is_active:
        raise TicketConfiguredTransitionError
    if not _role_is_allowed(transition, current_user):
        raise TicketPermissionError
    if transition.requires_comment and not (comment or "").strip():
        raise TicketTransitionCommentRequiredError
    if transition.requires_attachment and _count_ticket_attachments(session, ticket.id) == 0:
        raise TicketTransitionAttachmentRequiredError
    return to_config


def _status_changes(
    session: Session,
    *,
    to_status: TicketStatus,
    fallback_status: TicketStatus | None = None,
) -> dict[str, object]:
    configured_status = _resolve_configured_status_by_legacy(session, to_status)
    legacy_status = _legacy_status_from_config(configured_status, fallback_status or to_status)
    return {
        "status": legacy_status,
        "status_id": configured_status.id if configured_status else None,
    }


def _set_legacy_status_id(session: Session, ticket: Ticket, status: TicketStatus) -> None:
    configured_status = _resolve_configured_status_by_legacy(session, status)
    if configured_status is not None:
        ticket.status_id = configured_status.id


def _resolve_ticket_category_config(
    session: Session,
    category_id: int | None,
) -> TicketCategoryConfig | None:
    if category_id is None:
        return None

    category = get_ticket_config_category_by_id(session, category_id)
    if category is None:
        raise TicketCategoryConfigNotFoundError
    if not category.is_active:
        raise TicketCategoryConfigInactiveError
    return category


def _resolve_ticket_subcategory_config(
    session: Session,
    subcategory_id: int | None,
) -> TicketSubcategoryConfig | None:
    if subcategory_id is None:
        return None

    subcategory = get_ticket_config_subcategory_by_id(session, subcategory_id)
    if subcategory is None:
        raise TicketSubcategoryConfigNotFoundError
    if not subcategory.is_active:
        raise TicketSubcategoryConfigInactiveError
    return subcategory


def _resolve_ticket_type_config(
    session: Session,
    type_id: int | None,
) -> TicketTypeConfig | None:
    if type_id is None:
        return None

    ticket_type = get_ticket_config_type_by_id(session, type_id)
    if ticket_type is None:
        raise TicketTypeConfigNotFoundError
    if not ticket_type.is_active:
        raise TicketTypeConfigInactiveError
    return ticket_type


def _resolve_ticket_priority_config(
    session: Session,
    priority_id: int | None,
) -> TicketPriorityConfig | None:
    if priority_id is None:
        return None

    priority = get_ticket_config_priority_by_id(session, priority_id)
    if priority is None:
        raise TicketPriorityConfigNotFoundError
    if not priority.is_active:
        raise TicketPriorityConfigInactiveError
    return priority


def _legacy_category_from_config(category: TicketCategoryConfig) -> TicketCategory:
    if category.legacy_value:
        try:
            return TicketCategory(category.legacy_value)
        except ValueError:
            pass
    return TicketCategory.OTHER


def _legacy_priority_from_config(priority: TicketPriorityConfig) -> PriorityLevel:
    if priority.legacy_value:
        try:
            return PriorityLevel(priority.legacy_value)
        except ValueError:
            pass

    if priority.weight >= 40:
        return PriorityLevel.CRITICAL
    if priority.weight >= 30:
        return PriorityLevel.HIGH
    if priority.weight >= 20:
        return PriorityLevel.MEDIUM
    return PriorityLevel.LOW


def _resolve_ticket_configuration_payload(
    session: Session,
    payload: TicketCreate,
) -> tuple[
    TicketCategoryConfig | None,
    TicketSubcategoryConfig | None,
    TicketTypeConfig | None,
    TicketPriorityConfig | None,
    TicketCategory,
    PriorityLevel,
]:
    subcategory = _resolve_ticket_subcategory_config(session, payload.subcategory_id)
    category = _resolve_ticket_category_config(session, payload.category_id)
    if category is None and subcategory is not None:
        category = _resolve_ticket_category_config(session, subcategory.category_id)

    ticket_type = _resolve_ticket_type_config(session, payload.type_id)
    priority = _resolve_ticket_priority_config(session, payload.priority_id)

    if subcategory is not None and category is not None and subcategory.category_id != category.id:
        raise TicketSubcategoryCategoryMismatchError

    if category is not None and ticket_type is not None:
        allowed_type_ids = {link.type_id for link in category.category_types if link.ticket_type and link.ticket_type.is_active}
        if ticket_type.id not in allowed_type_ids:
            raise TicketTypeCategoryMismatchError

    legacy_category = _legacy_category_from_config(category) if category is not None else payload.category
    legacy_priority = _legacy_priority_from_config(priority) if priority is not None else payload.priority

    if legacy_category is None:
        raise TicketCategoryConfigNotFoundError
    if legacy_priority is None:
        raise TicketPriorityConfigNotFoundError

    return category, subcategory, ticket_type, priority, legacy_category, legacy_priority


def _to_ticket_response(ticket: Ticket) -> TicketResponse:
    has_closing_evidence = any(
        attachment.attachment_type == _CLOSING_ATTACHMENT_TYPE for attachment in ticket.attachments
    )
    return TicketResponse.model_validate(
        {
            "id": ticket.id,
            "ticket_number": ticket.ticket_number,
            "unit_id": ticket.unit_id,
            "opened_by_user_id": ticket.opened_by_user_id,
            "assigned_to_user_id": ticket.assigned_to_user_id,
            "category_id": ticket.category_id,
            "subcategory_id": ticket.subcategory_id,
            "type_id": ticket.type_id,
            "priority_id": ticket.priority_id,
            "category": ticket.category,
            "category_name": _fallback_category_name(ticket),
            "subcategory_name": ticket.configured_subcategory.name if ticket.configured_subcategory else None,
            "type_name": ticket.configured_type.name if ticket.configured_type else None,
            "problem_type": ticket.problem_type,
            "title": ticket.title,
            "description": ticket.description,
            "priority": ticket.priority,
            "priority_name": _fallback_priority_name(ticket),
            "priority_color": ticket.configured_priority.color if ticket.configured_priority else None,
            "priority_weight": ticket.configured_priority.weight if ticket.configured_priority else None,
            "severity": ticket.severity,
            "status": ticket.status,
            "status_id": ticket.status_id,
            "status_name": _fallback_status_name(ticket),
            "status_color": _fallback_status_color(ticket),
            "operational_impact": ticket.operational_impact,
            "fuel_nozzles_stopped": ticket.fuel_nozzles_stopped,
            "estimated_daily_loss": ticket.estimated_daily_loss,
            "estimated_loss_total": _calculate_estimated_loss_total(
                ticket.fuel_nozzles_stopped,
                ticket.estimated_daily_loss,
            ),
            "estimated_cost": ticket.estimated_cost,
            "approved_cost": ticket.approved_cost,
            "final_cost": ticket.final_cost,
            "requires_approval": ticket.requires_approval,
            "opened_at": ticket.opened_at,
            "triaged_at": ticket.triaged_at,
            "approved_at": ticket.approved_at,
            "started_at": ticket.started_at,
            "resolved_at": ticket.resolved_at,
            "closed_at": ticket.closed_at,
            "sla_due_at": ticket.sla_due_at,
            "expected_resolution_at": ticket.expected_resolution_at,
            "supplier_id": ticket.supplier_id,
            "created_at": ticket.created_at,
            "updated_at": ticket.updated_at,
            "unit_name": ticket.unit.name if ticket.unit else None,
            "unit_code": ticket.unit.code if ticket.unit else None,
            "opened_by_user_name": ticket.opened_by_user.name if ticket.opened_by_user else None,
            "assigned_to_user_name": ticket.assigned_to_user.name if ticket.assigned_to_user else None,
            "supplier_name": ticket.supplier.name if ticket.supplier else None,
            "has_closing_evidence": has_closing_evidence,
        }
    )


def _to_approval_response(approval) -> ApprovalResponse:
    return ApprovalResponse(
        id=approval.id,
        ticket_id=approval.ticket_id,
        requested_by_user_id=approval.requested_by_user_id,
        requested_by_user_name=approval.requested_by_user.name if approval.requested_by_user else None,
        approved_by_user_id=approval.approved_by_user_id,
        approved_by_user_name=approval.approved_by_user.name if approval.approved_by_user else None,
        approval_level_id=approval.approval_level_id,
        approval_level_name=approval.approval_level.name if approval.approval_level else None,
        approval_allowed_roles=list(approval.approval_level.allowed_roles) if approval.approval_level else [],
        status=approval.status,
        amount_requested=approval.amount_requested,
        amount_approved=approval.amount_approved,
        justification=approval.justification,
        approved_at=approval.approved_at,
        created_at=approval.created_at,
    )


def _calculate_indicators(ticket: Ticket) -> TicketIndicators:
    now = datetime.now(UTC)
    opened_at = _to_utc(ticket.opened_at)
    end_time = _to_utc(ticket.closed_at) if ticket.closed_at else now
    elapsed_hours = round((end_time - opened_at).total_seconds() / 3600, 2)

    is_final = ticket.status in _FINAL_STATUSES
    sla_due = _to_utc(ticket.sla_due_at) if ticket.sla_due_at else None

    if is_final:
        sla_status: str = "closed"
        is_late = False
    elif sla_due is None:
        sla_status = "no_sla"
        is_late = False
    elif sla_due >= now:
        sla_status = "on_track"
        is_late = False
    else:
        sla_status = "late"
        is_late = True

    elapsed_execution_hours: float | None = None
    execution_is_late = False
    if ticket.started_at and ticket.status == TicketStatus.IN_PROGRESS:
        started_utc = _to_utc(ticket.started_at)
        elapsed_execution_hours = round((now - started_utc).total_seconds() / 3600, 2)
        if ticket.expected_resolution_at:
            expected_utc = _to_utc(ticket.expected_resolution_at)
            execution_is_late = expected_utc < now

    has_closing_evidence = any(
        attachment.attachment_type == _CLOSING_ATTACHMENT_TYPE for attachment in ticket.attachments
    )
    total_hours_end = ticket.closed_at or ticket.resolved_at or now

    return TicketIndicators(
        estimated_loss_total=_calculate_estimated_loss_total(
            ticket.fuel_nozzles_stopped,
            ticket.estimated_daily_loss,
        ),
        elapsed_hours=elapsed_hours,
        is_late=is_late,
        sla_status=sla_status,
        elapsed_execution_hours=elapsed_execution_hours,
        execution_is_late=execution_is_late,
        total_hours=_hours_between(ticket.opened_at, total_hours_end),
        resolution_hours=_hours_between(ticket.opened_at, ticket.resolved_at),
        closure_hours=_hours_between(ticket.resolved_at, ticket.closed_at),
        final_cost=ticket.final_cost,
        has_closing_evidence=has_closing_evidence,
    )


def build_ticket_detail_response(ticket: Ticket) -> TicketDetailResponse:
    unit_summary = (
        TicketUnitSummary(
            id=ticket.unit.id,
            code=ticket.unit.code,
            name=ticket.unit.name,
            city=ticket.unit.city,
            state=ticket.unit.state,
        )
        if ticket.unit
        else None
    )

    opened_by_summary = (
        TicketUserSummary(id=ticket.opened_by_user.id, name=ticket.opened_by_user.name)
        if ticket.opened_by_user
        else None
    )

    assigned_to_summary = (
        TicketUserSummary(id=ticket.assigned_to_user.id, name=ticket.assigned_to_user.name)
        if ticket.assigned_to_user
        else None
    )

    supplier_summary = (
        TicketSupplierSummary(
            id=ticket.supplier.id,
            name=ticket.supplier.name,
            document=ticket.supplier.document,
            phone=ticket.supplier.phone,
            email=ticket.supplier.email,
            specialty=ticket.supplier.specialty,
            is_active=ticket.supplier.is_active,
        )
        if ticket.supplier
        else None
    )

    history = sorted(ticket.history_entries, key=lambda h: h.created_at)
    history_responses = [
        TicketHistoryResponse(
            id=h.id,
            user_id=h.user_id,
            user_name=h.user.name if h.user else None,
            old_status=h.old_status,
            new_status=h.new_status,
            comment=h.comment,
            created_at=h.created_at,
        )
        for h in history
    ]
    approvals = sorted(ticket.approvals, key=lambda approval: approval.created_at)
    approval_responses = [_to_approval_response(approval) for approval in approvals]
    attachments = sorted(ticket.attachments, key=lambda attachment: attachment.created_at, reverse=True)
    attachment_responses = [_to_attachment_response(attachment) for attachment in attachments]
    custom_field_values = sorted(
        ticket.custom_field_values,
        key=lambda item: (
            item.custom_field.display_order if item.custom_field else 0,
            item.custom_field.label if item.custom_field else "",
            item.id,
        ),
    )
    custom_field_responses = [
        response
        for response in (_to_custom_field_value_response(value) for value in custom_field_values)
        if response is not None
    ]

    return TicketDetailResponse(
        id=ticket.id,
        ticket_number=ticket.ticket_number,
        unit_id=ticket.unit_id,
        opened_by_user_id=ticket.opened_by_user_id,
        assigned_to_user_id=ticket.assigned_to_user_id,
        category_id=ticket.category_id,
        subcategory_id=ticket.subcategory_id,
        type_id=ticket.type_id,
        priority_id=ticket.priority_id,
        category=ticket.category,
        category_name=_fallback_category_name(ticket),
        subcategory_name=ticket.configured_subcategory.name if ticket.configured_subcategory else None,
        type_name=ticket.configured_type.name if ticket.configured_type else None,
        problem_type=ticket.problem_type,
        title=ticket.title,
        description=ticket.description,
        priority=ticket.priority,
        priority_name=_fallback_priority_name(ticket),
        priority_color=ticket.configured_priority.color if ticket.configured_priority else None,
        priority_weight=ticket.configured_priority.weight if ticket.configured_priority else None,
        severity=ticket.severity,
        status=ticket.status,
        status_id=ticket.status_id,
        status_name=_fallback_status_name(ticket),
        status_color=_fallback_status_color(ticket),
        operational_impact=ticket.operational_impact,
        fuel_nozzles_stopped=ticket.fuel_nozzles_stopped,
        estimated_daily_loss=ticket.estimated_daily_loss,
        estimated_cost=ticket.estimated_cost,
        approved_cost=ticket.approved_cost,
        final_cost=ticket.final_cost,
        requires_approval=ticket.requires_approval,
        opened_at=ticket.opened_at,
        triaged_at=ticket.triaged_at,
        approved_at=ticket.approved_at,
        started_at=ticket.started_at,
        resolved_at=ticket.resolved_at,
        closed_at=ticket.closed_at,
        sla_due_at=ticket.sla_due_at,
        expected_resolution_at=ticket.expected_resolution_at,
        supplier_id=ticket.supplier_id,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
        unit=unit_summary,
        opened_by=opened_by_summary,
        assigned_to=assigned_to_summary,
        supplier=supplier_summary,
        history=history_responses,
        approvals=approval_responses,
        attachments=attachment_responses,
        indicators=_calculate_indicators(ticket),
        custom_fields=custom_field_responses,
    )


def _ensure_unit_available(session: Session, unit_id: int):
    unit = get_unit_by_id(session, unit_id)
    if unit is None:
        raise InvalidTicketUnitError
    if not unit.is_active:
        raise InactiveTicketUnitError
    return unit


def _enforce_create_permission(current_user: User, unit_id: int) -> None:
    if current_user.role == UserRole.SUPPLIER:
        raise TicketPermissionError
    if current_user.role == UserRole.MANAGER and current_user.unit_id != unit_id:
        raise TicketPermissionError
    if current_user.role not in {
        UserRole.ADMIN,
        UserRole.MANAGER,
        UserRole.ENGINEERING,
        UserRole.DIRECTOR,
    }:
        raise TicketPermissionError


def _restrict_unit_scope(current_user: User, params: TicketListParams) -> TicketListParams:
    if current_user.role == UserRole.MANAGER:
        return params.model_copy(update={"unit_id": current_user.unit_id})
    return params


def _can_view_ticket(current_user: User, ticket: Ticket) -> bool:
    if current_user.role in {UserRole.ADMIN, UserRole.ENGINEERING, UserRole.DIRECTOR}:
        return True
    if current_user.role == UserRole.MANAGER and current_user.unit_id == ticket.unit_id:
        return True
    return False


def _ensure_ticket_can_be_viewed(current_user: User, ticket: Ticket) -> None:
    if current_user.role == UserRole.SUPPLIER:
        raise TicketPermissionError
    if not _can_view_ticket(current_user, ticket):
        raise TicketPermissionError


def create_ticket_record(session: Session, payload: TicketCreate, current_user: User) -> TicketResponse:
    _enforce_create_permission(current_user, payload.unit_id)
    _ensure_unit_available(session, payload.unit_id)
    category_config, subcategory_config, type_config, priority_config, legacy_category, legacy_priority = (
        _resolve_ticket_configuration_payload(session, payload)
    )

    opened_at = datetime.now(UTC)
    initial_status = get_initial_ticket_status(session)
    legacy_initial_status = _legacy_status_from_config(initial_status, TicketStatus.OPEN)
    ticket = create_ticket(
        session,
        ticket_number=f"PENDING-{opened_at.strftime('%Y%m%d%H%M%S%f')}",
        unit_id=payload.unit_id,
        opened_by_user_id=current_user.id,
        assigned_to_user_id=None,
        category_id=category_config.id if category_config else None,
        subcategory_id=subcategory_config.id if subcategory_config else None,
        type_id=type_config.id if type_config else None,
        priority_id=priority_config.id if priority_config else None,
        category=legacy_category,
        problem_type=payload.problem_type,
        title=payload.title,
        description=payload.description,
        priority=legacy_priority,
        severity=payload.severity,
        status=legacy_initial_status,
        status_id=initial_status.id if initial_status else None,
        operational_impact=payload.operational_impact,
        fuel_nozzles_stopped=payload.fuel_nozzles_stopped,
        estimated_daily_loss=payload.estimated_daily_loss,
        estimated_cost=payload.estimated_cost,
        approved_cost=None,
        final_cost=None,
        requires_approval=payload.requires_approval,
        opened_at=opened_at,
        triaged_at=None,
        approved_at=None,
        started_at=None,
        resolved_at=None,
        closed_at=None,
        sla_due_at=None,
        expected_resolution_at=None,
        supplier_id=None,
    )
    ticket.ticket_number = _build_ticket_number(ticket.id, opened_at)
    _persist_ticket_custom_fields(
        session,
        ticket_id=ticket.id,
        category_id=ticket.category_id,
        subcategory_id=ticket.subcategory_id,
        custom_fields=payload.custom_fields,
    )
    create_ticket_history(
        session,
        ticket_id=ticket.id,
        user_id=current_user.id,
        old_status=None,
        new_status=legacy_initial_status,
        comment="Chamado aberto",
    )
    session.commit()

    persisted_ticket = get_ticket_by_id(session, ticket.id)
    if persisted_ticket is None:
        raise TicketNotFoundError
    return _to_ticket_response(persisted_ticket)


def get_ticket_or_404(session: Session, ticket_id: int) -> Ticket:
    ticket = get_ticket_by_id(session, ticket_id)
    if ticket is None:
        raise TicketNotFoundError
    return ticket


def list_ticket_records(session: Session, params: TicketListParams, current_user: User) -> TicketListResponse:
    if current_user.role == UserRole.SUPPLIER:
        raise TicketPermissionError

    scoped_params = _restrict_unit_scope(current_user, params)
    category_legacy_value: str | None = None
    priority_legacy_value: str | None = None
    if scoped_params.category_id is not None:
        category_config = get_ticket_config_category_by_id(session, scoped_params.category_id)
        category_legacy_value = category_config.legacy_value if category_config else None
    if scoped_params.priority_id is not None:
        priority_config = get_ticket_config_priority_by_id(session, scoped_params.priority_id)
        priority_legacy_value = priority_config.legacy_value if priority_config else None

    total = count_tickets(
        session,
        unit_id=scoped_params.unit_id,
        group_code=scoped_params.group_code,
        branch_code=scoped_params.branch_code,
        category_id=scoped_params.category_id,
        subcategory_id=scoped_params.subcategory_id,
        type_id=scoped_params.type_id,
        priority_id=scoped_params.priority_id,
        status_id=scoped_params.status_id,
        status=scoped_params.status,
        category=scoped_params.category,
        category_legacy_value=category_legacy_value,
        priority=scoped_params.priority,
        priority_legacy_value=priority_legacy_value,
        severity=scoped_params.severity,
        requires_approval=scoped_params.requires_approval,
        opened_from=scoped_params.opened_from,
        opened_to=scoped_params.opened_to,
        search=scoped_params.search,
        only_late=scoped_params.only_late,
        has_fuel_nozzles_stopped=scoped_params.has_fuel_nozzles_stopped,
        min_estimated_cost=scoped_params.min_estimated_cost,
        max_estimated_cost=scoped_params.max_estimated_cost,
        queue=scoped_params.queue,
    )
    items = list_tickets(
        session,
        page=scoped_params.page,
        page_size=scoped_params.page_size,
        unit_id=scoped_params.unit_id,
        group_code=scoped_params.group_code,
        branch_code=scoped_params.branch_code,
        category_id=scoped_params.category_id,
        subcategory_id=scoped_params.subcategory_id,
        type_id=scoped_params.type_id,
        priority_id=scoped_params.priority_id,
        status_id=scoped_params.status_id,
        status=scoped_params.status,
        category=scoped_params.category,
        category_legacy_value=category_legacy_value,
        priority=scoped_params.priority,
        priority_legacy_value=priority_legacy_value,
        severity=scoped_params.severity,
        requires_approval=scoped_params.requires_approval,
        opened_from=scoped_params.opened_from,
        opened_to=scoped_params.opened_to,
        search=scoped_params.search,
        only_late=scoped_params.only_late,
        has_fuel_nozzles_stopped=scoped_params.has_fuel_nozzles_stopped,
        min_estimated_cost=scoped_params.min_estimated_cost,
        max_estimated_cost=scoped_params.max_estimated_cost,
        queue=scoped_params.queue,
    )
    return TicketListResponse(
        items=[_to_ticket_response(ticket) for ticket in items],
        total=total,
        page=scoped_params.page,
        page_size=scoped_params.page_size,
        pages=calculate_pages(total, scoped_params.page_size),
    )


def get_ticket_detail(session: Session, ticket_id: int, current_user: User) -> TicketDetailResponse:
    ticket = get_ticket_detail_by_id(session, ticket_id)
    if ticket is None:
        raise TicketNotFoundError
    _ensure_ticket_can_be_viewed(current_user, ticket)
    return build_ticket_detail_response(ticket)


def get_available_ticket_transitions(
    session: Session,
    ticket_id: int,
    current_user: User,
) -> TicketAvailableTransitionsResponse:
    ticket = get_ticket_detail_by_id(session, ticket_id)
    if ticket is None:
        raise TicketNotFoundError
    _ensure_ticket_can_be_viewed(current_user, ticket)

    current_status = _resolve_current_configured_status(session, ticket)
    if current_status is None:
        return TicketAvailableTransitionsResponse(
            ticket_id=ticket.id,
            current_status_id=None,
            current_status_name=_fallback_status_name(ticket),
            transitions=[],
        )

    transitions = [
        transition
        for transition in list_ticket_status_transitions(
            session,
            page=1,
            page_size=100,
            from_status_id=current_status.id,
            is_active=True,
        )
        if transition.to_status is not None and transition.to_status.is_active and _role_is_allowed(transition, current_user)
    ]
    return TicketAvailableTransitionsResponse(
        ticket_id=ticket.id,
        current_status_id=current_status.id,
        current_status_name=current_status.name,
        transitions=[
            TicketAvailableTransitionResponse(
                transition_id=transition.id,
                from_status_id=transition.from_status_id,
                to_status_id=transition.to_status_id,
                to_status_name=transition.to_status.name,
                to_status_color=transition.to_status.color,
                requires_comment=transition.requires_comment,
                requires_attachment=transition.requires_attachment,
            )
            for transition in transitions
        ],
    )


def transition_ticket_status(
    session: Session,
    ticket_id: int,
    payload: TicketTransitionRequest,
    current_user: User,
) -> TicketDetailResponse:
    _enforce_execution_permission(current_user)

    ticket = get_ticket_for_update(session, ticket_id)
    if ticket is None:
        raise TicketNotFoundError
    to_status_config = get_ticket_config_status_by_id(session, payload.to_status_id)
    if to_status_config is None or not to_status_config.is_active:
        raise TicketConfiguredTransitionError

    to_legacy_status = _legacy_status_from_config(to_status_config, ticket.status)
    if (
        to_legacy_status == TicketStatus.RESOLVED
        and count_attachments_by_ticket_and_type(
            session,
            ticket_id=ticket.id,
            attachment_type=_CLOSING_ATTACHMENT_TYPE,
        )
        == 0
    ):
        raise MissingClosingEvidenceError
    validated_status = _validate_configured_transition(
        session,
        ticket=ticket,
        to_status=to_legacy_status,
        current_user=current_user,
        comment=payload.comment,
    )
    if validated_status is None or validated_status.id != to_status_config.id:
        raise TicketConfiguredTransitionError

    old_status = ticket.status
    changes = {
        "status": to_legacy_status,
        "status_id": to_status_config.id,
    }
    now = datetime.now(UTC)
    if to_legacy_status == TicketStatus.TRIAGE and ticket.triaged_at is None:
        changes["triaged_at"] = now
    if to_legacy_status == TicketStatus.IN_PROGRESS and ticket.started_at is None:
        changes["started_at"] = now
    if to_legacy_status == TicketStatus.RESOLVED and ticket.resolved_at is None:
        changes["resolved_at"] = now
    if to_legacy_status == TicketStatus.CLOSED and ticket.closed_at is None:
        changes["closed_at"] = now

    update_ticket(session, ticket, **changes)
    create_ticket_history(
        session,
        ticket_id=ticket.id,
        user_id=current_user.id,
        old_status=old_status,
        new_status=to_legacy_status,
        comment=payload.comment,
    )
    session.commit()

    persisted_ticket = get_ticket_detail_by_id(session, ticket.id)
    if persisted_ticket is None:
        raise TicketNotFoundError
    return build_ticket_detail_response(persisted_ticket)


def _enforce_triage_permission(current_user: User) -> None:
    if current_user.role not in {UserRole.ADMIN, UserRole.ENGINEERING}:
        raise TicketPermissionError


def _enforce_execution_permission(current_user: User) -> None:
    if current_user.role not in {UserRole.ADMIN, UserRole.ENGINEERING}:
        raise TicketPermissionError


def _validate_assigned_user(session: Session, user_id: int | None) -> User | None:
    if user_id is None:
        return None

    user = get_user_by_id(session, user_id)
    if user is None:
        raise AssignedUserNotFoundError
    if not user.is_active:
        raise AssignedUserInactiveError
    if user.role not in {UserRole.ADMIN, UserRole.ENGINEERING}:
        raise AssignedUserRoleError
    return user


def _validate_supplier(session: Session, supplier_id: int | None) -> None:
    if supplier_id is None:
        return
    supplier = get_supplier(session, supplier_id)
    if supplier is None:
        raise SupplierNotFoundError
    if not supplier.is_active:
        raise SupplierInactiveError


def triage_ticket(
    session: Session,
    ticket_id: int,
    payload: TicketTriageRequest,
    current_user: User,
) -> TicketDetailResponse:
    _enforce_triage_permission(current_user)

    ticket = get_ticket_for_update(session, ticket_id)
    if ticket is None:
        raise TicketNotFoundError

    if ticket.status not in _TRIAGE_ALLOWED_STATUSES:
        raise TicketTriageTransitionError

    payload_fields = payload.model_fields_set
    changes: dict[str, object] = {}

    if "assigned_to_user_id" in payload_fields:
        _validate_assigned_user(session, payload.assigned_to_user_id)
        changes["assigned_to_user_id"] = payload.assigned_to_user_id

    if "priority" in payload_fields and payload.priority is not None:
        changes["priority"] = payload.priority

    if "severity" in payload_fields and payload.severity is not None:
        changes["severity"] = payload.severity

    if "requires_approval" in payload_fields and payload.requires_approval is not None:
        changes["requires_approval"] = payload.requires_approval

    if "sla_due_at" in payload_fields:
        changes["sla_due_at"] = payload.sla_due_at

    old_status = ticket.status
    if ticket.status in {TicketStatus.OPEN, TicketStatus.WAITING_UNIT}:
        _validate_configured_transition(
            session,
            ticket=ticket,
            to_status=TicketStatus.TRIAGE,
            current_user=current_user,
            comment=payload.technical_comment,
        )
        changes.update(_status_changes(session, to_status=TicketStatus.TRIAGE))
        if ticket.triaged_at is None:
            changes["triaged_at"] = datetime.now(UTC)

    if changes:
        update_ticket(session, ticket, **changes)

    create_ticket_history(
        session,
        ticket_id=ticket.id,
        user_id=current_user.id,
        old_status=old_status,
        new_status=TicketStatus.TRIAGE,
        comment=payload.technical_comment,
    )
    session.commit()

    persisted_ticket = get_ticket_detail_by_id(session, ticket.id)
    if persisted_ticket is None:
        raise TicketNotFoundError
    return build_ticket_detail_response(persisted_ticket)


def start_ticket_execution(
    session: Session,
    ticket_id: int,
    payload: TicketStartExecutionRequest,
    current_user: User,
) -> TicketDetailResponse:
    _enforce_execution_permission(current_user)

    ticket = get_ticket_for_update(session, ticket_id)
    if ticket is None:
        raise TicketNotFoundError

    valid_from_no_approval = {TicketStatus.TRIAGE}
    valid_from_with_approval = {TicketStatus.APPROVED}
    valid_statuses = valid_from_no_approval | valid_from_with_approval

    if ticket.status not in valid_statuses:
        raise TicketExecutionTransitionError

    if ticket.status == TicketStatus.TRIAGE and ticket.requires_approval:
        raise TicketExecutionTransitionError

    if ticket.status == TicketStatus.APPROVED and not ticket.requires_approval:
        raise TicketExecutionTransitionError

    _validate_assigned_user(session, payload.assigned_to_user_id)
    _validate_supplier(session, payload.supplier_id)
    _validate_configured_transition(
        session,
        ticket=ticket,
        to_status=TicketStatus.IN_PROGRESS,
        current_user=current_user,
        comment=payload.execution_comment,
    )

    now = datetime.now(UTC)
    changes: dict[str, object] = {
        "started_at": now,
    }
    changes.update(_status_changes(session, to_status=TicketStatus.IN_PROGRESS))
    if payload.assigned_to_user_id is not None:
        changes["assigned_to_user_id"] = payload.assigned_to_user_id
    if payload.supplier_id is not None:
        changes["supplier_id"] = payload.supplier_id
    if payload.expected_resolution_at is not None:
        changes["expected_resolution_at"] = payload.expected_resolution_at

    old_status = ticket.status
    update_ticket(session, ticket, **changes)
    create_ticket_history(
        session,
        ticket_id=ticket.id,
        user_id=current_user.id,
        old_status=old_status,
        new_status=TicketStatus.IN_PROGRESS,
        comment=payload.execution_comment,
    )
    session.commit()

    persisted_ticket = get_ticket_detail_by_id(session, ticket.id)
    if persisted_ticket is None:
        raise TicketNotFoundError
    return build_ticket_detail_response(persisted_ticket)


def update_ticket_progress(
    session: Session,
    ticket_id: int,
    payload: TicketProgressUpdateRequest,
    current_user: User,
) -> TicketDetailResponse:
    _enforce_execution_permission(current_user)

    ticket = get_ticket_for_update(session, ticket_id)
    if ticket is None:
        raise TicketNotFoundError

    if ticket.status != TicketStatus.IN_PROGRESS:
        raise TicketProgressTransitionError

    _validate_assigned_user(session, payload.assigned_to_user_id)
    _validate_supplier(session, payload.supplier_id)

    changes: dict[str, object] = {}
    payload_fields = payload.model_fields_set

    if "expected_resolution_at" in payload_fields:
        changes["expected_resolution_at"] = payload.expected_resolution_at
    if "estimated_cost" in payload_fields and payload.estimated_cost is not None:
        changes["estimated_cost"] = payload.estimated_cost
    if "supplier_id" in payload_fields and payload.supplier_id is not None:
        changes["supplier_id"] = payload.supplier_id
    if "assigned_to_user_id" in payload_fields and payload.assigned_to_user_id is not None:
        changes["assigned_to_user_id"] = payload.assigned_to_user_id

    if changes:
        update_ticket(session, ticket, **changes)

    create_ticket_history(
        session,
        ticket_id=ticket.id,
        user_id=current_user.id,
        old_status=TicketStatus.IN_PROGRESS,
        new_status=TicketStatus.IN_PROGRESS,
        comment=payload.progress_comment,
    )
    session.commit()

    persisted_ticket = get_ticket_detail_by_id(session, ticket.id)
    if persisted_ticket is None:
        raise TicketNotFoundError
    return build_ticket_detail_response(persisted_ticket)


def resolve_ticket(
    session: Session,
    ticket_id: int,
    payload: TicketResolveRequest,
    current_user: User,
) -> TicketDetailResponse:
    _enforce_execution_permission(current_user)

    ticket = get_ticket_for_update(session, ticket_id)
    if ticket is None:
        raise TicketNotFoundError
    if ticket.status != TicketStatus.IN_PROGRESS:
        raise TicketResolveTransitionError
    if count_attachments_by_ticket_and_type(
        session,
        ticket_id=ticket.id,
        attachment_type=_CLOSING_ATTACHMENT_TYPE,
    ) == 0:
        raise MissingClosingEvidenceError
    _validate_configured_transition(
        session,
        ticket=ticket,
        to_status=TicketStatus.RESOLVED,
        current_user=current_user,
        comment=payload.solution_description,
    )

    changes: dict[str, object] = {
        "final_cost": payload.final_cost,
    }
    changes.update(_status_changes(session, to_status=TicketStatus.RESOLVED))
    if ticket.resolved_at is None:
        changes["resolved_at"] = datetime.now(UTC)

    old_status = ticket.status
    update_ticket(session, ticket, **changes)
    create_ticket_history(
        session,
        ticket_id=ticket.id,
        user_id=current_user.id,
        old_status=old_status,
        new_status=TicketStatus.RESOLVED,
        comment=payload.solution_description,
    )
    session.commit()

    persisted_ticket = get_ticket_detail_by_id(session, ticket.id)
    if persisted_ticket is None:
        raise TicketNotFoundError
    return build_ticket_detail_response(persisted_ticket)


def close_ticket(
    session: Session,
    ticket_id: int,
    payload: TicketCloseRequest,
    current_user: User,
) -> TicketDetailResponse:
    _enforce_execution_permission(current_user)

    ticket = get_ticket_for_update(session, ticket_id)
    if ticket is None:
        raise TicketNotFoundError
    if ticket.status != TicketStatus.RESOLVED:
        raise TicketCloseTransitionError
    _validate_configured_transition(
        session,
        ticket=ticket,
        to_status=TicketStatus.CLOSED,
        current_user=current_user,
        comment=payload.close_comment,
    )

    changes: dict[str, object] = _status_changes(session, to_status=TicketStatus.CLOSED)
    if ticket.closed_at is None:
        changes["closed_at"] = datetime.now(UTC)

    old_status = ticket.status
    update_ticket(session, ticket, **changes)
    create_ticket_history(
        session,
        ticket_id=ticket.id,
        user_id=current_user.id,
        old_status=old_status,
        new_status=TicketStatus.CLOSED,
        comment=payload.close_comment,
    )
    session.commit()

    persisted_ticket = get_ticket_detail_by_id(session, ticket.id)
    if persisted_ticket is None:
        raise TicketNotFoundError
    return build_ticket_detail_response(persisted_ticket)


def list_ticket_triage_assignees(
    session: Session,
    params: UserListParams,
    current_user: User,
) -> UserListResponse:
    _enforce_triage_permission(current_user)

    eligible_roles = [UserRole.ADMIN, UserRole.ENGINEERING]
    total = count_users(
        session,
        search=params.search,
        roles=eligible_roles,
        is_active=True,
    )
    items = list_users(
        session,
        page=params.page,
        page_size=params.page_size,
        search=params.search,
        roles=eligible_roles,
        is_active=True,
        sort=params.sort,
    )
    return UserListResponse(
        items=[UserResponse.model_validate(user) for user in items],
        total=total,
        page=params.page,
        page_size=params.page_size,
        pages=calculate_pages(total, params.page_size),
    )
