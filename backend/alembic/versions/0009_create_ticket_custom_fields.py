"""create ticket custom fields

Revision ID: 0009
Revises: 0008
Create Date: 2026-06-26 01:00:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ticket_custom_fields",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.Column("subcategory_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("label", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("field_type", sa.String(length=30), nullable=False),
        sa.Column("is_required", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("display_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("placeholder", sa.String(length=255), nullable=True),
        sa.Column("help_text", sa.Text(), nullable=True),
        sa.Column("validation_json", sa.JSON(), nullable=True),
        sa.Column("options_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["category_id"], ["ticket_categories.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["subcategory_id"], ["ticket_subcategories.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("category_id", "subcategory_id", "name", name="uq_ticket_custom_fields_scope_name"),
    )
    op.create_index("ix_ticket_custom_fields_category_id", "ticket_custom_fields", ["category_id"], unique=False)
    op.create_index("ix_ticket_custom_fields_subcategory_id", "ticket_custom_fields", ["subcategory_id"], unique=False)
    op.create_index("ix_ticket_custom_fields_is_active", "ticket_custom_fields", ["is_active"], unique=False)
    op.create_index("ix_ticket_custom_fields_display_order", "ticket_custom_fields", ["display_order"], unique=False)

    op.create_table(
        "ticket_custom_field_values",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("ticket_id", sa.Integer(), nullable=False),
        sa.Column("custom_field_id", sa.Integer(), nullable=False),
        sa.Column("value_text", sa.Text(), nullable=True),
        sa.Column("value_number", sa.Numeric(12, 2), nullable=True),
        sa.Column("value_boolean", sa.Boolean(), nullable=True),
        sa.Column("value_date", sa.Date(), nullable=True),
        sa.Column("value_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["custom_field_id"], ["ticket_custom_fields.id"]),
        sa.ForeignKeyConstraint(["ticket_id"], ["tickets.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("ticket_id", "custom_field_id", name="uq_ticket_custom_field_values_ticket_field"),
    )
    op.create_index("ix_ticket_custom_field_values_ticket_id", "ticket_custom_field_values", ["ticket_id"], unique=False)
    op.create_index(
        "ix_ticket_custom_field_values_custom_field_id",
        "ticket_custom_field_values",
        ["custom_field_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_ticket_custom_field_values_custom_field_id", table_name="ticket_custom_field_values")
    op.drop_index("ix_ticket_custom_field_values_ticket_id", table_name="ticket_custom_field_values")
    op.drop_table("ticket_custom_field_values")
    op.drop_index("ix_ticket_custom_fields_display_order", table_name="ticket_custom_fields")
    op.drop_index("ix_ticket_custom_fields_is_active", table_name="ticket_custom_fields")
    op.drop_index("ix_ticket_custom_fields_subcategory_id", table_name="ticket_custom_fields")
    op.drop_index("ix_ticket_custom_fields_category_id", table_name="ticket_custom_fields")
    op.drop_table("ticket_custom_fields")
