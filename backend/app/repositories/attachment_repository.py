from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.ticket_attachment import TicketAttachment


def create_attachment(
    session: Session,
    *,
    ticket_id: int,
    uploaded_by_user_id: int,
    file_url: str,
    file_type: str,
    attachment_type: str,
) -> TicketAttachment:
    attachment = TicketAttachment(
        ticket_id=ticket_id,
        uploaded_by_user_id=uploaded_by_user_id,
        file_url=file_url,
        file_type=file_type,
        attachment_type=attachment_type,
    )
    session.add(attachment)
    session.flush()
    return attachment


def get_attachment_by_id(session: Session, attachment_id: int) -> TicketAttachment | None:
    statement = (
        select(TicketAttachment)
        .options(selectinload(TicketAttachment.uploaded_by_user), selectinload(TicketAttachment.ticket))
        .where(TicketAttachment.id == attachment_id)
        .limit(1)
    )
    return session.scalar(statement)


def list_attachments_by_ticket_id(
    session: Session,
    *,
    ticket_id: int,
    page: int,
    page_size: int,
) -> list[TicketAttachment]:
    statement = (
        select(TicketAttachment)
        .options(selectinload(TicketAttachment.uploaded_by_user))
        .where(TicketAttachment.ticket_id == ticket_id)
        .order_by(TicketAttachment.created_at.desc(), TicketAttachment.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return list(session.scalars(statement).all())


def count_attachments_by_ticket_id(session: Session, *, ticket_id: int) -> int:
    statement = select(func.count()).select_from(TicketAttachment).where(TicketAttachment.ticket_id == ticket_id)
    return int(session.scalar(statement) or 0)


def count_attachments_by_ticket_and_type(
    session: Session,
    *,
    ticket_id: int,
    attachment_type: str,
) -> int:
    statement = (
        select(func.count())
        .select_from(TicketAttachment)
        .where(
            TicketAttachment.ticket_id == ticket_id,
            TicketAttachment.attachment_type == attachment_type,
        )
    )
    return int(session.scalar(statement) or 0)
