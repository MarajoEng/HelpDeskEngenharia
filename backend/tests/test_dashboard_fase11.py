"""FASE 11 — testes do dashboard operacional."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import httpx
import pytest

from app.models.enums import TicketStatus, UserRole
from app.models.ticket import Ticket


def _create_ticket(
    db_session,
    *,
    unit_id: int,
    opened_by_user_id: int,
    ticket_number: str,
    status: TicketStatus,
    category: str = "fuel_pump",
    priority: str = "medium",
    severity: str = "medium",
    opened_at: datetime | None = None,
    sla_due_at: datetime | None = None,
    resolved_at: datetime | None = None,
    closed_at: datetime | None = None,
    fuel_nozzles_stopped: int | None = None,
    estimated_daily_loss: str | Decimal | None = None,
    estimated_cost: str | Decimal | None = None,
    approved_cost: str | Decimal | None = None,
    final_cost: str | Decimal | None = None,
) -> Ticket:
    now = datetime.now(UTC)
    ticket = Ticket(
        ticket_number=ticket_number,
        unit_id=unit_id,
        opened_by_user_id=opened_by_user_id,
        assigned_to_user_id=None,
        category=category,
        problem_type="Falha operacional",
        title=f"Chamado {ticket_number}",
        description="Descricao",
        priority=priority,
        severity=severity,
        status=status,
        requires_approval=False,
        opened_at=opened_at or now,
        triaged_at=now if status in {TicketStatus.TRIAGE, TicketStatus.WAITING_APPROVAL, TicketStatus.APPROVED, TicketStatus.IN_PROGRESS, TicketStatus.RESOLVED, TicketStatus.CLOSED} else None,
        approved_at=now if status == TicketStatus.APPROVED else None,
        started_at=now if status in {TicketStatus.IN_PROGRESS, TicketStatus.RESOLVED, TicketStatus.CLOSED} else None,
        resolved_at=resolved_at,
        closed_at=closed_at,
        sla_due_at=sla_due_at,
        fuel_nozzles_stopped=fuel_nozzles_stopped,
        estimated_daily_loss=estimated_daily_loss,
        estimated_cost=estimated_cost,
        approved_cost=approved_cost,
        final_cost=final_cost,
    )
    db_session.add(ticket)
    db_session.commit()
    db_session.refresh(ticket)
    return ticket


def _seed_dashboard_dataset(db_session, create_unit, create_user):
    base_now = datetime.now(UTC)
    unit_1 = create_unit(code="U-001", name="Unidade Centro", region="Sudeste")
    unit_2 = create_unit(code="U-002", name="Unidade Sul", region="Sul")
    admin = create_user(role=UserRole.ADMIN, email="admin-dashboard@local.test")
    engineering = create_user(role=UserRole.ENGINEERING, email="eng-dashboard@local.test")
    director = create_user(role=UserRole.DIRECTOR, email="director-dashboard@local.test")
    manager = create_user(role=UserRole.MANAGER, email="manager-dashboard@local.test", unit_id=unit_1.id)
    supplier = create_user(role=UserRole.SUPPLIER, email="supplier-dashboard@local.test")

    _create_ticket(
        db_session,
        unit_id=unit_1.id,
        opened_by_user_id=admin.id,
        ticket_number="ENG-001",
        status=TicketStatus.OPEN,
        priority="high",
        severity="critical",
        opened_at=base_now - timedelta(days=1),
        sla_due_at=base_now + timedelta(hours=6),
        fuel_nozzles_stopped=2,
        estimated_daily_loss="1000.00",
        estimated_cost="200.00",
    )
    _create_ticket(
        db_session,
        unit_id=unit_1.id,
        opened_by_user_id=admin.id,
        ticket_number="ENG-002",
        status=TicketStatus.TRIAGE,
        category="leak",
        priority="medium",
        severity="high",
        opened_at=base_now - timedelta(days=2),
        sla_due_at=base_now - timedelta(hours=2),
        estimated_cost="120.00",
    )
    _create_ticket(
        db_session,
        unit_id=unit_1.id,
        opened_by_user_id=admin.id,
        ticket_number="ENG-003",
        status=TicketStatus.WAITING_APPROVAL,
        category="electrical",
        priority="low",
        severity="medium",
        opened_at=base_now - timedelta(days=3),
        approved_cost="50.00",
    )
    _create_ticket(
        db_session,
        unit_id=unit_2.id,
        opened_by_user_id=admin.id,
        ticket_number="ENG-004",
        status=TicketStatus.APPROVED,
        category="roof",
        priority="medium",
        severity="medium",
        opened_at=base_now - timedelta(days=1),
        sla_due_at=base_now + timedelta(hours=8),
        approved_cost="280.00",
    )
    _create_ticket(
        db_session,
        unit_id=unit_2.id,
        opened_by_user_id=admin.id,
        ticket_number="ENG-005",
        status=TicketStatus.IN_PROGRESS,
        category="structure",
        priority="critical",
        severity="critical",
        opened_at=base_now - timedelta(days=1, hours=6),
        sla_due_at=base_now - timedelta(hours=1),
        fuel_nozzles_stopped=3,
        estimated_daily_loss="500.00",
        estimated_cost="300.00",
        approved_cost="280.00",
    )
    _create_ticket(
        db_session,
        unit_id=unit_1.id,
        opened_by_user_id=admin.id,
        ticket_number="ENG-006",
        status=TicketStatus.RESOLVED,
        category="plumbing",
        priority="high",
        severity="medium",
        opened_at=base_now - timedelta(hours=10),
        resolved_at=base_now - timedelta(hours=6),
        sla_due_at=base_now - timedelta(hours=5),
        final_cost="400.00",
    )
    _create_ticket(
        db_session,
        unit_id=unit_2.id,
        opened_by_user_id=admin.id,
        ticket_number="ENG-007",
        status=TicketStatus.CLOSED,
        category="roof",
        priority="medium",
        severity="low",
        opened_at=base_now - timedelta(hours=12),
        resolved_at=base_now - timedelta(hours=9),
        closed_at=base_now - timedelta(hours=7),
        sla_due_at=base_now - timedelta(hours=8),
        final_cost="250.00",
    )
    _create_ticket(
        db_session,
        unit_id=unit_2.id,
        opened_by_user_id=admin.id,
        ticket_number="ENG-008",
        status=TicketStatus.CANCELED,
        category="other",
        priority="low",
        severity="low",
        opened_at=base_now - timedelta(days=4),
    )
    _create_ticket(
        db_session,
        unit_id=unit_1.id,
        opened_by_user_id=admin.id,
        ticket_number="ENG-009",
        status=TicketStatus.OPEN,
        category="fuel_pump",
        priority="low",
        severity="low",
        opened_at=base_now - timedelta(days=40),
        sla_due_at=base_now - timedelta(days=39),
        estimated_cost="50.00",
    )
    return {
        "unit_1": unit_1,
        "unit_2": unit_2,
        "admin": admin,
        "engineering": engineering,
        "director": director,
        "manager": manager,
        "supplier": supplier,
    }


@pytest.mark.anyio
async def test_dashboard_access_by_role(
    client: httpx.AsyncClient,
    db_session,
    create_unit,
    create_user,
    auth_header_for_user,
) -> None:
    data = _seed_dashboard_dataset(db_session, create_unit, create_user)

    admin_response = await client.get("/dashboard/overview", headers=auth_header_for_user(data["admin"]))
    engineering_response = await client.get("/dashboard/overview", headers=auth_header_for_user(data["engineering"]))
    director_response = await client.get("/dashboard/overview", headers=auth_header_for_user(data["director"]))
    supplier_response = await client.get("/dashboard/overview", headers=auth_header_for_user(data["supplier"]))
    no_auth_response = await client.get("/dashboard/overview")

    assert admin_response.status_code == 200
    assert engineering_response.status_code == 200
    assert director_response.status_code == 200
    assert supplier_response.status_code == 403
    assert no_auth_response.status_code == 401


@pytest.mark.anyio
async def test_manager_dashboard_scope_and_other_unit_block(
    client: httpx.AsyncClient,
    db_session,
    create_unit,
    create_user,
    auth_header_for_user,
) -> None:
    data = _seed_dashboard_dataset(db_session, create_unit, create_user)

    own_scope_response = await client.get("/dashboard/overview", headers=auth_header_for_user(data["manager"]))
    blocked_response = await client.get(
        f"/dashboard/overview?unit_id={data['unit_2'].id}",
        headers=auth_header_for_user(data["manager"]),
    )

    assert own_scope_response.status_code == 200
    own_scope = own_scope_response.json()
    assert own_scope["total_tickets"] == 5
    assert all(item["unit_id"] == data["unit_1"].id for item in own_scope["ranking_units_by_tickets"])
    assert blocked_response.status_code == 403


@pytest.mark.anyio
async def test_dashboard_filters_period_unit_region_status_and_category(
    client: httpx.AsyncClient,
    db_session,
    create_unit,
    create_user,
    auth_header_for_user,
) -> None:
    data = _seed_dashboard_dataset(db_session, create_unit, create_user)

    today = datetime.now(UTC).date().isoformat()
    unit_response = await client.get(
        f"/dashboard/overview?unit_id={data['unit_2'].id}",
        headers=auth_header_for_user(data["admin"]),
    )
    region_response = await client.get(
        "/dashboard/overview?region=Sudeste",
        headers=auth_header_for_user(data["admin"]),
    )
    status_response = await client.get(
        "/dashboard/overview?status=in_progress",
        headers=auth_header_for_user(data["admin"]),
    )
    category_response = await client.get(
        "/dashboard/overview?category=roof",
        headers=auth_header_for_user(data["admin"]),
    )
    period_response = await client.get(
        f"/dashboard/overview?date_from={today}&date_to={today}",
        headers=auth_header_for_user(data["admin"]),
    )

    assert unit_response.status_code == 200
    assert unit_response.json()["total_tickets"] == 4
    assert region_response.status_code == 200
    assert region_response.json()["total_tickets"] == 5
    assert status_response.status_code == 200
    assert status_response.json()["in_progress_tickets"] == 1
    assert status_response.json()["total_tickets"] == 1
    assert category_response.status_code == 200
    assert category_response.json()["total_tickets"] == 2
    assert period_response.status_code == 200
    assert period_response.json()["total_tickets"] == 2


@pytest.mark.anyio
async def test_dashboard_zero_cards_when_no_data(
    client: httpx.AsyncClient,
    create_user,
    auth_header_for_user,
) -> None:
    admin = create_user(role=UserRole.ADMIN, email="admin-empty-dashboard@local.test")
    response = await client.get("/dashboard/overview", headers=auth_header_for_user(admin))

    assert response.status_code == 200
    data = response.json()
    assert data["total_tickets"] == 0
    assert data["sla_compliance_rate"] == 0
    assert data["executive_cards"]["final_cost_total"] == 0
    assert data["tickets_by_status"] == []
    assert data["tickets_by_category"] == []
    assert data["tickets_by_priority"] == []
    assert data["tickets_by_severity"] == []
    assert data["late_tickets_preview"] == []


@pytest.mark.anyio
async def test_dashboard_counts_distributions_rankings_and_costs(
    client: httpx.AsyncClient,
    db_session,
    create_unit,
    create_user,
    auth_header_for_user,
) -> None:
    data = _seed_dashboard_dataset(db_session, create_unit, create_user)
    response = await client.get("/dashboard/overview", headers=auth_header_for_user(data["admin"]))

    assert response.status_code == 200
    payload = response.json()
    assert payload["total_tickets"] == 9
    assert payload["open_tickets"] == 2
    assert payload["triage_tickets"] == 1
    assert payload["waiting_approval_tickets"] == 1
    assert payload["approved_tickets"] == 1
    assert payload["in_progress_tickets"] == 1
    assert payload["resolved_tickets"] == 1
    assert payload["closed_tickets"] == 1
    assert payload["canceled_tickets"] == 1
    assert payload["late_tickets"] == 3
    assert payload["critical_tickets"] == 2
    assert payload["tickets_with_fuel_nozzles_stopped"] == 2
    assert payload["total_fuel_nozzles_stopped"] == 5
    assert payload["estimated_daily_loss_total"] == 1500
    assert payload["estimated_cost_total"] == 670
    assert payload["approved_cost_total"] == 610
    assert payload["final_cost_total"] == 650

    status_map = {item["status"]: item["total"] for item in payload["tickets_by_status"]}
    category_map = {item["category"]: item["total"] for item in payload["tickets_by_category"]}
    priority_map = {item["priority"]: item["total"] for item in payload["tickets_by_priority"]}
    severity_map = {item["severity"]: item["total"] for item in payload["tickets_by_severity"]}
    assert status_map["open"] == 2
    assert category_map["roof"] == 2
    assert priority_map["medium"] == 3
    assert severity_map["critical"] == 2

    assert len(payload["ranking_units_by_tickets"]) == 2
    assert payload["ranking_units_by_tickets"][0]["unit_id"] == data["unit_1"].id
    assert payload["ranking_units_by_tickets"][0]["total_tickets"] == 5
    assert len(payload["ranking_units_by_cost"]) == 2
    assert payload["ranking_units_by_cost"][0]["estimated_cost_total"] >= payload["ranking_units_by_cost"][1]["estimated_cost_total"]
    assert len(payload["ranking_units_by_fuel_nozzles"]) == 2
    assert payload["ranking_units_by_fuel_nozzles"][0]["total_fuel_nozzles_stopped"] >= payload["ranking_units_by_fuel_nozzles"][1]["total_fuel_nozzles_stopped"]


@pytest.mark.anyio
async def test_dashboard_sla_and_averages_are_calculated_safely(
    client: httpx.AsyncClient,
    db_session,
    create_unit,
    create_user,
    auth_header_for_user,
) -> None:
    data = _seed_dashboard_dataset(db_session, create_unit, create_user)
    response = await client.get("/dashboard/overview", headers=auth_header_for_user(data["admin"]))

    assert response.status_code == 200
    payload = response.json()
    assert payload["average_resolution_hours"] == 3.5
    assert payload["average_closure_hours"] == 2
    assert payload["sla_compliance_rate"] == 42.86
    assert payload["sla_summary"]["total_with_sla"] == 7
    assert payload["sla_summary"]["on_track"] == 2
    assert payload["sla_summary"]["late"] == 3
    assert payload["sla_summary"]["closed_on_time"] == 1
    assert payload["sla_summary"]["closed_late"] == 1
    assert payload["executive_cards"]["sla_compliance_rate"] == payload["sla_compliance_rate"]


@pytest.mark.anyio
async def test_dashboard_late_preview_is_limited_to_ten(
    client: httpx.AsyncClient,
    db_session,
    create_unit,
    create_user,
    auth_header_for_user,
) -> None:
    unit = create_unit(code="U-010", name="Unidade Limite", region="Sudeste")
    admin = create_user(role=UserRole.ADMIN, email="admin-preview@local.test")
    base_now = datetime.now(UTC)

    for index in range(12):
        _create_ticket(
            db_session,
            unit_id=unit.id,
            opened_by_user_id=admin.id,
            ticket_number=f"ENG-LATE-{index:02d}",
            status=TicketStatus.OPEN,
            priority="high",
            severity="high",
            opened_at=base_now - timedelta(days=index + 1),
            sla_due_at=base_now - timedelta(hours=index + 1),
        )

    response = await client.get("/dashboard/overview", headers=auth_header_for_user(admin))

    assert response.status_code == 200
    payload = response.json()
    assert payload["late_tickets"] == 12
    assert len(payload["late_tickets_preview"]) == 10
    assert payload["late_tickets_preview"][0]["ticket_number"] == "ENG-LATE-11"
