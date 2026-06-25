from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.enums import UserRole
from app.models.ticket import Ticket
from app.models.ticket_attachment import TicketAttachment
from app.models.user import User
from app.repositories.attachment_repository import (
    count_attachments_by_ticket_id,
    create_attachment,
    get_attachment_by_id,
    list_attachments_by_ticket_id,
)
from app.repositories.ticket_repository import get_ticket_by_id
from app.schemas.attachment import (
    TicketAttachmentListParams,
    TicketAttachmentListResponse,
    TicketAttachmentResponse,
)
from app.schemas.pagination import calculate_pages
from app.services.exceptions import NotFoundServiceError, ValidationServiceError
from app.services.ticket_service import TicketNotFoundError, TicketPermissionError

_ALLOWED_UPLOAD_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "application/pdf": ".pdf",
}


class AttachmentNotFoundError(NotFoundServiceError):
    detail = "Attachment not found."


class InvalidAttachmentTypeError(ValidationServiceError):
    detail = "Attachment type is required."


class InvalidAttachmentFileTypeError(ValidationServiceError):
    detail = "Unsupported file type. Allowed types: JPEG, PNG, WEBP and PDF."


class AttachmentFileTooLargeError(ValidationServiceError):
    detail = "File exceeds the configured upload limit."


class EmptyAttachmentFileError(ValidationServiceError):
    detail = "Uploaded file is empty."


class AttachmentFileMissingError(NotFoundServiceError):
    detail = "Attachment file is not available on disk."


@dataclass
class AttachmentDownloadPayload:
    attachment: TicketAttachment
    file_path: Path
    download_name: str


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


def _get_upload_root() -> Path:
    settings = get_settings()
    return Path(settings.upload_dir)


def _resolve_storage_path(stored_file_url: str) -> Path:
    return _get_upload_root() / Path(stored_file_url)


def _assert_attachment_type(attachment_type: str) -> str:
    normalized = attachment_type.strip()
    if not normalized:
        raise InvalidAttachmentTypeError
    return normalized


def _can_upload_attachment(current_user: User, ticket: Ticket) -> bool:
    if current_user.role in {UserRole.ADMIN, UserRole.ENGINEERING}:
        return True
    if current_user.role == UserRole.MANAGER and current_user.unit_id == ticket.unit_id:
        return True
    return False


def _can_view_attachment(current_user: User, ticket: Ticket) -> bool:
    if current_user.role in {UserRole.ADMIN, UserRole.ENGINEERING, UserRole.DIRECTOR}:
        return True
    if current_user.role == UserRole.MANAGER and current_user.unit_id == ticket.unit_id:
        return True
    return False


def _get_ticket_or_404(session: Session, ticket_id: int) -> Ticket:
    ticket = get_ticket_by_id(session, ticket_id)
    if ticket is None:
        raise TicketNotFoundError
    return ticket


def _validate_upload_file(upload: UploadFile) -> tuple[str, bytes]:
    content_type = (upload.content_type or "").strip().lower()
    if content_type not in _ALLOWED_UPLOAD_TYPES:
        raise InvalidAttachmentFileTypeError

    file_bytes = upload.file.read()
    if not file_bytes:
        raise EmptyAttachmentFileError

    max_size_bytes = get_settings().max_upload_size_mb * 1024 * 1024
    if len(file_bytes) > max_size_bytes:
        raise AttachmentFileTooLargeError(
            f"File exceeds the configured upload limit of {get_settings().max_upload_size_mb} MB."
        )

    return content_type, file_bytes


def upload_ticket_attachment(
    session: Session,
    *,
    ticket_id: int,
    attachment_type: str,
    upload: UploadFile,
    current_user: User,
) -> TicketAttachmentResponse:
    ticket = _get_ticket_or_404(session, ticket_id)
    if not _can_upload_attachment(current_user, ticket):
        raise TicketPermissionError

    normalized_attachment_type = _assert_attachment_type(attachment_type)
    content_type, file_bytes = _validate_upload_file(upload)

    extension = Path(upload.filename or "").suffix.lower() or _ALLOWED_UPLOAD_TYPES[content_type]
    if extension not in {".jpg", ".jpeg", ".png", ".webp", ".pdf"}:
        extension = _ALLOWED_UPLOAD_TYPES[content_type]

    relative_path = Path("tickets") / str(ticket.id) / f"{uuid4().hex}{extension}"
    absolute_path = _resolve_storage_path(relative_path.as_posix())
    absolute_path.parent.mkdir(parents=True, exist_ok=True)

    attachment_record: TicketAttachment | None = None
    file_written = False
    try:
        absolute_path.write_bytes(file_bytes)
        file_written = True
        attachment_record = create_attachment(
            session,
            ticket_id=ticket.id,
            uploaded_by_user_id=current_user.id,
            file_url=relative_path.as_posix(),
            file_type=content_type,
            attachment_type=normalized_attachment_type,
        )
        session.commit()
    except Exception:
        session.rollback()
        if file_written and absolute_path.exists():
            absolute_path.unlink(missing_ok=True)
        raise

    session.refresh(attachment_record)
    return _to_attachment_response(attachment_record)


def list_ticket_attachments(
    session: Session,
    *,
    ticket_id: int,
    params: TicketAttachmentListParams,
    current_user: User,
) -> TicketAttachmentListResponse:
    ticket = _get_ticket_or_404(session, ticket_id)
    if not _can_view_attachment(current_user, ticket):
        raise TicketPermissionError

    total = count_attachments_by_ticket_id(session, ticket_id=ticket.id)
    items = list_attachments_by_ticket_id(
        session,
        ticket_id=ticket.id,
        page=params.page,
        page_size=params.page_size,
    )
    return TicketAttachmentListResponse(
        items=[_to_attachment_response(item) for item in items],
        total=total,
        page=params.page,
        page_size=params.page_size,
        pages=calculate_pages(total, params.page_size),
    )


def get_attachment_download(
    session: Session,
    *,
    attachment_id: int,
    current_user: User,
) -> AttachmentDownloadPayload:
    attachment = get_attachment_by_id(session, attachment_id)
    if attachment is None or attachment.ticket is None:
        raise AttachmentNotFoundError
    if not _can_view_attachment(current_user, attachment.ticket):
        raise TicketPermissionError

    file_path = _resolve_storage_path(attachment.file_url)
    if not file_path.exists() or not file_path.is_file():
        raise AttachmentFileMissingError

    extension = file_path.suffix.lower()
    download_name = f"attachment-{attachment.id}{extension}"
    return AttachmentDownloadPayload(
        attachment=attachment,
        file_path=file_path,
        download_name=download_name,
    )
