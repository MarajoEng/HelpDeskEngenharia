from __future__ import annotations

from datetime import UTC, date, datetime, time
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator, model_validator

from app.models.enums import PriorityLevel, TicketCategory, TicketSeverity, TicketStatus
from app.schemas.pagination import MAX_PAGE_SIZE, PaginatedResponse, PageParams


class ReportFilters(PageParams):
    page_size: int = Field(default=20, ge=1, le=MAX_PAGE_SIZE)
    date_from: date | None = None
    date_to: date | None = None
    unit_id: int | None = Field(default=None, ge=1)
    group_code: str | None = None
    branch_code: str | None = None
    region: str | None = None
    status: TicketStatus | None = None
    category: TicketCategory | None = None
    category_id: int | None = Field(default=None, ge=1)
    subcategory_id: int | None = Field(default=None, ge=1)
    type_id: int | None = Field(default=None, ge=1)
    priority: PriorityLevel | None = None
    priority_id: int | None = Field(default=None, ge=1)
    severity: TicketSeverity | None = None
    supplier_id: int | None = Field(default=None, ge=1)
    only_late: bool | None = None
    requires_approval: bool | None = None
    min_estimated_cost: Decimal | None = Field(default=None, ge=0, decimal_places=2)
    max_estimated_cost: Decimal | None = Field(default=None, ge=0, decimal_places=2)

    @field_validator("region", "group_code", "branch_code")
    @classmethod
    def strip_region(cls, value: str | None) -> str | None:
        if value is None:
            return value
        normalized = value.strip()
        return normalized or None

    @model_validator(mode="after")
    def validate_filters(self) -> "ReportFilters":
        if self.date_from and self.date_to and self.date_from > self.date_to:
            raise ValueError("date_from nao pode ser maior que date_to.")
        if (
            self.min_estimated_cost is not None
            and self.max_estimated_cost is not None
            and self.max_estimated_cost < self.min_estimated_cost
        ):
            raise ValueError("max_estimated_cost deve ser maior ou igual a min_estimated_cost.")
        return self

    def opened_from_datetime(self) -> datetime | None:
        if self.date_from is None:
            return None
        return datetime.combine(self.date_from, time.min).replace(tzinfo=UTC)

    def opened_to_datetime(self) -> datetime | None:
        if self.date_to is None:
            return None
        return datetime.combine(self.date_to, time.max).replace(tzinfo=UTC)

    def to_audit_metadata(self) -> dict[str, object]:
        metadata: dict[str, object] = {
            "page": self.page,
            "page_size": self.page_size,
        }
        for field_name in (
            "date_from",
            "date_to",
            "unit_id",
            "region",
            "status",
            "category",
            "category_id",
            "subcategory_id",
            "type_id",
            "priority",
            "priority_id",
            "severity",
            "supplier_id",
            "only_late",
            "requires_approval",
            "min_estimated_cost",
            "max_estimated_cost",
        ):
            value = getattr(self, field_name)
            if value is None:
                continue
            if hasattr(value, "value"):
                metadata[field_name] = value.value
            elif isinstance(value, (date, datetime)):
                metadata[field_name] = value.isoformat()
            else:
                metadata[field_name] = str(value) if isinstance(value, Decimal) else value
        return metadata


class TicketReportItem(BaseModel):
    id: int
    ticket_number: str
    unit_id: int
    unit_code: str
    unit_name: str
    status: TicketStatus
    category_id: int | None = None
    subcategory_id: int | None = None
    type_id: int | None = None
    category: TicketCategory
    category_name: str
    subcategory_name: str | None = None
    type_name: str | None = None
    priority_id: int | None = None
    priority: PriorityLevel
    priority_name: str
    priority_color: str | None = None
    priority_weight: int | None = None
    severity: TicketSeverity
    opened_by_user_name: str | None
    assigned_to_user_name: str | None
    supplier_name: str | None
    opened_at: datetime
    resolved_at: datetime | None
    closed_at: datetime | None
    sla_due_at: datetime | None
    is_late: bool
    estimated_cost: Decimal | None
    approved_cost: Decimal | None
    final_cost: Decimal | None
    fuel_nozzles_stopped: int | None
    requires_approval: bool


class TicketReportResponse(PaginatedResponse[TicketReportItem]):
    pass


class CostReportItem(BaseModel):
    unit_id: int
    unit_code: str
    unit_name: str
    category_id: int | None = None
    category: TicketCategory
    category_name: str
    supplier_id: int | None
    supplier_name: str | None
    estimated_cost_total: Decimal
    approved_cost_total: Decimal
    final_cost_total: Decimal
    total_tickets: int
    average_ticket_cost: Decimal


class CostReportResponse(PaginatedResponse[CostReportItem]):
    pass


class SlaReportItem(BaseModel):
    unit_id: int
    unit_code: str
    unit_name: str
    total_with_sla: int
    on_track: int
    late: int
    closed_on_time: int
    closed_late: int
    compliance_rate: float
    average_resolution_hours: float
    average_closure_hours: float


class SlaReportResponse(PaginatedResponse[SlaReportItem]):
    pass


class UnitReportItem(BaseModel):
    unit_id: int
    unit_code: str
    unit_name: str
    region: str
    total_tickets: int
    critical_tickets: int
    late_tickets: int
    in_progress_tickets: int
    closed_tickets: int
    final_cost_total: Decimal
    total_fuel_nozzles_stopped: int
    estimated_daily_loss_total: Decimal


class UnitReportResponse(PaginatedResponse[UnitReportItem]):
    pass


class SupplierReportItem(BaseModel):
    supplier_id: int
    supplier_name: str
    total_tickets: int
    in_progress_tickets: int
    resolved_tickets: int
    closed_tickets: int
    final_cost_total: Decimal
    average_execution_hours: float
    late_execution_tickets: int


class SupplierReportResponse(PaginatedResponse[SupplierReportItem]):
    pass
