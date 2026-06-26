"""create ticket status workflow

Revision ID: 0010
Revises: 0009
Create Date: 2026-06-26 11:00:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


STATUS_SEED = [
    ("Aberto", "open", "Chamado aberto aguardando triagem.", "#2563eb", True, False, False, False, True, 10),
    ("Triagem", "triage", "Chamado em análise técnica.", "#7c3aed", False, False, False, False, True, 20),
    ("Aguardando aprovação", "waiting_approval", "Chamado aguardando aprovação.", "#d97706", False, False, True, False, True, 30),
    ("Aprovado", "approved", "Chamado aprovado para execução.", "#059669", False, False, False, False, True, 40),
    ("Rejeitado", "rejected", "Chamado rejeitado no fluxo de aprovação.", "#dc2626", False, True, False, True, True, 50),
    ("Em atendimento", "in_progress", "Chamado em execução.", "#0891b2", False, False, False, False, True, 60),
    ("Aguardando fornecedor", "waiting_supplier", "Chamado pausado aguardando fornecedor.", "#9333ea", False, False, True, False, True, 70),
    ("Aguardando unidade", "waiting_unit", "Chamado pausado aguardando unidade.", "#ca8a04", False, False, True, False, True, 80),
    ("Resolvido", "resolved", "Chamado resolvido aguardando fechamento.", "#16a34a", False, True, False, True, True, 90),
    ("Fechado", "closed", "Chamado fechado.", "#475569", False, True, False, False, True, 100),
    ("Cancelado", "canceled", "Chamado cancelado.", "#991b1b", False, True, False, True, True, 110),
]

TRANSITION_SEED = [
    ("open", "triage", True, False, ["admin", "engineering"]),
    ("waiting_unit", "triage", True, False, ["admin", "engineering"]),
    ("triage", "waiting_approval", True, False, ["admin", "engineering"]),
    ("triage", "in_progress", True, False, ["admin", "engineering"]),
    ("waiting_approval", "approved", True, False, None),
    ("waiting_approval", "rejected", True, False, None),
    ("approved", "in_progress", True, False, ["admin", "engineering"]),
    ("in_progress", "waiting_supplier", True, False, ["admin", "engineering"]),
    ("in_progress", "waiting_unit", True, False, ["admin", "engineering"]),
    ("waiting_supplier", "in_progress", True, False, ["admin", "engineering"]),
    ("waiting_unit", "in_progress", True, False, ["admin", "engineering"]),
    ("in_progress", "resolved", True, True, ["admin", "engineering"]),
    ("resolved", "closed", True, False, ["admin", "engineering"]),
    ("resolved", "in_progress", True, False, ["admin", "engineering"]),
    ("rejected", "triage", True, False, ["admin", "engineering"]),
    ("canceled", "triage", True, False, ["admin"]),
]


def upgrade() -> None:
    op.create_table(
        "ticket_statuses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("legacy_value", sa.String(length=50), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("color", sa.String(length=32), nullable=False),
        sa.Column("is_initial", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_final", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("pauses_sla", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("allows_reopen", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("display_order", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("name", name="uq_ticket_statuses_name"),
    )
    op.create_index("ix_ticket_statuses_legacy_value", "ticket_statuses", ["legacy_value"], unique=False)
    op.create_index("ix_ticket_statuses_is_active", "ticket_statuses", ["is_active"], unique=False)

    op.create_table(
        "ticket_status_transitions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("from_status_id", sa.Integer(), sa.ForeignKey("ticket_statuses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("to_status_id", sa.Integer(), sa.ForeignKey("ticket_statuses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("requires_comment", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("requires_attachment", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("allowed_roles_json", sa.JSON(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("from_status_id", "to_status_id", name="uq_ticket_status_transitions_from_to"),
    )
    op.create_index("ix_ticket_status_transitions_from_status_id", "ticket_status_transitions", ["from_status_id"], unique=False)
    op.create_index("ix_ticket_status_transitions_to_status_id", "ticket_status_transitions", ["to_status_id"], unique=False)
    op.create_index("ix_ticket_status_transitions_is_active", "ticket_status_transitions", ["is_active"], unique=False)

    with op.batch_alter_table("tickets") as batch_op:
        batch_op.add_column(sa.Column("status_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            op.f("fk_tickets_status_id_ticket_statuses"),
            "ticket_statuses",
            ["status_id"],
            ["id"],
        )
        batch_op.create_index("ix_tickets_status_id", ["status_id"], unique=False)

    connection = op.get_bind()
    statuses = sa.table(
        "ticket_statuses",
        sa.column("id", sa.Integer),
        sa.column("name", sa.String),
        sa.column("legacy_value", sa.String),
        sa.column("description", sa.Text),
        sa.column("color", sa.String),
        sa.column("is_initial", sa.Boolean),
        sa.column("is_final", sa.Boolean),
        sa.column("pauses_sla", sa.Boolean),
        sa.column("allows_reopen", sa.Boolean),
        sa.column("is_active", sa.Boolean),
        sa.column("display_order", sa.Integer),
    )
    transitions = sa.table(
        "ticket_status_transitions",
        sa.column("from_status_id", sa.Integer),
        sa.column("to_status_id", sa.Integer),
        sa.column("requires_comment", sa.Boolean),
        sa.column("requires_attachment", sa.Boolean),
        sa.column("allowed_roles_json", sa.JSON),
        sa.column("is_active", sa.Boolean),
    )

    for item in STATUS_SEED:
        name, legacy_value, description, color, is_initial, is_final, pauses_sla, allows_reopen, is_active, display_order = item
        existing_id = connection.scalar(
            sa.select(statuses.c.id).where(statuses.c.legacy_value == legacy_value).limit(1)
        )
        if existing_id is None:
            connection.execute(
                statuses.insert().values(
                    name=name,
                    legacy_value=legacy_value,
                    description=description,
                    color=color,
                    is_initial=is_initial,
                    is_final=is_final,
                    pauses_sla=pauses_sla,
                    allows_reopen=allows_reopen,
                    is_active=is_active,
                    display_order=display_order,
                )
            )

    status_ids = {
        legacy: status_id
        for legacy, status_id in connection.execute(sa.select(statuses.c.legacy_value, statuses.c.id)).all()
        if legacy is not None
    }
    for from_legacy, to_legacy, requires_comment, requires_attachment, allowed_roles in TRANSITION_SEED:
        from_id = status_ids.get(from_legacy)
        to_id = status_ids.get(to_legacy)
        if from_id is None or to_id is None:
            continue
        exists = connection.scalar(
            sa.select(transitions.c.from_status_id)
            .where(transitions.c.from_status_id == from_id, transitions.c.to_status_id == to_id)
            .limit(1)
        )
        if exists is None:
            connection.execute(
                transitions.insert().values(
                    from_status_id=from_id,
                    to_status_id=to_id,
                    requires_comment=requires_comment,
                    requires_attachment=requires_attachment,
                    allowed_roles_json=allowed_roles,
                    is_active=True,
                )
            )

    tickets = sa.table("tickets", sa.column("status", sa.String), sa.column("status_id", sa.Integer))
    for legacy, status_id in status_ids.items():
        connection.execute(tickets.update().where(tickets.c.status == legacy).values(status_id=status_id))


def downgrade() -> None:
    with op.batch_alter_table("tickets") as batch_op:
        batch_op.drop_index("ix_tickets_status_id")
        batch_op.drop_constraint(op.f("fk_tickets_status_id_ticket_statuses"), type_="foreignkey")
        batch_op.drop_column("status_id")

    op.drop_index("ix_ticket_status_transitions_is_active", table_name="ticket_status_transitions")
    op.drop_index("ix_ticket_status_transitions_to_status_id", table_name="ticket_status_transitions")
    op.drop_index("ix_ticket_status_transitions_from_status_id", table_name="ticket_status_transitions")
    op.drop_table("ticket_status_transitions")

    op.drop_index("ix_ticket_statuses_is_active", table_name="ticket_statuses")
    op.drop_index("ix_ticket_statuses_legacy_value", table_name="ticket_statuses")
    op.drop_table("ticket_statuses")
