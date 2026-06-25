from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.pagination import PaginatedResponse, PageParams


class TicketAttachmentCreateRequest(BaseModel):
    attachment_type: str = Field(min_length=1, max_length=100)

    @field_validator("attachment_type")
    @classmethod
    def strip_attachment_type(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Attachment type is required.")
        return normalized


class TicketAttachmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ticket_id: int
    uploaded_by_user_id: int
    uploaded_by_user_name: str | None
    file_url: str
    file_type: str
    attachment_type: str
    created_at: datetime


class TicketAttachmentListParams(PageParams):
    pass


class TicketAttachmentListResponse(PaginatedResponse[TicketAttachmentResponse]):
    pass
