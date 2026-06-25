from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, CreatedAtMixin
from app.models.enums import ApprovalStatus


class Approval(CreatedAtMixin, Base):
    __tablename__ = "approvals"
    __table_args__ = (
        Index("ix_approvals_ticket_id", "ticket_id"),
        Index("ix_approvals_status", "status"),
        Index("ix_approvals_approval_level_id", "approval_level_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False)
    approval_level_id: Mapped[int | None] = mapped_column(ForeignKey("approval_levels.id"), nullable=True)
    requested_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    approved_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    status: Mapped[ApprovalStatus] = mapped_column(
        Enum(
            ApprovalStatus,
            name="approval_status",
            native_enum=False,
            create_constraint=True,
            length=50,
        ),
        nullable=False,
    )
    amount_requested: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    amount_approved: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    justification: Mapped[str] = mapped_column(Text, nullable=False)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    ticket: Mapped["Ticket"] = relationship(back_populates="approvals")
    approval_level: Mapped["ApprovalLevel | None"] = relationship(back_populates="approvals")
    requested_by_user: Mapped["User"] = relationship(
        back_populates="requested_approvals",
        foreign_keys=[requested_by_user_id],
    )
    approved_by_user: Mapped["User | None"] = relationship(
        back_populates="approved_approvals",
        foreign_keys=[approved_by_user_id],
    )
