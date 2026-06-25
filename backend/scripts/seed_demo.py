from __future__ import annotations

import sys
from datetime import datetime, timedelta, UTC
from decimal import Decimal
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from sqlalchemy import select

from app.core.config import get_settings
from app.core.database import get_session_factory
from app.core.security import hash_password
from app.models.approval import Approval
from app.models.approval_level import ApprovalLevel
from app.models.enums import AlertSeverity, AlertType, ApprovalStatus, PriorityLevel, TicketCategory, TicketSeverity, TicketStatus, UserRole
from app.models.supplier import Supplier
from app.models.ticket import Ticket
from app.models.ticket_alert import TicketAlert
from app.models.ticket_history import TicketHistory
from app.models.unit import Unit
from app.models.user import User


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


def seed_users(session, units) -> list[User]:
    users_data = [
        {"name": "Admin", "email": "admin@local.test", "role": UserRole.ADMIN, "unit_id": None},
        {"name": "Engenharia", "email": "engenharia@local.test", "role": UserRole.ENGINEERING, "unit_id": None},
        {"name": "Diretor", "email": "diretor@local.test", "role": UserRole.DIRECTOR, "unit_id": None},
        {"name": "Gerente SP", "email": "gerente0101@local.test", "role": UserRole.MANAGER, "unit_id": units[0].id},
        {"name": "Gerente Campinas", "email": "gerente0201@local.test", "role": UserRole.MANAGER, "unit_id": units[1].id},
    ]

    users = []
    password_hash = hash_password("admin123")
    for data in users_data:
        stmt = select(User).where(User.email == data["email"])
        user = session.scalar(stmt)
        if not user:
            user = User(**data, password_hash=password_hash, is_active=True)
            session.add(user)
            session.flush()
        else:
            for k, v in data.items():
                setattr(user, k, v)
            user.password_hash = password_hash
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


def _create_ticket_with_history(session, ticket_data, user_id):
    stmt = select(Ticket).where(Ticket.ticket_number == ticket_data["ticket_number"])
    ticket = session.scalar(stmt)
    if ticket:
        # Already seeded
        return ticket

    ticket = Ticket(**ticket_data)
    session.add(ticket)
    session.flush()

    history = TicketHistory(
        ticket_id=ticket.id,
        user_id=user_id,
        old_status=None,
        new_status=ticket_data["status"],
        comment="Chamado criado pelo seed demo."
    )
    session.add(history)
    session.flush()
    return ticket


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
        "category": TicketCategory.FUEL_NOZZLE,
        "problem_type": "Bico parado",
        "title": "Bico de gasolina comum vazando",
        "description": "Bico 4 da bomba 2 está vazando quando abastece. Fechamos o bico.",
        "priority": PriorityLevel.HIGH,
        "severity": TicketSeverity.HIGH,
        "status": TicketStatus.OPEN,
        "fuel_nozzles_stopped": 1,
        "estimated_daily_loss": Decimal("800.00"),
        "opened_at": now - timedelta(hours=2),
    }, manager_sp.id)

    # 2. Triage ticket (with SLA due soon)
    _create_ticket_with_history(session, {
        "ticket_number": f"DEMO-{now.strftime('%Y%m%d')}-000002",
        "unit_id": units[1].id,
        "opened_by_user_id": manager_campinas.id,
        "category": TicketCategory.ELECTRICAL,
        "problem_type": "Curto circuito",
        "title": "Luzes da pista piscando",
        "description": "Metade das luzes da pista estão apagadas.",
        "priority": PriorityLevel.MEDIUM,
        "severity": TicketSeverity.MEDIUM,
        "status": TicketStatus.TRIAGE,
        "opened_at": now - timedelta(days=1),
        "triaged_at": now - timedelta(hours=12),
        "sla_due_at": now + timedelta(hours=2),
    }, manager_campinas.id)

    # 3. Waiting Approval (Engineering level)
    t3 = _create_ticket_with_history(session, {
        "ticket_number": f"DEMO-{now.strftime('%Y%m%d')}-000003",
        "unit_id": units[0].id,
        "opened_by_user_id": manager_sp.id,
        "category": TicketCategory.PLUMBING,
        "problem_type": "Vazamento no banheiro",
        "title": "Pia do banheiro quebrada",
        "description": "Cano da pia quebrou, água jorrando. Fechamos o registro.",
        "priority": PriorityLevel.MEDIUM,
        "severity": TicketSeverity.MEDIUM,
        "status": TicketStatus.WAITING_APPROVAL,
        "estimated_cost": Decimal("800.00"),
        "requires_approval": True,
        "opened_at": now - timedelta(days=2),
        "triaged_at": now - timedelta(days=1),
        "sla_due_at": now + timedelta(days=1),
        "supplier_id": suppliers[1].id,
    }, manager_sp.id)

    if not session.scalar(select(Approval).where(Approval.ticket_id == t3.id)):
        appr1 = Approval(
            ticket_id=t3.id,
            approval_level_id=levels[0].id,
            requested_by_user_id=eng.id,
            status=ApprovalStatus.PENDING,
            amount_requested=Decimal("800.00"),
            justification="Orçamento do fornecedor para troca do cano."
        )
        session.add(appr1)

    # 4. Approved (Director level) -> Waiting Supplier
    t4 = _create_ticket_with_history(session, {
        "ticket_number": f"DEMO-{now.strftime('%Y%m%d')}-000004",
        "unit_id": units[1].id,
        "opened_by_user_id": manager_campinas.id,
        "category": TicketCategory.ROOF,
        "problem_type": "Telha voou",
        "title": "Vento forte arrancou parte do telhado",
        "description": "Parte da cobertura da pista 1 caiu. Isolamos a área.",
        "priority": PriorityLevel.CRITICAL,
        "severity": TicketSeverity.CRITICAL,
        "status": TicketStatus.WAITING_SUPPLIER,
        "estimated_cost": Decimal("4500.00"),
        "approved_cost": Decimal("4500.00"),
        "requires_approval": True,
        "opened_at": now - timedelta(days=5),
        "triaged_at": now - timedelta(days=4),
        "approved_at": now - timedelta(days=2),
        "sla_due_at": now - timedelta(hours=5), # Late!
        "supplier_id": suppliers[3].id,
    }, manager_campinas.id)

    if not session.scalar(select(Approval).where(Approval.ticket_id == t4.id)):
        appr2 = Approval(
            ticket_id=t4.id,
            approval_level_id=levels[1].id,
            requested_by_user_id=eng.id,
            approved_by_user_id=director.id,
            status=ApprovalStatus.APPROVED,
            amount_requested=Decimal("4500.00"),
            amount_approved=Decimal("4500.00"),
            justification="Orçamento para telhado aprovado devido à urgência.",
            approved_at=now - timedelta(days=2)
        )
        session.add(appr2)

        # Alert SLA LATE
        alert = TicketAlert(
            ticket_id=t4.id,
            alert_type=AlertType.SLA_LATE,
            severity=AlertSeverity.CRITICAL,
            message=f"SLA estourado para o chamado {t4.ticket_number}.",
            is_read=False
        )
        session.add(alert)

    # 5. In Progress
    _create_ticket_with_history(session, {
        "ticket_number": f"DEMO-{now.strftime('%Y%m%d')}-000005",
        "unit_id": units[0].id,
        "opened_by_user_id": manager_sp.id,
        "assigned_to_user_id": eng.id,
        "category": TicketCategory.FUEL_PUMP,
        "problem_type": "Falha na bomba",
        "title": "Bomba 1 parou geral",
        "description": "Bomba não liga.",
        "priority": PriorityLevel.HIGH,
        "severity": TicketSeverity.HIGH,
        "status": TicketStatus.IN_PROGRESS,
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
        "category": TicketCategory.PAVEMENT,
        "problem_type": "Buraco na pista",
        "title": "Buraco grande próximo à bomba 4",
        "description": "Carros estão batendo o pneu.",
        "priority": PriorityLevel.LOW,
        "severity": TicketSeverity.LOW,
        "status": TicketStatus.RESOLVED,
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
        "category": TicketCategory.ENVIRONMENTAL_RISK,
        "problem_type": "Vazamento de óleo",
        "title": "Mancha de óleo na canaleta",
        "description": "Vazamento do tanque antigo.",
        "priority": PriorityLevel.CRITICAL,
        "severity": TicketSeverity.CRITICAL,
        "status": TicketStatus.CLOSED,
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
            "category": TicketCategory.OTHER,
            "problem_type": f"Problema genérico {i}",
            "title": f"Chamado de teste {i}",
            "description": f"Descrição do chamado {i} gerado no seed demo.",
            "priority": PriorityLevel.LOW,
            "severity": TicketSeverity.LOW,
            "status": TicketStatus.OPEN,
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
