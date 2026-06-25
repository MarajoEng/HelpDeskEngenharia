from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.approval import Approval
from app.models.enums import ApprovalStatus


def create_approval(session: Session, **payload: object) -> Approval:
    approval = Approval(**payload)
    session.add(approval)
    session.flush()
    return approval


def update_approval(session: Session, approval: Approval, **changes: object) -> Approval:
    for field, value in changes.items():
        setattr(approval, field, value)

    session.add(approval)
    session.flush()
    return approval


def get_pending_approval_by_ticket_id(session: Session, ticket_id: int) -> Approval | None:
    statement = (
        select(Approval)
        .options(
            selectinload(Approval.approval_level),
            selectinload(Approval.requested_by_user),
            selectinload(Approval.approved_by_user),
        )
        .where(
            Approval.ticket_id == ticket_id,
            Approval.status == ApprovalStatus.PENDING,
        )
        .order_by(Approval.id.desc())
        .limit(1)
    )
    return session.scalar(statement)
