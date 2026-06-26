from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models.enums import ApprovalStatus, TicketStatus, UserRole
from app.models.user import User
from app.repositories.approval_level_repository import get_active_approval_level_for_amount
from app.repositories.approval_repository import create_approval, get_pending_approval_by_ticket_id, update_approval
from app.repositories.ticket_repository import create_ticket_history, get_ticket_detail_by_id, get_ticket_for_update, update_ticket
from app.schemas.approval import ApprovalDecisionRequest, ApprovalRequestCreate
from app.schemas.ticket import TicketDetailResponse
from app.services.exceptions import ConflictServiceError, ValidationServiceError
from app.services.ticket_service import (
    TicketNotFoundError,
    _status_changes,
    _validate_configured_transition,
    build_ticket_detail_response,
)


class ApprovalLevelNotConfiguredError(ValidationServiceError):
    detail = "No active approval level is configured for the requested amount."


class ApprovalPermissionError(ValidationServiceError):
    status_code = 403
    detail = "Insufficient permissions."


class ApprovalRequestDuplicateError(ConflictServiceError):
    detail = "Ticket already has a pending approval request."


class ApprovalRequestTransitionError(ConflictServiceError):
    detail = "Ticket cannot request approval from the current status."


class ApprovalDecisionTransitionError(ConflictServiceError):
    detail = "Ticket cannot be decided from the current status."


class ApprovalPendingNotFoundError(ConflictServiceError):
    detail = "Ticket does not have a pending approval request."


class TicketApprovalNotRequiredError(ValidationServiceError):
    detail = "Ticket does not require approval."


class ApprovalRoleNotAllowedError(ValidationServiceError):
    status_code = 403
    detail = "Your role is not allowed to approve this amount."


def _enforce_approval_request_permission(current_user: User) -> None:
    if current_user.role not in {UserRole.ADMIN, UserRole.ENGINEERING}:
        raise ApprovalPermissionError


def _merge_justifications(request_justification: str, decision_justification: str) -> str:
    return (
        f"Solicitacao: {request_justification}\n"
        f"Decisao: {decision_justification}"
    )


def request_ticket_approval(
    session: Session,
    ticket_id: int,
    payload: ApprovalRequestCreate,
    current_user: User,
) -> TicketDetailResponse:
    _enforce_approval_request_permission(current_user)

    ticket = get_ticket_for_update(session, ticket_id)
    if ticket is None:
        raise TicketNotFoundError
    if get_pending_approval_by_ticket_id(session, ticket.id) is not None:
        raise ApprovalRequestDuplicateError
    if ticket.status != TicketStatus.TRIAGE:
        raise ApprovalRequestTransitionError
    if not ticket.requires_approval:
        raise TicketApprovalNotRequiredError

    approval_level = get_active_approval_level_for_amount(session, payload.amount_requested)
    if approval_level is None:
        raise ApprovalLevelNotConfiguredError

    create_approval(
        session,
        ticket_id=ticket.id,
        approval_level_id=approval_level.id,
        requested_by_user_id=current_user.id,
        approved_by_user_id=None,
        status=ApprovalStatus.PENDING,
        amount_requested=payload.amount_requested,
        amount_approved=None,
        justification=payload.justification,
        approved_at=None,
    )
    _validate_configured_transition(
        session,
        ticket=ticket,
        to_status=TicketStatus.WAITING_APPROVAL,
        current_user=current_user,
        comment=payload.justification,
    )
    update_ticket(
        session,
        ticket,
        **_status_changes(session, to_status=TicketStatus.WAITING_APPROVAL),
    )
    create_ticket_history(
        session,
        ticket_id=ticket.id,
        user_id=current_user.id,
        old_status=TicketStatus.TRIAGE,
        new_status=TicketStatus.WAITING_APPROVAL,
        comment=payload.justification,
    )
    session.commit()

    persisted_ticket = get_ticket_detail_by_id(session, ticket.id)
    if persisted_ticket is None:
        raise TicketNotFoundError
    return build_ticket_detail_response(persisted_ticket)


def decide_ticket_approval(
    session: Session,
    ticket_id: int,
    payload: ApprovalDecisionRequest,
    current_user: User,
) -> TicketDetailResponse:
    ticket = get_ticket_for_update(session, ticket_id)
    if ticket is None:
        raise TicketNotFoundError
    if ticket.status != TicketStatus.WAITING_APPROVAL:
        raise ApprovalDecisionTransitionError

    approval = get_pending_approval_by_ticket_id(session, ticket.id)
    if approval is None:
        raise ApprovalPendingNotFoundError
    if approval.approval_level is None:
        raise ApprovalLevelNotConfiguredError
    if current_user.role in {UserRole.MANAGER, UserRole.SUPPLIER}:
        raise ApprovalRoleNotAllowedError

    allowed_roles = set(approval.approval_level.allowed_roles)
    if current_user.role.value not in allowed_roles:
        raise ApprovalRoleNotAllowedError

    decided_at = datetime.now(UTC)
    if payload.decision == ApprovalStatus.APPROVED.value:
        approved_amount = payload.amount_approved if payload.amount_approved is not None else approval.amount_requested
        update_approval(
            session,
            approval,
            status=ApprovalStatus.APPROVED,
            amount_approved=approved_amount,
            approved_by_user_id=current_user.id,
            approved_at=decided_at,
            justification=_merge_justifications(approval.justification, payload.justification),
        )
        _validate_configured_transition(
            session,
            ticket=ticket,
            to_status=TicketStatus.APPROVED,
            current_user=current_user,
            comment=payload.justification,
        )
        update_ticket(
            session,
            ticket,
            approved_cost=approved_amount,
            approved_at=decided_at,
            **_status_changes(session, to_status=TicketStatus.APPROVED),
        )
        create_ticket_history(
            session,
            ticket_id=ticket.id,
            user_id=current_user.id,
            old_status=TicketStatus.WAITING_APPROVAL,
            new_status=TicketStatus.APPROVED,
            comment=payload.justification,
        )
    else:
        update_approval(
            session,
            approval,
            status=ApprovalStatus.REJECTED,
            approved_by_user_id=current_user.id,
            approved_at=decided_at,
            justification=_merge_justifications(approval.justification, payload.justification),
        )
        _validate_configured_transition(
            session,
            ticket=ticket,
            to_status=TicketStatus.REJECTED,
            current_user=current_user,
            comment=payload.justification,
        )
        update_ticket(
            session,
            ticket,
            **_status_changes(session, to_status=TicketStatus.REJECTED),
        )
        create_ticket_history(
            session,
            ticket_id=ticket.id,
            user_id=current_user.id,
            old_status=TicketStatus.WAITING_APPROVAL,
            new_status=TicketStatus.REJECTED,
            comment=payload.justification,
        )

    session.commit()

    persisted_ticket = get_ticket_detail_by_id(session, ticket.id)
    if persisted_ticket is None:
        raise TicketNotFoundError
    return build_ticket_detail_response(persisted_ticket)
