from sqlalchemy import Boolean, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class TicketSubcategoryConfig(TimestampMixin, Base):
    __tablename__ = "ticket_subcategories"
    __table_args__ = (
        UniqueConstraint("category_id", "name"),
        Index("ix_ticket_subcategories_category_id", "category_id"),
        Index("ix_ticket_subcategories_is_active", "is_active"),
        Index("ix_ticket_subcategories_display_order", "display_order"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("ticket_categories.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
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

    category: Mapped["TicketCategoryConfig"] = relationship(back_populates="subcategories")
    custom_fields: Mapped[list["TicketCustomField"]] = relationship(
        back_populates="subcategory",
        cascade="all, delete-orphan",
    )
