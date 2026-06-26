from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Index, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, CreatedAtMixin
from app.models.enum_columns import enum_values
from app.models.enums import AlertSeverity, AlertType


class TicketAlert(CreatedAtMixin, Base):
    __tablename__ = "ticket_alerts"
    __table_args__ = (
        Index("ix_ticket_alerts_ticket_id", "ticket_id"),
        Index("ix_ticket_alerts_alert_type", "alert_type"),
        Index("ix_ticket_alerts_is_read", "is_read"),
        Index("ix_ticket_alerts_created_at", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("tickets.id"), nullable=False)
    alert_type: Mapped[AlertType] = mapped_column(
        Enum(AlertType, name="alert_type_enum", native_enum=False, values_callable=enum_values),
        nullable=False,
    )
    severity: Mapped[AlertSeverity] = mapped_column(
        Enum(AlertSeverity, name="alert_severity_enum", native_enum=False, values_callable=enum_values),
        nullable=False,
    )
    message: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )
    created_by_system: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    ticket: Mapped["Ticket"] = relationship(back_populates="alerts")
