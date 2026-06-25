"""add contract enums

Revision ID: 0002
Revises: 0001
Create Date: 2026-06-25 11:10:00
"""

from __future__ import annotations

from alembic import op


revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("tickets") as batch_op:
        batch_op.create_check_constraint(
            "ticket_severity",
            "severity in ('low', 'medium', 'high', 'critical')",
        )

    with op.batch_alter_table("approvals") as batch_op:
        batch_op.create_check_constraint(
            "approval_status",
            "status in ('pending', 'approved', 'rejected', 'canceled')",
        )


def downgrade() -> None:
    with op.batch_alter_table("approvals") as batch_op:
        batch_op.drop_constraint("ck_approvals_approval_status", type_="check")

    with op.batch_alter_table("tickets") as batch_op:
        batch_op.drop_constraint("ck_tickets_ticket_severity", type_="check")
