from decimal import Decimal

from sqlalchemy import Boolean, Index, JSON, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class ApprovalLevel(TimestampMixin, Base):
    __tablename__ = "approval_levels"
    __table_args__ = (
        Index("ix_approval_levels_is_active", "is_active"),
        Index("ix_approval_levels_min_amount", "min_amount"),
        Index("ix_approval_levels_max_amount", "max_amount"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    min_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    max_amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    allowed_roles: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )

    approvals: Mapped[list["Approval"]] = relationship(back_populates="approval_level")
