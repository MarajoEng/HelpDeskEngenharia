from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import PriorityLevel, TicketCategory, TicketSeverity, TicketStatus
from app.schemas.pagination import PaginatedResponse, PageParams


class TicketCreate(BaseModel):
    unit_id: int = Field(ge=1)
    category: TicketCategory
    problem_type: str = Field(min_length=1, max_length=255)
    title: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=1)
    priority: PriorityLevel
    severity: TicketSeverity
    operational_impact: str | None = None
    fuel_nozzles_stopped: int | None = Field(default=None, ge=0)
    estimated_daily_loss: Decimal | None = Field(default=None, ge=0, decimal_places=2)
    estimated_cost: Decimal | None = Field(default=None, ge=0, decimal_places=2)
    requires_approval: bool = False

    @field_validator("problem_type", "title", "description")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Field cannot be empty.")
        return normalized

    @field_validator("operational_impact")
    @classmethod
    def strip_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return value
        normalized = value.strip()
        return normalized or None


class TicketResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ticket_number: str
    unit_id: int
    opened_by_user_id: int
    assigned_to_user_id: int | None
    category: TicketCategory
    problem_type: str
    title: str
    description: str
    priority: PriorityLevel
    severity: TicketSeverity
    status: TicketStatus
    operational_impact: str | None
    fuel_nozzles_stopped: int | None
    estimated_daily_loss: Decimal | None
    estimated_loss_total: Decimal | None
    estimated_cost: Decimal | None
    approved_cost: Decimal | None
    final_cost: Decimal | None
    requires_approval: bool
    opened_at: datetime
    triaged_at: datetime | None
    approved_at: datetime | None
    started_at: datetime | None
    resolved_at: datetime | None
    closed_at: datetime | None
    sla_due_at: datetime | None
    created_at: datetime
    updated_at: datetime
    unit_name: str | None = None
    unit_code: str | None = None
    opened_by_user_name: str | None = None


class TicketListResponse(PaginatedResponse[TicketResponse]):
    pass


class TicketListParams(PageParams):
    unit_id: int | None = Field(default=None, ge=1)
    status: TicketStatus | None = None
    category: TicketCategory | None = None
    priority: PriorityLevel | None = None
    severity: TicketSeverity | None = None
    requires_approval: bool | None = None
    opened_from: datetime | None = None
    opened_to: datetime | None = None
    search: str | None = None
    sort: Literal["opened_at_desc"] = "opened_at_desc"

    @field_validator("search")
    @classmethod
    def strip_search(cls, value: str | None) -> str | None:
        if value is None:
            return value
        normalized = value.strip()
        return normalized or None
