from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy import Boolean, Date, ForeignKey, Index, JSON, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class TicketCustomField(TimestampMixin, Base):
    __tablename__ = "ticket_custom_fields"
    __table_args__ = (
        UniqueConstraint("category_id", "subcategory_id", "name", name="uq_ticket_custom_fields_scope_name"),
        Index("ix_ticket_custom_fields_category_id", "category_id"),
        Index("ix_ticket_custom_fields_subcategory_id", "subcategory_id"),
        Index("ix_ticket_custom_fields_is_active", "is_active"),
        Index("ix_ticket_custom_fields_display_order", "display_order"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("ticket_categories.id", ondelete="CASCADE"), nullable=False)
    subcategory_id: Mapped[int | None] = mapped_column(ForeignKey("ticket_subcategories.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    field_type: Mapped[str] = mapped_column(String(30), nullable=False)
    is_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    display_order: Mapped[int] = mapped_column(nullable=False, default=0, server_default="0")
    placeholder: Mapped[str | None] = mapped_column(String(255))
    help_text: Mapped[str | None] = mapped_column(Text)
    validation_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    options_json: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON)

    category: Mapped["TicketCategoryConfig"] = relationship(back_populates="custom_fields")
    subcategory: Mapped["TicketSubcategoryConfig | None"] = relationship(back_populates="custom_fields")
    values: Mapped[list["TicketCustomFieldValue"]] = relationship(back_populates="custom_field")


class TicketCustomFieldValue(TimestampMixin, Base):
    __tablename__ = "ticket_custom_field_values"
    __table_args__ = (
        UniqueConstraint("ticket_id", "custom_field_id", name="uq_ticket_custom_field_values_ticket_field"),
        Index("ix_ticket_custom_field_values_ticket_id", "ticket_id"),
        Index("ix_ticket_custom_field_values_custom_field_id", "custom_field_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False)
    custom_field_id: Mapped[int] = mapped_column(ForeignKey("ticket_custom_fields.id"), nullable=False)
    value_text: Mapped[str | None] = mapped_column(Text)
    value_number: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    value_boolean: Mapped[bool | None] = mapped_column(Boolean)
    value_date: Mapped[date | None] = mapped_column(Date)
    value_json: Mapped[dict[str, Any] | list[Any] | None] = mapped_column(JSON)

    ticket: Mapped["Ticket"] = relationship(back_populates="custom_field_values")
    custom_field: Mapped[TicketCustomField] = relationship(back_populates="values")
