from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Index, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.enums import PriorityLevel, TicketCategory, TicketSeverity, TicketStatus


class Ticket(TimestampMixin, Base):
    __tablename__ = "tickets"
    __table_args__ = (
        Index("ix_tickets_unit_id", "unit_id"),
        Index("ix_tickets_status", "status"),
        Index("ix_tickets_priority", "priority"),
        Index("ix_tickets_severity", "severity"),
        Index("ix_tickets_category", "category"),
        Index("ix_tickets_opened_at", "opened_at"),
        Index("ix_tickets_closed_at", "closed_at"),
        Index("ix_tickets_sla_due_at", "sla_due_at"),
        Index("ix_tickets_requires_approval", "requires_approval"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    ticket_number: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    unit_id: Mapped[int] = mapped_column(ForeignKey("units.id"), nullable=False)
    opened_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    assigned_to_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    category: Mapped[TicketCategory] = mapped_column(
        Enum(TicketCategory, name="ticket_category", native_enum=False),
        nullable=False,
    )
    problem_type: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[PriorityLevel] = mapped_column(
        Enum(PriorityLevel, name="priority_level", native_enum=False),
        nullable=False,
    )
    severity: Mapped[TicketSeverity] = mapped_column(
        Enum(
            TicketSeverity,
            name="ticket_severity",
            native_enum=False,
            create_constraint=True,
            length=50,
        ),
        nullable=False,
    )
    status: Mapped[TicketStatus] = mapped_column(
        Enum(TicketStatus, name="ticket_status", native_enum=False),
        nullable=False,
        default=TicketStatus.OPEN,
        server_default=TicketStatus.OPEN.value,
    )
    operational_impact: Mapped[str | None] = mapped_column(Text)
    fuel_nozzles_stopped: Mapped[int | None] = mapped_column()
    estimated_daily_loss: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    estimated_cost: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    approved_cost: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    final_cost: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    requires_approval: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )
    opened_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    triaged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    sla_due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    unit: Mapped["Unit"] = relationship(back_populates="tickets")
    opened_by_user: Mapped["User"] = relationship(
        back_populates="opened_tickets",
        foreign_keys=[opened_by_user_id],
    )
    assigned_to_user: Mapped["User | None"] = relationship(
        back_populates="assigned_tickets",
        foreign_keys=[assigned_to_user_id],
    )
    history_entries: Mapped[list["TicketHistory"]] = relationship(
        back_populates="ticket",
        cascade="all, delete-orphan",
    )
    attachments: Mapped[list["TicketAttachment"]] = relationship(
        back_populates="ticket",
        cascade="all, delete-orphan",
    )
    approvals: Mapped[list["Approval"]] = relationship(
        back_populates="ticket",
        cascade="all, delete-orphan",
    )
