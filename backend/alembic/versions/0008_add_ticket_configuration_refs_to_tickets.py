"""add ticket configuration references to tickets

Revision ID: 0008
Revises: 0007
Create Date: 2026-06-26 00:30:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("ticket_categories") as batch_op:
        batch_op.add_column(sa.Column("legacy_value", sa.String(length=50), nullable=True))

    with op.batch_alter_table("ticket_priorities") as batch_op:
        batch_op.add_column(sa.Column("legacy_value", sa.String(length=50), nullable=True))

    with op.batch_alter_table("tickets") as batch_op:
        batch_op.add_column(sa.Column("category_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("subcategory_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("type_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("priority_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            op.f("fk_tickets_category_id_ticket_categories"),
            "ticket_categories",
            ["category_id"],
            ["id"],
        )
        batch_op.create_foreign_key(
            op.f("fk_tickets_subcategory_id_ticket_subcategories"),
            "ticket_subcategories",
            ["subcategory_id"],
            ["id"],
        )
        batch_op.create_foreign_key(
            op.f("fk_tickets_type_id_ticket_types"),
            "ticket_types",
            ["type_id"],
            ["id"],
        )
        batch_op.create_foreign_key(
            op.f("fk_tickets_priority_id_ticket_priorities"),
            "ticket_priorities",
            ["priority_id"],
            ["id"],
        )
        batch_op.create_index("ix_tickets_category_id", ["category_id"], unique=False)
        batch_op.create_index("ix_tickets_subcategory_id", ["subcategory_id"], unique=False)
        batch_op.create_index("ix_tickets_type_id", ["type_id"], unique=False)
        batch_op.create_index("ix_tickets_priority_id", ["priority_id"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("tickets") as batch_op:
        batch_op.drop_index("ix_tickets_priority_id")
        batch_op.drop_index("ix_tickets_type_id")
        batch_op.drop_index("ix_tickets_subcategory_id")
        batch_op.drop_index("ix_tickets_category_id")
        batch_op.drop_constraint(op.f("fk_tickets_priority_id_ticket_priorities"), type_="foreignkey")
        batch_op.drop_constraint(op.f("fk_tickets_type_id_ticket_types"), type_="foreignkey")
        batch_op.drop_constraint(op.f("fk_tickets_subcategory_id_ticket_subcategories"), type_="foreignkey")
        batch_op.drop_constraint(op.f("fk_tickets_category_id_ticket_categories"), type_="foreignkey")
        batch_op.drop_column("priority_id")
        batch_op.drop_column("type_id")
        batch_op.drop_column("subcategory_id")
        batch_op.drop_column("category_id")

    with op.batch_alter_table("ticket_priorities") as batch_op:
        batch_op.drop_column("legacy_value")

    with op.batch_alter_table("ticket_categories") as batch_op:
        batch_op.drop_column("legacy_value")
