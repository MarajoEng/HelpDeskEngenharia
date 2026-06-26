"""add group_code and branch_code to units

Revision ID: 0011
Revises: 0010
Create Date: 2026-06-26 12:00:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("units", sa.Column("group_code", sa.String(20), nullable=True))
    op.add_column("units", sa.Column("branch_code", sa.String(20), nullable=True))


def downgrade() -> None:
    op.drop_column("units", "branch_code")
    op.drop_column("units", "group_code")
