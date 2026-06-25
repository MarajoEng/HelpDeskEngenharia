from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, CreatedAtMixin


class TicketAttachment(CreatedAtMixin, Base):
    __tablename__ = "ticket_attachments"

    id: Mapped[int] = mapped_column(primary_key=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False)
    uploaded_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    file_url: Mapped[str] = mapped_column(Text, nullable=False)
    file_type: Mapped[str] = mapped_column(String(100), nullable=False)
    attachment_type: Mapped[str] = mapped_column(String(100), nullable=False)

    ticket: Mapped["Ticket"] = relationship(back_populates="attachments")
    uploaded_by_user: Mapped["User"] = relationship(back_populates="uploaded_attachments")
