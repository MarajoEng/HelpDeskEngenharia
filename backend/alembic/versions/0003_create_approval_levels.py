"""create approval levels

Revision ID: 0003
Revises: 0002
Create Date: 2026-06-25 17:30:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "approval_levels",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("min_amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("max_amount", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("allowed_roles", sa.JSON(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("min_amount >= 0", name=op.f("ck_approval_levels_min_amount_non_negative")),
        sa.CheckConstraint("max_amount is null or max_amount >= 0", name=op.f("ck_approval_levels_max_amount_non_negative")),
        sa.CheckConstraint(
            "max_amount is null or max_amount >= min_amount",
            name=op.f("ck_approval_levels_max_amount_gte_min_amount"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_approval_levels")),
    )
    op.create_index("ix_approval_levels_is_active", "approval_levels", ["is_active"], unique=False)
    op.create_index("ix_approval_levels_min_amount", "approval_levels", ["min_amount"], unique=False)
    op.create_index("ix_approval_levels_max_amount", "approval_levels", ["max_amount"], unique=False)

    with op.batch_alter_table("approvals") as batch_op:
        batch_op.add_column(sa.Column("approval_level_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            op.f("fk_approvals_approval_level_id_approval_levels"),
            "approval_levels",
            ["approval_level_id"],
            ["id"],
        )
        batch_op.create_index("ix_approvals_approval_level_id", ["approval_level_id"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("approvals") as batch_op:
        batch_op.drop_index("ix_approvals_approval_level_id")
        batch_op.drop_constraint(op.f("fk_approvals_approval_level_id_approval_levels"), type_="foreignkey")
        batch_op.drop_column("approval_level_id")

    op.drop_index("ix_approval_levels_max_amount", table_name="approval_levels")
    op.drop_index("ix_approval_levels_min_amount", table_name="approval_levels")
    op.drop_index("ix_approval_levels_is_active", table_name="approval_levels")
    op.drop_table("approval_levels")
