from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.pagination import PageParams, PaginatedResponse


class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    actor_user_id: int | None
    actor_user_name: str | None
    action: str
    entity_type: str
    entity_id: int | None
    ip_address: str | None
    user_agent: str | None
    metadata_json: dict | None
    created_at: datetime


class AuditLogListParams(PageParams):
    actor_user_id: int | None = None
    action: str | None = None
    entity_type: str | None = None
    entity_id: int | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None
    search: str | None = None


class AuditLogListResponse(PaginatedResponse[AuditLogResponse]):
    pass
