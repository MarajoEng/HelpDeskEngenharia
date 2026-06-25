from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.database import get_db_session
from app.models.user import User
from app.schemas.attachment import (
    TicketAttachmentListParams,
    TicketAttachmentListResponse,
    TicketAttachmentResponse,
)
from app.services.attachment_service import get_attachment_download, list_ticket_attachments, upload_ticket_attachment
from app.services.exceptions import ServiceError

router = APIRouter(tags=["attachments"])


def _raise_service_error(error: ServiceError) -> None:
    raise HTTPException(status_code=error.status_code, detail=error.detail)


def _build_attachment_list_params(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> TicketAttachmentListParams:
    return TicketAttachmentListParams(page=page, page_size=page_size)


@router.post("/tickets/{ticket_id}/attachments", response_model=TicketAttachmentResponse, status_code=201)
def create_ticket_attachment(
    ticket_id: int,
    attachment_type: str = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> TicketAttachmentResponse:
    try:
        return upload_ticket_attachment(
            session,
            ticket_id=ticket_id,
            attachment_type=attachment_type,
            upload=file,
            current_user=current_user,
        )
    except ServiceError as error:
        _raise_service_error(error)


@router.get("/tickets/{ticket_id}/attachments", response_model=TicketAttachmentListResponse)
def read_ticket_attachments(
    ticket_id: int,
    params: Annotated[TicketAttachmentListParams, Depends(_build_attachment_list_params)],
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> TicketAttachmentListResponse:
    try:
        return list_ticket_attachments(
            session,
            ticket_id=ticket_id,
            params=params,
            current_user=current_user,
        )
    except ServiceError as error:
        _raise_service_error(error)


@router.get("/attachments/{attachment_id}/download")
def download_attachment(
    attachment_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> FileResponse:
    try:
        payload = get_attachment_download(session, attachment_id=attachment_id, current_user=current_user)
    except ServiceError as error:
        _raise_service_error(error)

    return FileResponse(
        path=payload.file_path,
        media_type=payload.attachment.file_type,
        filename=payload.download_name,
    )
