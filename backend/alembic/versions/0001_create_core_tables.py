"""create core tables

Revision ID: 0001
Revises:
Create Date: 2026-06-25 09:30:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

user_role_enum = sa.Enum(
    "admin",
    "manager",
    "engineering",
    "director",
    "supplier",
    name="user_role",
    native_enum=False,
)

ticket_status_enum = sa.Enum(
    "open",
    "triage",
    "waiting_approval",
    "approved",
    "rejected",
    "in_progress",
    "waiting_supplier",
    "waiting_unit",
    "resolved",
    "closed",
    "canceled",
    name="ticket_status",
    native_enum=False,
)

ticket_category_enum = sa.Enum(
    "fuel_pump",
    "fuel_nozzle",
    "electrical",
    "plumbing",
    "leak",
    "structure",
    "roof",
    "pavement",
    "environmental_risk",
    "other",
    name="ticket_category",
    native_enum=False,
)

priority_level_enum = sa.Enum(
    "low",
    "medium",
    "high",
    "critical",
    name="priority_level",
    native_enum=False,
)


def upgrade() -> None:
    op.create_table(
        "suppliers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("document", sa.String(length=50), nullable=False),
        sa.Column("phone", sa.String(length=50), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("specialty", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_suppliers")),
    )

    op.create_table(
        "units",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("city", sa.String(length=120), nullable=False),
        sa.Column("state", sa.String(length=2), nullable=False),
        sa.Column("region", sa.String(length=120), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_units")),
        sa.UniqueConstraint("code", name=op.f("uq_units_code")),
    )

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", user_role_enum, nullable=False),
        sa.Column("unit_id", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["unit_id"], ["units.id"], name=op.f("fk_users_unit_id_units"), ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        sa.UniqueConstraint("email", name=op.f("uq_users_email")),
    )

    op.create_table(
        "tickets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("ticket_number", sa.String(length=50), nullable=False),
        sa.Column("unit_id", sa.Integer(), nullable=False),
        sa.Column("opened_by_user_id", sa.Integer(), nullable=False),
        sa.Column("assigned_to_user_id", sa.Integer(), nullable=True),
        sa.Column("category", ticket_category_enum, nullable=False),
        sa.Column("problem_type", sa.String(length=255), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("priority", priority_level_enum, nullable=False),
        sa.Column("severity", sa.String(length=50), nullable=False),
        sa.Column("status", ticket_status_enum, server_default="open", nullable=False),
        sa.Column("operational_impact", sa.Text(), nullable=True),
        sa.Column("fuel_nozzles_stopped", sa.Integer(), nullable=True),
        sa.Column("estimated_daily_loss", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("estimated_cost", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("approved_cost", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("final_cost", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("requires_approval", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("opened_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("triaged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sla_due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["assigned_to_user_id"], ["users.id"], name=op.f("fk_tickets_assigned_to_user_id_users")),
        sa.ForeignKeyConstraint(["opened_by_user_id"], ["users.id"], name=op.f("fk_tickets_opened_by_user_id_users")),
        sa.ForeignKeyConstraint(["unit_id"], ["units.id"], name=op.f("fk_tickets_unit_id_units")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_tickets")),
        sa.UniqueConstraint("ticket_number", name=op.f("uq_tickets_ticket_number")),
    )
    op.create_index("ix_tickets_unit_id", "tickets", ["unit_id"], unique=False)
    op.create_index("ix_tickets_status", "tickets", ["status"], unique=False)
    op.create_index("ix_tickets_priority", "tickets", ["priority"], unique=False)
    op.create_index("ix_tickets_severity", "tickets", ["severity"], unique=False)
    op.create_index("ix_tickets_category", "tickets", ["category"], unique=False)
    op.create_index("ix_tickets_opened_at", "tickets", ["opened_at"], unique=False)
    op.create_index("ix_tickets_closed_at", "tickets", ["closed_at"], unique=False)
    op.create_index("ix_tickets_sla_due_at", "tickets", ["sla_due_at"], unique=False)
    op.create_index("ix_tickets_requires_approval", "tickets", ["requires_approval"], unique=False)

    op.create_table(
        "approvals",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("ticket_id", sa.Integer(), nullable=False),
        sa.Column("requested_by_user_id", sa.Integer(), nullable=False),
        sa.Column("approved_by_user_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("amount_requested", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("amount_approved", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("justification", sa.Text(), nullable=False),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["approved_by_user_id"], ["users.id"], name=op.f("fk_approvals_approved_by_user_id_users")),
        sa.ForeignKeyConstraint(["requested_by_user_id"], ["users.id"], name=op.f("fk_approvals_requested_by_user_id_users")),
        sa.ForeignKeyConstraint(["ticket_id"], ["tickets.id"], name=op.f("fk_approvals_ticket_id_tickets"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_approvals")),
    )
    op.create_index("ix_approvals_ticket_id", "approvals", ["ticket_id"], unique=False)
    op.create_index("ix_approvals_status", "approvals", ["status"], unique=False)

    op.create_table(
        "ticket_attachments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("ticket_id", sa.Integer(), nullable=False),
        sa.Column("uploaded_by_user_id", sa.Integer(), nullable=False),
        sa.Column("file_url", sa.Text(), nullable=False),
        sa.Column("file_type", sa.String(length=100), nullable=False),
        sa.Column("attachment_type", sa.String(length=100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["ticket_id"], ["tickets.id"], name=op.f("fk_ticket_attachments_ticket_id_tickets"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["uploaded_by_user_id"], ["users.id"], name=op.f("fk_ticket_attachments_uploaded_by_user_id_users")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ticket_attachments")),
    )

    op.create_table(
        "ticket_history",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("ticket_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("old_status", ticket_status_enum, nullable=True),
        sa.Column("new_status", ticket_status_enum, nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["ticket_id"], ["tickets.id"], name=op.f("fk_ticket_history_ticket_id_tickets"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_ticket_history_user_id_users")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ticket_history")),
    )
    op.create_index("ix_ticket_history_ticket_id", "ticket_history", ["ticket_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_ticket_history_ticket_id", table_name="ticket_history")
    op.drop_table("ticket_history")
    op.drop_table("ticket_attachments")
    op.drop_index("ix_approvals_status", table_name="approvals")
    op.drop_index("ix_approvals_ticket_id", table_name="approvals")
    op.drop_table("approvals")
    op.drop_index("ix_tickets_requires_approval", table_name="tickets")
    op.drop_index("ix_tickets_sla_due_at", table_name="tickets")
    op.drop_index("ix_tickets_closed_at", table_name="tickets")
    op.drop_index("ix_tickets_opened_at", table_name="tickets")
    op.drop_index("ix_tickets_category", table_name="tickets")
    op.drop_index("ix_tickets_severity", table_name="tickets")
    op.drop_index("ix_tickets_priority", table_name="tickets")
    op.drop_index("ix_tickets_status", table_name="tickets")
    op.drop_index("ix_tickets_unit_id", table_name="tickets")
    op.drop_table("tickets")
    op.drop_table("users")
    op.drop_table("units")
    op.drop_table("suppliers")
