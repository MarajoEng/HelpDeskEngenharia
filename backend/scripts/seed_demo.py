from __future__ import annotations

import sys
from datetime import datetime, timedelta, UTC
from decimal import Decimal
from enum import Enum
from pathlib import Path
from types import SimpleNamespace

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from sqlalchemy import select, text

from app.core.config import get_settings
from app.core.database import get_session_factory
from app.core.security import hash_password
from app.models.approval_level import ApprovalLevel
from app.models.enums import AlertSeverity, AlertType, ApprovalStatus, PriorityLevel, TicketCategory, TicketSeverity, TicketStatus, UserRole
from app.models.supplier import Supplier
from app.models.unit import Unit
from app.services.ticket_configuration_seed import seed_ticket_configurations


def _sql_params(**values):
    normalized = {}
    for key, value in values.items():
        if isinstance(value, Decimal):
            normalized[key] = str(value)
        else:
            normalized[key] = value
    return normalized


def _enum_storage_value(session, enum_cls: type[Enum], value):
    if value is None:
        return None
    if isinstance(value, enum_cls):
        return value.value
    return value


def seed_approval_levels(session) -> list[ApprovalLevel]:
    levels_data = [
        {
            "name": "Engenharia ate 1000",
            "min_amount": Decimal("0.00"),
            "max_amount": Decimal("1000.00"),
            "allowed_roles": [UserRole.ENGINEERING.value, UserRole.ADMIN.value],
        },
        {
            "name": "Diretoria ate 5000",
            "min_amount": Decimal("1000.01"),
            "max_amount": Decimal("5000.00"),
            "allowed_roles": [UserRole.DIRECTOR.value, UserRole.ADMIN.value],
        },
        {
            "name": "Alta alcada acima de 5000",
            "min_amount": Decimal("5000.01"),
            "max_amount": None,
            "allowed_roles": [UserRole.ADMIN.value],
        },
    ]

    levels = []
    for data in levels_data:
        stmt = select(ApprovalLevel).where(ApprovalLevel.name == data["name"])
        level = session.scalar(stmt)
        if not level:
            level = ApprovalLevel(**data, is_active=True)
            session.add(level)
            session.flush()
        else:
            level.min_amount = data["min_amount"]
            level.max_amount = data["max_amount"]
            level.allowed_roles = data["allowed_roles"]
            level.is_active = True
        levels.append(level)
    return levels


def seed_units(session) -> list[Unit]:
    units_data = [
        {"code": "0101", "name": "Posto Central SP", "city": "São Paulo", "state": "SP", "region": "Sudeste"},
        {"code": "0201", "name": "Posto Bandeirantes", "city": "Campinas", "state": "SP", "region": "Sudeste"},
        {"code": "0301", "name": "Posto Dutra RJ", "city": "Rio de Janeiro", "state": "RJ", "region": "Sudeste"},
        {"code": "0401", "name": "Posto Linha Amarela", "city": "Rio de Janeiro", "state": "RJ", "region": "Sudeste"},
        {"code": "0501", "name": "Posto Pampulha", "city": "Belo Horizonte", "state": "MG", "region": "Sudeste"},
        {"code": "0601", "name": "Posto Contorno", "city": "Contagem", "state": "MG", "region": "Sudeste"},
        {"code": "0701", "name": "Posto BR116 Sul", "city": "Curitiba", "state": "PR", "region": "Sul"},
        {"code": "0801", "name": "Posto Imigrantes", "city": "São Bernardo do Campo", "state": "SP", "region": "Sudeste"},
        {"code": "0901", "name": "Posto Aeroporto", "city": "Guarulhos", "state": "SP", "region": "Sudeste"},
        {"code": "1001", "name": "Posto Via Lagos", "city": "Cabo Frio", "state": "RJ", "region": "Sudeste"},
    ]

    units = []
    for data in units_data:
        stmt = select(Unit).where(Unit.code == data["code"])
        unit = session.scalar(stmt)
        if not unit:
            unit = Unit(**data, is_active=True)
            session.add(unit)
            session.flush()
        else:
            for k, v in data.items():
                setattr(unit, k, v)
        units.append(unit)
    return units


def _fetch_seeded_user(session, email: str) -> SimpleNamespace | None:
    row = session.execute(
        text(
            """
            SELECT id, name, email, role, unit_id
            FROM users
            WHERE email = :email
            """
        ),
        {"email": email},
    ).mappings().first()
    return SimpleNamespace(**row) if row else None


def seed_users(session, units) -> list[SimpleNamespace]:
    users_data = [
        {"name": "Admin", "email": "admin@local.test", "role": UserRole.ADMIN.value, "unit_id": None},
        {"name": "Engenharia", "email": "engenharia@local.test", "role": UserRole.ENGINEERING.value, "unit_id": None},
        {"name": "Diretor", "email": "diretor@local.test", "role": UserRole.DIRECTOR.value, "unit_id": None},
        {"name": "Gerente SP", "email": "gerente0101@local.test", "role": UserRole.MANAGER.value, "unit_id": units[0].id},
        {"name": "Gerente Campinas", "email": "gerente0201@local.test", "role": UserRole.MANAGER.value, "unit_id": units[1].id},
    ]

    users = []
    password_hash = hash_password("admin123")
    for data in users_data:
        user = _fetch_seeded_user(session, data["email"])
        user_params = dict(data)
        user_params["role"] = _enum_storage_value(session, UserRole, data["role"])
        if not user:
            session.execute(
                text(
                    """
                    INSERT INTO users (name, email, password_hash, role, unit_id, is_active)
                    VALUES (:name, :email, :password_hash, :role, :unit_id, :is_active)
                    """
                ),
                _sql_params(**user_params, password_hash=password_hash, is_active=True),
            )
            session.flush()
        else:
            session.execute(
                text(
                    """
                    UPDATE users
                    SET name = :name,
                        password_hash = :password_hash,
                        role = :role,
                        unit_id = :unit_id,
                        is_active = :is_active,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = :id
                    """
                ),
                _sql_params(
                    id=user.id,
                    **user_params,
                    password_hash=password_hash,
                    is_active=True,
                ),
            )
            session.flush()
        user = _fetch_seeded_user(session, data["email"])
        if not user:
            raise RuntimeError(f"Failed to upsert seeded user {data['email']}.")
        users.append(user)
    return users


def seed_suppliers(session) -> list[Supplier]:
    suppliers_data = [
        {"name": "Eletrica Central", "document": "11111111000111", "phone": "11999999999", "email": "contato@eletricacentral.test", "specialty": "elétrica"},
        {"name": "Hidraulica Cano Rápido", "document": "22222222000122", "phone": "11988888888", "email": "contato@canorapido.test", "specialty": "hidráulica"},
        {"name": "Bombas Sul", "document": "33333333000133", "phone": "11977777777", "email": "contato@bombassul.test", "specialty": "bombas"},
        {"name": "Coberturas Norte", "document": "44444444000144", "phone": "11966666666", "email": "contato@coberturasnorte.test", "specialty": "cobertura"},
        {"name": "Pavimentação Forte", "document": "55555555000155", "phone": "11955555555", "email": "contato@pavimentacaoforte.test", "specialty": "pavimentação"},
    ]

    suppliers = []
    for data in suppliers_data:
        stmt = select(Supplier).where(Supplier.document == data["document"])
        supplier = session.scalar(stmt)
        if not supplier:
            supplier = Supplier(**data, is_active=True)
            session.add(supplier)
            session.flush()
        else:
            for k, v in data.items():
                setattr(supplier, k, v)
        suppliers.append(supplier)
    return suppliers


def seed_ticket_configuration(session):
    return seed_ticket_configurations(session)


def _create_ticket_with_history(session, ticket_data, user_id):
    ticket_row = session.execute(
        text(
            """
            SELECT id, ticket_number
            FROM tickets
            WHERE ticket_number = :ticket_number
            """
        ),
        {"ticket_number": ticket_data["ticket_number"]},
    ).mappings().first()
    if ticket_row:
        # Already seeded
        return SimpleNamespace(**ticket_row)

    ticket_insert_params = {
        "assigned_to_user_id": None,
        "operational_impact": None,
        "fuel_nozzles_stopped": None,
        "estimated_daily_loss": None,
        "estimated_cost": None,
        "approved_cost": None,
        "final_cost": None,
        "requires_approval": False,
        "triaged_at": None,
        "approved_at": None,
        "started_at": None,
        "resolved_at": None,
        "closed_at": None,
        "sla_due_at": None,
        "expected_resolution_at": None,
        "supplier_id": None,
    }
    ticket_insert_params.update(ticket_data)
    ticket_insert_params["category"] = _enum_storage_value(session, TicketCategory, ticket_insert_params["category"])
    ticket_insert_params["priority"] = _enum_storage_value(session, PriorityLevel, ticket_insert_params["priority"])
    ticket_insert_params["severity"] = _enum_storage_value(session, TicketSeverity, ticket_insert_params["severity"])
    ticket_insert_params["status"] = _enum_storage_value(session, TicketStatus, ticket_insert_params["status"])

    ticket_id = session.execute(
        text(
            """
            INSERT INTO tickets (
                ticket_number,
                unit_id,
                opened_by_user_id,
                assigned_to_user_id,
                category,
                problem_type,
                title,
                description,
                priority,
                severity,
                status,
                operational_impact,
                fuel_nozzles_stopped,
                estimated_daily_loss,
                estimated_cost,
                approved_cost,
                final_cost,
                requires_approval,
                opened_at,
                triaged_at,
                approved_at,
                started_at,
                resolved_at,
                closed_at,
                sla_due_at,
                expected_resolution_at,
                supplier_id
            )
            VALUES (
                :ticket_number,
                :unit_id,
                :opened_by_user_id,
                :assigned_to_user_id,
                :category,
                :problem_type,
                :title,
                :description,
                :priority,
                :severity,
                :status,
                :operational_impact,
                :fuel_nozzles_stopped,
                :estimated_daily_loss,
                :estimated_cost,
                :approved_cost,
                :final_cost,
                :requires_approval,
                :opened_at,
                :triaged_at,
                :approved_at,
                :started_at,
                :resolved_at,
                :closed_at,
                :sla_due_at,
                :expected_resolution_at,
                :supplier_id
            )
            RETURNING id
            """
        ),
        _sql_params(**ticket_insert_params),
    ).scalar_one()

    session.execute(
        text(
            """
            INSERT INTO ticket_history (ticket_id, user_id, old_status, new_status, comment)
            VALUES (:ticket_id, :user_id, :old_status, :new_status, :comment)
            """
        ),
        _sql_params(
            ticket_id=ticket_id,
            user_id=user_id,
            old_status=None,
            new_status=_enum_storage_value(session, TicketStatus, ticket_data["status"]),
            comment="Chamado criado pelo seed demo.",
        ),
    )
    session.flush()
    return SimpleNamespace(id=ticket_id, ticket_number=ticket_data["ticket_number"])


def seed_tickets(session, units, users, suppliers, levels):
    manager_sp = users[3]
    manager_campinas = users[4]
    eng = users[1]
    director = users[2]
    now = datetime.now(UTC)

    # 1. Open ticket
    _create_ticket_with_history(session, {
        "ticket_number": f"DEMO-{now.strftime('%Y%m%d')}-000001",
        "unit_id": units[0].id,
        "opened_by_user_id": manager_sp.id,
        "category": TicketCategory.FUEL_NOZZLE.value,
        "problem_type": "Bico parado",
        "title": "Bico de gasolina comum vazando",
        "description": "Bico 4 da bomba 2 está vazando quando abastece. Fechamos o bico.",
        "priority": PriorityLevel.HIGH.value,
        "severity": TicketSeverity.HIGH.value,
        "status": TicketStatus.OPEN.value,
        "fuel_nozzles_stopped": 1,
        "estimated_daily_loss": Decimal("800.00"),
        "opened_at": now - timedelta(hours=2),
    }, manager_sp.id)

    # 2. Triage ticket (with SLA due soon)
    _create_ticket_with_history(session, {
        "ticket_number": f"DEMO-{now.strftime('%Y%m%d')}-000002",
        "unit_id": units[1].id,
        "opened_by_user_id": manager_campinas.id,
        "category": TicketCategory.ELECTRICAL.value,
        "problem_type": "Curto circuito",
        "title": "Luzes da pista piscando",
        "description": "Metade das luzes da pista estão apagadas.",
        "priority": PriorityLevel.MEDIUM.value,
        "severity": TicketSeverity.MEDIUM.value,
        "status": TicketStatus.TRIAGE.value,
        "opened_at": now - timedelta(days=1),
        "triaged_at": now - timedelta(hours=12),
        "sla_due_at": now + timedelta(hours=2),
    }, manager_campinas.id)

    # 3. Waiting Approval (Engineering level)
    t3 = _create_ticket_with_history(session, {
        "ticket_number": f"DEMO-{now.strftime('%Y%m%d')}-000003",
        "unit_id": units[0].id,
        "opened_by_user_id": manager_sp.id,
        "category": TicketCategory.PLUMBING.value,
        "problem_type": "Vazamento no banheiro",
        "title": "Pia do banheiro quebrada",
        "description": "Cano da pia quebrou, água jorrando. Fechamos o registro.",
        "priority": PriorityLevel.MEDIUM.value,
        "severity": TicketSeverity.MEDIUM.value,
        "status": TicketStatus.WAITING_APPROVAL.value,
        "estimated_cost": Decimal("800.00"),
        "requires_approval": True,
        "opened_at": now - timedelta(days=2),
        "triaged_at": now - timedelta(days=1),
        "sla_due_at": now + timedelta(days=1),
        "supplier_id": suppliers[1].id,
    }, manager_sp.id)

    approval_t3_exists = session.execute(
        text("SELECT id FROM approvals WHERE ticket_id = :ticket_id"),
        {"ticket_id": t3.id},
    ).scalar()
    if not approval_t3_exists:
        session.execute(
            text(
                """
                INSERT INTO approvals (
                    ticket_id,
                    approval_level_id,
                    requested_by_user_id,
                    approved_by_user_id,
                    status,
                    amount_requested,
                    amount_approved,
                    justification,
                    approved_at
                )
                VALUES (
                    :ticket_id,
                    :approval_level_id,
                    :requested_by_user_id,
                    :approved_by_user_id,
                    :status,
                    :amount_requested,
                    :amount_approved,
                    :justification,
                    :approved_at
                )
                """
            ),
            _sql_params(
                ticket_id=t3.id,
                approval_level_id=levels[0].id,
                requested_by_user_id=eng.id,
                approved_by_user_id=None,
                status=_enum_storage_value(session, ApprovalStatus, ApprovalStatus.PENDING.value),
                amount_requested=Decimal("800.00"),
                amount_approved=None,
                justification="Orçamento do fornecedor para troca do cano.",
                approved_at=None,
            ),
        )

    # 4. Approved (Director level) -> Waiting Supplier
    t4 = _create_ticket_with_history(session, {
        "ticket_number": f"DEMO-{now.strftime('%Y%m%d')}-000004",
        "unit_id": units[1].id,
        "opened_by_user_id": manager_campinas.id,
        "category": TicketCategory.ROOF.value,
        "problem_type": "Telha voou",
        "title": "Vento forte arrancou parte do telhado",
        "description": "Parte da cobertura da pista 1 caiu. Isolamos a área.",
        "priority": PriorityLevel.CRITICAL.value,
        "severity": TicketSeverity.CRITICAL.value,
        "status": TicketStatus.WAITING_SUPPLIER.value,
        "estimated_cost": Decimal("4500.00"),
        "approved_cost": Decimal("4500.00"),
        "requires_approval": True,
        "opened_at": now - timedelta(days=5),
        "triaged_at": now - timedelta(days=4),
        "approved_at": now - timedelta(days=2),
        "sla_due_at": now - timedelta(hours=5), # Late!
        "supplier_id": suppliers[3].id,
    }, manager_campinas.id)

    approval_t4_exists = session.execute(
        text("SELECT id FROM approvals WHERE ticket_id = :ticket_id"),
        {"ticket_id": t4.id},
    ).scalar()
    if not approval_t4_exists:
        session.execute(
            text(
                """
                INSERT INTO approvals (
                    ticket_id,
                    approval_level_id,
                    requested_by_user_id,
                    approved_by_user_id,
                    status,
                    amount_requested,
                    amount_approved,
                    justification,
                    approved_at
                )
                VALUES (
                    :ticket_id,
                    :approval_level_id,
                    :requested_by_user_id,
                    :approved_by_user_id,
                    :status,
                    :amount_requested,
                    :amount_approved,
                    :justification,
                    :approved_at
                )
                """
            ),
            _sql_params(
                ticket_id=t4.id,
                approval_level_id=levels[1].id,
                requested_by_user_id=eng.id,
                approved_by_user_id=director.id,
                status=_enum_storage_value(session, ApprovalStatus, ApprovalStatus.APPROVED.value),
                amount_requested=Decimal("4500.00"),
                amount_approved=Decimal("4500.00"),
                justification="Orçamento para telhado aprovado devido à urgência.",
                approved_at=now - timedelta(days=2),
            ),
        )

        session.execute(
            text(
                """
                INSERT INTO ticket_alerts (
                    ticket_id,
                    alert_type,
                    severity,
                    message,
                    is_read,
                    created_by_system,
                    read_at
                )
                VALUES (
                    :ticket_id,
                    :alert_type,
                    :severity,
                    :message,
                    :is_read,
                    :created_by_system,
                    :read_at
                )
                """
            ),
            _sql_params(
                ticket_id=t4.id,
                alert_type=_enum_storage_value(session, AlertType, AlertType.SLA_LATE.value),
                severity=_enum_storage_value(session, AlertSeverity, AlertSeverity.CRITICAL.value),
                message=f"SLA estourado para o chamado {t4.ticket_number}.",
                is_read=False,
                created_by_system=True,
                read_at=None,
            ),
        )

    # 5. In Progress
    _create_ticket_with_history(session, {
        "ticket_number": f"DEMO-{now.strftime('%Y%m%d')}-000005",
        "unit_id": units[0].id,
        "opened_by_user_id": manager_sp.id,
        "assigned_to_user_id": eng.id,
        "category": TicketCategory.FUEL_PUMP.value,
        "problem_type": "Falha na bomba",
        "title": "Bomba 1 parou geral",
        "description": "Bomba não liga.",
        "priority": PriorityLevel.HIGH.value,
        "severity": TicketSeverity.HIGH.value,
        "status": TicketStatus.IN_PROGRESS.value,
        "fuel_nozzles_stopped": 2,
        "estimated_daily_loss": Decimal("1500.00"),
        "opened_at": now - timedelta(days=2),
        "triaged_at": now - timedelta(days=1),
        "started_at": now - timedelta(hours=2),
        "sla_due_at": now + timedelta(days=2),
        "supplier_id": suppliers[2].id,
    }, manager_sp.id)

    # 6. Resolved
    _create_ticket_with_history(session, {
        "ticket_number": f"DEMO-{now.strftime('%Y%m%d')}-000006",
        "unit_id": units[1].id,
        "opened_by_user_id": manager_campinas.id,
        "assigned_to_user_id": eng.id,
        "category": TicketCategory.PAVEMENT.value,
        "problem_type": "Buraco na pista",
        "title": "Buraco grande próximo à bomba 4",
        "description": "Carros estão batendo o pneu.",
        "priority": PriorityLevel.LOW.value,
        "severity": TicketSeverity.LOW.value,
        "status": TicketStatus.RESOLVED.value,
        "opened_at": now - timedelta(days=10),
        "triaged_at": now - timedelta(days=9),
        "started_at": now - timedelta(days=5),
        "resolved_at": now - timedelta(days=1),
        "sla_due_at": now + timedelta(days=5),
        "supplier_id": suppliers[4].id,
    }, manager_campinas.id)

    # 7. Closed
    _create_ticket_with_history(session, {
        "ticket_number": f"DEMO-{now.strftime('%Y%m%d')}-000007",
        "unit_id": units[0].id,
        "opened_by_user_id": manager_sp.id,
        "assigned_to_user_id": eng.id,
        "category": TicketCategory.ENVIRONMENTAL_RISK.value,
        "problem_type": "Vazamento de óleo",
        "title": "Mancha de óleo na canaleta",
        "description": "Vazamento do tanque antigo.",
        "priority": PriorityLevel.CRITICAL.value,
        "severity": TicketSeverity.CRITICAL.value,
        "status": TicketStatus.CLOSED.value,
        "opened_at": now - timedelta(days=30),
        "triaged_at": now - timedelta(days=29),
        "started_at": now - timedelta(days=28),
        "resolved_at": now - timedelta(days=15),
        "closed_at": now - timedelta(days=10),
        "sla_due_at": now - timedelta(days=25),
        "supplier_id": suppliers[0].id,
        "final_cost": Decimal("12500.00"),
    }, manager_sp.id)

    # Create more generic tickets to reach 20
    for i in range(8, 21):
        _create_ticket_with_history(session, {
            "ticket_number": f"DEMO-{now.strftime('%Y%m%d')}-{i:06d}",
            "unit_id": units[i % len(units)].id,
            "opened_by_user_id": manager_sp.id if i % 2 == 0 else manager_campinas.id,
            "category": TicketCategory.OTHER.value,
            "problem_type": f"Problema genérico {i}",
            "title": f"Chamado de teste {i}",
            "description": f"Descrição do chamado {i} gerado no seed demo.",
            "priority": PriorityLevel.LOW.value,
            "severity": TicketSeverity.LOW.value,
            "status": TicketStatus.OPEN.value,
            "opened_at": now - timedelta(days=i),
            "sla_due_at": now + timedelta(days=30-i),
        }, users[0].id)

    session.flush()


def main() -> None:
    settings = get_settings()
    if settings.app_env.lower() == "production":
        raise SystemExit("Refusing to run seed_demo in production.")

    session_factory = get_session_factory()
    session = session_factory()

    try:
        levels = seed_approval_levels(session)
        print("✅ Approval Levels seeded.")

        seed_ticket_configuration(session)
        print("✅ Ticket configuration seeded.")

        units = seed_units(session)
        print("✅ Units seeded.")

        users = seed_users(session, units)
        print("✅ Users seeded.")

        suppliers = seed_suppliers(session)
        print("✅ Suppliers seeded.")

        seed_tickets(session, units, users, suppliers, levels)
        print("✅ Tickets seeded.")

        session.commit()
        print("✅ Seed demo completed successfully.")
    except Exception as e:
        session.rollback()
        print(f"❌ Error during seed: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()
