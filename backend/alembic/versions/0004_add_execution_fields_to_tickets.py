"""add supplier_id and expected_resolution_at to tickets

Revision ID: 0004
Revises: 0003
Create Date: 2026-06-25 18:00:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("tickets") as batch_op:
        batch_op.add_column(sa.Column("supplier_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("expected_resolution_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.create_foreign_key(
            op.f("fk_tickets_supplier_id_suppliers"),
            "suppliers",
            ["supplier_id"],
            ["id"],
        )
        batch_op.create_index("ix_tickets_supplier_id", ["supplier_id"], unique=False)
        batch_op.create_index("ix_tickets_expected_resolution_at", ["expected_resolution_at"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("tickets") as batch_op:
        batch_op.drop_index("ix_tickets_expected_resolution_at")
        batch_op.drop_index("ix_tickets_supplier_id")
        batch_op.drop_constraint(op.f("fk_tickets_supplier_id_suppliers"), type_="foreignkey")
        batch_op.drop_column("expected_resolution_at")
        batch_op.drop_column("supplier_id")
