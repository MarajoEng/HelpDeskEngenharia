from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class TicketCategoryTypeLink(Base):
    __tablename__ = "ticket_category_types"

    category_id: Mapped[int] = mapped_column(
        ForeignKey("ticket_categories.id", ondelete="CASCADE"),
        primary_key=True,
    )
    type_id: Mapped[int] = mapped_column(
        ForeignKey("ticket_types.id", ondelete="CASCADE"),
        primary_key=True,
    )

    category: Mapped["TicketCategoryConfig"] = relationship(back_populates="category_types")
    ticket_type: Mapped["TicketTypeConfig"] = relationship(back_populates="category_types")
