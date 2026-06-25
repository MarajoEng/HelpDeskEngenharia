from __future__ import annotations

from datetime import UTC, date, datetime, time

from pydantic import BaseModel, Field, field_validator, model_validator

from app.models.enums import PriorityLevel, TicketCategory, TicketSeverity, TicketStatus


class DashboardOverviewParams(BaseModel):
    date_from: date | None = None
    date_to: date | None = None
    unit_id: int | None = Field(default=None, ge=1)
    region: str | None = None
    status: TicketStatus | None = None
    category: TicketCategory | None = None

    @field_validator("region")
    @classmethod
    def strip_region(cls, value: str | None) -> str | None:
        if value is None:
            return value
        normalized = value.strip()
        return normalized or None

    @model_validator(mode="after")
    def validate_date_range(self) -> "DashboardOverviewParams":
        if self.date_from and self.date_to and self.date_from > self.date_to:
            raise ValueError("date_from cannot be after date_to.")
        return self

    def opened_from_datetime(self) -> datetime | None:
        if self.date_from is None:
            return None
        return datetime.combine(self.date_from, time.min, tzinfo=UTC)

    def opened_to_datetime(self) -> datetime | None:
        if self.date_to is None:
            return None
        return datetime.combine(self.date_to, time.max, tzinfo=UTC)


class ExecutiveCards(BaseModel):
    total_open: int
    total_late: int
    total_critical: int
    total_in_progress: int
    total_fuel_nozzles_stopped: int
    estimated_daily_loss_total: float
    final_cost_total: float
    sla_compliance_rate: float


class UnitTicketsRankingItem(BaseModel):
    unit_id: int
    unit_code: str
    unit_name: str
    total_tickets: int
    late_tickets: int
    critical_tickets: int


class UnitCostRankingItem(BaseModel):
    unit_id: int
    unit_code: str
    unit_name: str
    estimated_cost_total: float
    final_cost_total: float


class UnitFuelNozzlesRankingItem(BaseModel):
    unit_id: int
    unit_code: str
    unit_name: str
    total_fuel_nozzles_stopped: int
    estimated_daily_loss_total: float


class TicketsByStatusItem(BaseModel):
    status: TicketStatus
    total: int


class TicketsByCategoryItem(BaseModel):
    category: TicketCategory
    total: int


class TicketsByPriorityItem(BaseModel):
    priority: PriorityLevel
    total: int


class TicketsBySeverityItem(BaseModel):
    severity: TicketSeverity
    total: int


class SlaSummary(BaseModel):
    total_with_sla: int
    on_track: int
    late: int
    closed_on_time: int
    closed_late: int
    compliance_rate: float


class LateTicketsPreviewItem(BaseModel):
    id: int
    ticket_number: str
    unit_code: str
    unit_name: str
    title: str
    status: TicketStatus
    priority: PriorityLevel
    severity: TicketSeverity
    sla_due_at: datetime
    opened_at: datetime


class DashboardOverviewResponse(BaseModel):
    total_tickets: int
    open_tickets: int
    triage_tickets: int
    waiting_approval_tickets: int
    approved_tickets: int
    in_progress_tickets: int
    resolved_tickets: int
    closed_tickets: int
    canceled_tickets: int
    late_tickets: int
    critical_tickets: int
    tickets_with_fuel_nozzles_stopped: int
    total_fuel_nozzles_stopped: int
    estimated_daily_loss_total: float
    estimated_cost_total: float
    approved_cost_total: float
    final_cost_total: float
    average_resolution_hours: float
    average_closure_hours: float
    sla_compliance_rate: float
    executive_cards: ExecutiveCards
    ranking_units_by_tickets: list[UnitTicketsRankingItem]
    ranking_units_by_cost: list[UnitCostRankingItem]
    ranking_units_by_fuel_nozzles: list[UnitFuelNozzlesRankingItem]
    tickets_by_status: list[TicketsByStatusItem]
    tickets_by_category: list[TicketsByCategoryItem]
    tickets_by_priority: list[TicketsByPriorityItem]
    tickets_by_severity: list[TicketsBySeverityItem]
    sla_summary: SlaSummary
    late_tickets_preview: list[LateTicketsPreviewItem]
