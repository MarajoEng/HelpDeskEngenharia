from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, Index, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class TicketStatusConfig(TimestampMixin, Base):
    __tablename__ = "ticket_statuses"
    __table_args__ = (
        Index("ix_ticket_statuses_legacy_value", "legacy_value"),
        Index("ix_ticket_statuses_is_active", "is_active"),
        UniqueConstraint("name", name="uq_ticket_statuses_name"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    legacy_value: Mapped[str | None] = mapped_column(String(50))
    description: Mapped[str | None] = mapped_column(Text)
    color: Mapped[str] = mapped_column(String(32), nullable=False)
    is_initial: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    is_final: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    pauses_sla: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    allows_reopen: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")

    tickets: Mapped[list["Ticket"]] = relationship(back_populates="configured_status")
    outgoing_transitions: Mapped[list["TicketStatusTransitionConfig"]] = relationship(
        back_populates="from_status",
        foreign_keys="TicketStatusTransitionConfig.from_status_id",
        cascade="all, delete-orphan",
    )
    incoming_transitions: Mapped[list["TicketStatusTransitionConfig"]] = relationship(
        back_populates="to_status",
        foreign_keys="TicketStatusTransitionConfig.to_status_id",
        cascade="all, delete-orphan",
    )


class TicketStatusTransitionConfig(TimestampMixin, Base):
    __tablename__ = "ticket_status_transitions"
    __table_args__ = (
        UniqueConstraint("from_status_id", "to_status_id", name="uq_ticket_status_transitions_from_to"),
        Index("ix_ticket_status_transitions_from_status_id", "from_status_id"),
        Index("ix_ticket_status_transitions_to_status_id", "to_status_id"),
        Index("ix_ticket_status_transitions_is_active", "is_active"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    from_status_id: Mapped[int] = mapped_column(ForeignKey("ticket_statuses.id", ondelete="CASCADE"), nullable=False)
    to_status_id: Mapped[int] = mapped_column(ForeignKey("ticket_statuses.id", ondelete="CASCADE"), nullable=False)
    requires_comment: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    requires_attachment: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    allowed_roles_json: Mapped[list[str] | None] = mapped_column(JSON)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")

    from_status: Mapped[TicketStatusConfig] = relationship(
        back_populates="outgoing_transitions",
        foreign_keys=[from_status_id],
    )
    to_status: Mapped[TicketStatusConfig] = relationship(
        back_populates="incoming_transitions",
        foreign_keys=[to_status_id],
    )
