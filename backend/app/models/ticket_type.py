from sqlalchemy import Boolean, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class TicketTypeConfig(TimestampMixin, Base):
    __tablename__ = "ticket_types"
    __table_args__ = (
        Index("ix_ticket_types_is_active", "is_active"),
        Index("ix_ticket_types_display_order", "display_order"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )
    display_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )

    category_types: Mapped[list["TicketCategoryTypeLink"]] = relationship(
        back_populates="ticket_type",
        cascade="all, delete-orphan",
    )
