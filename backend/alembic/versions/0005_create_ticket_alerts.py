"""create ticket_alerts table

Revision ID: 0005
Revises: 0004
Create Date: 2026-06-25 20:00:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ticket_alerts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("ticket_id", sa.Integer(), sa.ForeignKey("tickets.id"), nullable=False),
        sa.Column("alert_type", sa.String(50), nullable=False),
        sa.Column("severity", sa.String(50), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_by_system", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_ticket_alerts_ticket_id", "ticket_alerts", ["ticket_id"])
    op.create_index("ix_ticket_alerts_alert_type", "ticket_alerts", ["alert_type"])
    op.create_index("ix_ticket_alerts_is_read", "ticket_alerts", ["is_read"])
    op.create_index("ix_ticket_alerts_created_at", "ticket_alerts", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_ticket_alerts_created_at", table_name="ticket_alerts")
    op.drop_index("ix_ticket_alerts_is_read", table_name="ticket_alerts")
    op.drop_index("ix_ticket_alerts_alert_type", table_name="ticket_alerts")
    op.drop_index("ix_ticket_alerts_ticket_id", table_name="ticket_alerts")
    op.drop_table("ticket_alerts")
