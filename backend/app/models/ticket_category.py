from sqlalchemy import Boolean, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class TicketCategoryConfig(TimestampMixin, Base):
    __tablename__ = "ticket_categories"
    __table_args__ = (
        Index("ix_ticket_categories_is_active", "is_active"),
        Index("ix_ticket_categories_display_order", "display_order"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    legacy_value: Mapped[str | None] = mapped_column(String(50))
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
    requires_attachment: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )
    requires_location: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    subcategories: Mapped[list["TicketSubcategoryConfig"]] = relationship(
        back_populates="category",
        cascade="all, delete-orphan",
    )
    category_types: Mapped[list["TicketCategoryTypeLink"]] = relationship(
        back_populates="category",
        cascade="all, delete-orphan",
    )
    custom_fields: Mapped[list["TicketCustomField"]] = relationship(
        back_populates="category",
        cascade="all, delete-orphan",
    )
