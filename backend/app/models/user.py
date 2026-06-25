from sqlalchemy import Boolean, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.enums import UserRole


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role", native_enum=False),
        nullable=False,
    )
    unit_id: Mapped[int | None] = mapped_column(
        ForeignKey("units.id", ondelete="SET NULL"),
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )

    unit: Mapped["Unit | None"] = relationship(back_populates="users")
    opened_tickets: Mapped[list["Ticket"]] = relationship(
        back_populates="opened_by_user",
        foreign_keys="Ticket.opened_by_user_id",
    )
    assigned_tickets: Mapped[list["Ticket"]] = relationship(
        back_populates="assigned_to_user",
        foreign_keys="Ticket.assigned_to_user_id",
    )
    ticket_history_entries: Mapped[list["TicketHistory"]] = relationship(
        back_populates="user",
    )
    uploaded_attachments: Mapped[list["TicketAttachment"]] = relationship(
        back_populates="uploaded_by_user",
    )
    requested_approvals: Mapped[list["Approval"]] = relationship(
        back_populates="requested_by_user",
        foreign_keys="Approval.requested_by_user_id",
    )
    approved_approvals: Mapped[list["Approval"]] = relationship(
        back_populates="approved_by_user",
        foreign_keys="Approval.approved_by_user_id",
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship(  # type: ignore[name-defined]
        back_populates="actor",
        foreign_keys="AuditLog.actor_user_id",
    )
