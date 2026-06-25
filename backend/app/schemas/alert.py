from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import AlertSeverity, AlertType
from app.schemas.pagination import PageParams, PaginatedResponse


class TicketAlertResponse(BaseModel):
    id: int
    ticket_id: int
    ticket_number: str
    unit_code: str
    unit_name: str
    alert_type: AlertType
    severity: AlertSeverity
    message: str
    is_read: bool
    created_at: datetime
    read_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class TicketAlertListParams(PageParams):
    is_read: bool | None = None
    alert_type: AlertType | None = None
    severity: AlertSeverity | None = None
    ticket_id: int | None = None
    unit_id: int | None = None


class TicketAlertListResponse(PaginatedResponse[TicketAlertResponse]):
    pass


class RunSlaMonitorResponse(BaseModel):
    checked_tickets: int
    created_alerts: int
    skipped_duplicates: int
