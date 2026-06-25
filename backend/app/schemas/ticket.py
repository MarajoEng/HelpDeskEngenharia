from __future__ import annotations

from datetime import UTC, datetime
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


class TicketUnitSummary(BaseModel):
    id: int
    code: str
    name: str
    city: str
    state: str


class TicketUserSummary(BaseModel):
    id: int
    name: str


class TicketHistoryResponse(BaseModel):
    id: int
    user_id: int
    user_name: str | None
    old_status: TicketStatus | None
    new_status: TicketStatus
    comment: str | None
    created_at: datetime


class TicketIndicators(BaseModel):
    estimated_loss_total: Decimal | None
    elapsed_hours: float | None
    is_late: bool
    sla_status: Literal["on_track", "late", "no_sla", "closed"]


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
    assigned_to_user_name: str | None = None


class TicketDetailResponse(BaseModel):
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
    unit: TicketUnitSummary | None
    opened_by: TicketUserSummary | None
    assigned_to: TicketUserSummary | None
    history: list[TicketHistoryResponse]
    indicators: TicketIndicators


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
    only_late: bool | None = None
    has_fuel_nozzles_stopped: bool | None = None
    min_estimated_cost: Decimal | None = Field(default=None, ge=0)
    max_estimated_cost: Decimal | None = Field(default=None, ge=0)
    queue: Literal["engineering"] | None = None

    @field_validator("search")
    @classmethod
    def strip_search(cls, value: str | None) -> str | None:
        if value is None:
            return value
        normalized = value.strip()
        return normalized or None


class TicketTriageRequest(BaseModel):
    assigned_to_user_id: int | None = Field(default=None, ge=1)
    priority: PriorityLevel | None = None
    severity: TicketSeverity | None = None
    requires_approval: bool | None = None
    sla_due_at: datetime | None = None
    technical_comment: str = Field(min_length=1)

    @field_validator("technical_comment")
    @classmethod
    def strip_technical_comment(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Technical comment is required.")
        return normalized

    @field_validator("sla_due_at")
    @classmethod
    def validate_sla_due_at(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return value

        normalized = value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)
        if normalized < datetime.now(UTC):
            raise ValueError("SLA due date cannot be in the past.")
        return normalized
