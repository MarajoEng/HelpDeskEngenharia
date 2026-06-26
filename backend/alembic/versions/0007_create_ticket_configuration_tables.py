"""create ticket configuration tables

Revision ID: 0007
Revises: 0006
Create Date: 2026-06-25 23:00:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ticket_categories",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("display_order", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("requires_attachment", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("requires_location", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_ticket_categories_is_active", "ticket_categories", ["is_active"])
    op.create_index("ix_ticket_categories_display_order", "ticket_categories", ["display_order"])

    op.create_table(
        "ticket_types",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("display_order", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_ticket_types_is_active", "ticket_types", ["is_active"])
    op.create_index("ix_ticket_types_display_order", "ticket_types", ["display_order"])

    op.create_table(
        "ticket_priorities",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("color", sa.String(length=32), nullable=False),
        sa.Column("weight", sa.Integer(), nullable=False),
        sa.Column("sla_hours", sa.Integer(), nullable=False),
        sa.Column("requires_reason", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("display_order", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_ticket_priorities_is_active", "ticket_priorities", ["is_active"])
    op.create_index("ix_ticket_priorities_display_order", "ticket_priorities", ["display_order"])
    op.create_index("ix_ticket_priorities_weight", "ticket_priorities", ["weight"])

    op.create_table(
        "ticket_category_types",
        sa.Column("category_id", sa.Integer(), sa.ForeignKey("ticket_categories.id", ondelete="CASCADE"), nullable=False),
        sa.Column("type_id", sa.Integer(), sa.ForeignKey("ticket_types.id", ondelete="CASCADE"), nullable=False),
        sa.PrimaryKeyConstraint("category_id", "type_id"),
    )

    op.create_table(
        "ticket_subcategories",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("category_id", sa.Integer(), sa.ForeignKey("ticket_categories.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("display_order", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("category_id", "name"),
    )
    op.create_index("ix_ticket_subcategories_category_id", "ticket_subcategories", ["category_id"])
    op.create_index("ix_ticket_subcategories_is_active", "ticket_subcategories", ["is_active"])
    op.create_index("ix_ticket_subcategories_display_order", "ticket_subcategories", ["display_order"])


def downgrade() -> None:
    op.drop_index("ix_ticket_subcategories_display_order", table_name="ticket_subcategories")
    op.drop_index("ix_ticket_subcategories_is_active", table_name="ticket_subcategories")
    op.drop_index("ix_ticket_subcategories_category_id", table_name="ticket_subcategories")
    op.drop_table("ticket_subcategories")

    op.drop_table("ticket_category_types")

    op.drop_index("ix_ticket_priorities_weight", table_name="ticket_priorities")
    op.drop_index("ix_ticket_priorities_display_order", table_name="ticket_priorities")
    op.drop_index("ix_ticket_priorities_is_active", table_name="ticket_priorities")
    op.drop_table("ticket_priorities")

    op.drop_index("ix_ticket_types_display_order", table_name="ticket_types")
    op.drop_index("ix_ticket_types_is_active", table_name="ticket_types")
    op.drop_table("ticket_types")

    op.drop_index("ix_ticket_categories_display_order", table_name="ticket_categories")
    op.drop_index("ix_ticket_categories_is_active", table_name="ticket_categories")
    op.drop_table("ticket_categories")
