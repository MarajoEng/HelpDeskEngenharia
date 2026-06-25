from datetime import UTC, datetime, timedelta
from decimal import Decimal

import httpx
import pytest
from sqlalchemy import select

from app.models.enums import TicketStatus, UserRole
from app.models.ticket import Ticket
from app.models.ticket_history import TicketHistory


def make_ticket_payload(unit_id: int, **overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "unit_id": unit_id,
        "category": "fuel_pump",
        "problem_type": "Falha de pressao",
        "title": "Bomba principal sem operacao",
        "description": "A bomba principal da pista 2 parou de funcionar.",
        "priority": "high",
        "severity": "critical",
        "operational_impact": "Pista operando parcialmente.",
        "fuel_nozzles_stopped": 2,
        "estimated_daily_loss": "1500.00",
        "estimated_cost": "8000.00",
        "requires_approval": True,
    }
    payload.update(overrides)
    return payload


@pytest.mark.anyio
async def test_admin_creates_ticket(
    client: httpx.AsyncClient,
    db_session,
    create_unit,
    create_user,
    auth_header_for_user,
) -> None:
    unit = create_unit()
    admin = create_user(role=UserRole.ADMIN)

    response = await client.post(
        "/tickets",
        headers=auth_header_for_user(admin),
        json=make_ticket_payload(unit.id),
    )

    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "open"
    assert data["opened_by_user_id"] == admin.id
    assert data["assigned_to_user_id"] is None
    assert data["ticket_number"].startswith("ENG-")
    assert data["opened_at"] is not None
    assert data["estimated_loss_total"] == "3000.00"

    created_ticket = db_session.get(Ticket, data["id"])
    assert created_ticket is not None
    history = db_session.scalar(
        select(TicketHistory).where(TicketHistory.ticket_id == created_ticket.id)
    )
    assert history is not None
    assert history.old_status is None
    assert history.new_status == TicketStatus.OPEN
    assert history.comment == "Chamado aberto"


@pytest.mark.anyio
async def test_engineering_creates_ticket(
    client: httpx.AsyncClient,
    create_unit,
    create_user,
    auth_header_for_user,
) -> None:
    unit = create_unit()
    engineering = create_user(role=UserRole.ENGINEERING)

    response = await client.post(
        "/tickets",
        headers=auth_header_for_user(engineering),
        json=make_ticket_payload(unit.id, requires_approval=False),
    )

    assert response.status_code == 201
    assert response.json()["opened_by_user_id"] == engineering.id


@pytest.mark.anyio
async def test_director_creates_ticket(
    client: httpx.AsyncClient,
    create_unit,
    create_user,
    auth_header_for_user,
) -> None:
    unit = create_unit()
    director = create_user(role=UserRole.DIRECTOR)

    response = await client.post(
        "/tickets",
        headers=auth_header_for_user(director),
        json=make_ticket_payload(unit.id),
    )

    assert response.status_code == 201
    assert response.json()["opened_by_user_id"] == director.id


@pytest.mark.anyio
async def test_manager_creates_ticket_for_own_unit(
    client: httpx.AsyncClient,
    create_unit,
    create_user,
    auth_header_for_user,
) -> None:
    unit = create_unit()
    manager = create_user(role=UserRole.MANAGER, unit_id=unit.id)

    response = await client.post(
        "/tickets",
        headers=auth_header_for_user(manager),
        json=make_ticket_payload(unit.id),
    )

    assert response.status_code == 201
    assert response.json()["unit_id"] == unit.id


@pytest.mark.anyio
async def test_manager_cannot_create_ticket_for_other_unit(
    client: httpx.AsyncClient,
    create_unit,
    create_user,
    auth_header_for_user,
) -> None:
    own_unit = create_unit(code="U-001")
    other_unit = create_unit(code="U-002", name="Outra", city="Campinas")
    manager = create_user(role=UserRole.MANAGER, unit_id=own_unit.id)

    response = await client.post(
        "/tickets",
        headers=auth_header_for_user(manager),
        json=make_ticket_payload(other_unit.id),
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "Insufficient permissions."}


@pytest.mark.anyio
async def test_supplier_cannot_create_ticket(
    client: httpx.AsyncClient,
    create_unit,
    create_user,
    auth_header_for_user,
) -> None:
    unit = create_unit()
    supplier = create_user(role=UserRole.SUPPLIER)

    response = await client.post(
        "/tickets",
        headers=auth_header_for_user(supplier),
        json=make_ticket_payload(unit.id),
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "Insufficient permissions."}


@pytest.mark.anyio
async def test_ticket_creation_blocks_nonexistent_unit(
    client: httpx.AsyncClient,
    create_user,
    auth_header_for_user,
) -> None:
    admin = create_user(role=UserRole.ADMIN)

    response = await client.post(
        "/tickets",
        headers=auth_header_for_user(admin),
        json=make_ticket_payload(999),
    )

    assert response.status_code == 422
    assert response.json() == {"detail": "Provided unit does not exist."}


@pytest.mark.anyio
async def test_ticket_creation_blocks_inactive_unit(
    client: httpx.AsyncClient,
    create_unit,
    create_user,
    auth_header_for_user,
) -> None:
    inactive_unit = create_unit(is_active=False)
    admin = create_user(role=UserRole.ADMIN)

    response = await client.post(
        "/tickets",
        headers=auth_header_for_user(admin),
        json=make_ticket_payload(inactive_unit.id),
    )

    assert response.status_code == 422
    assert response.json() == {"detail": "Provided unit is inactive."}


@pytest.mark.anyio
async def test_ticket_negative_values_are_blocked(
    client: httpx.AsyncClient,
    create_unit,
    create_user,
    auth_header_for_user,
) -> None:
    unit = create_unit()
    admin = create_user(role=UserRole.ADMIN)

    response = await client.post(
        "/tickets",
        headers=auth_header_for_user(admin),
        json=make_ticket_payload(unit.id, estimated_cost="-10.00"),
    )

    assert response.status_code == 422


@pytest.mark.anyio
async def test_tickets_list_is_paginated(
    client: httpx.AsyncClient,
    create_unit,
    create_user,
    auth_header_for_user,
) -> None:
    unit = create_unit()
    admin = create_user(role=UserRole.ADMIN)

    await client.post("/tickets", headers=auth_header_for_user(admin), json=make_ticket_payload(unit.id, title="Ticket A"))
    await client.post("/tickets", headers=auth_header_for_user(admin), json=make_ticket_payload(unit.id, title="Ticket B"))
    await client.post("/tickets", headers=auth_header_for_user(admin), json=make_ticket_payload(unit.id, title="Ticket C"))

    response = await client.get("/tickets?page=2&page_size=2", headers=auth_header_for_user(admin))

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert data["page"] == 2
    assert data["page_size"] == 2
    assert data["pages"] == 2
    assert len(data["items"]) == 1


@pytest.mark.anyio
async def test_manager_lists_only_own_unit_tickets(
    client: httpx.AsyncClient,
    create_unit,
    create_user,
    auth_header_for_user,
) -> None:
    own_unit = create_unit(code="U-001")
    other_unit = create_unit(code="U-002", name="Outra", city="Campinas")
    admin = create_user(role=UserRole.ADMIN)
    manager = create_user(
        name="Manager Centro",
        email="manager.centro@local.test",
        role=UserRole.MANAGER,
        unit_id=own_unit.id,
    )

    await client.post("/tickets", headers=auth_header_for_user(admin), json=make_ticket_payload(own_unit.id, title="Ticket proprio"))
    await client.post("/tickets", headers=auth_header_for_user(admin), json=make_ticket_payload(other_unit.id, title="Ticket externo"))

    response = await client.get("/tickets", headers=auth_header_for_user(manager))

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["unit_id"] == own_unit.id


@pytest.mark.anyio
async def test_ticket_filters_by_status_category_priority_and_search(
    client: httpx.AsyncClient,
    db_session,
    create_unit,
    create_user,
    auth_header_for_user,
) -> None:
    unit = create_unit()
    admin = create_user(role=UserRole.ADMIN)

    first_response = await client.post(
        "/tickets",
        headers=auth_header_for_user(admin),
        json=make_ticket_payload(unit.id, title="Vazamento grave", category="leak", priority="critical"),
    )
    second_response = await client.post(
        "/tickets",
        headers=auth_header_for_user(admin),
        json=make_ticket_payload(unit.id, title="Falha eletrica", category="electrical", priority="medium"),
    )

    first_ticket = db_session.get(Ticket, first_response.json()["id"])
    second_ticket = db_session.get(Ticket, second_response.json()["id"])
    assert first_ticket is not None and second_ticket is not None

    second_ticket.status = TicketStatus.TRIAGE
    db_session.add(second_ticket)
    db_session.commit()

    response = await client.get(
        "/tickets?status=open&category=leak&priority=critical&search=Vazamento",
        headers=auth_header_for_user(admin),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["id"] == first_ticket.id


@pytest.mark.anyio
async def test_ticket_detail_respects_permissions(
    client: httpx.AsyncClient,
    create_unit,
    create_user,
    auth_header_for_user,
) -> None:
    own_unit = create_unit(code="U-001")
    other_unit = create_unit(code="U-002", name="Outra", city="Campinas")
    admin = create_user(role=UserRole.ADMIN)
    manager = create_user(
        name="Manager Centro",
        email="manager.centro@local.test",
        role=UserRole.MANAGER,
        unit_id=own_unit.id,
    )

    response = await client.post(
        "/tickets",
        headers=auth_header_for_user(admin),
        json=make_ticket_payload(other_unit.id, title="Ticket externo"),
    )
    ticket_id = response.json()["id"]

    forbidden = await client.get(f"/tickets/{ticket_id}", headers=auth_header_for_user(manager))
    assert forbidden.status_code == 403
    assert forbidden.json() == {"detail": "Insufficient permissions."}

    allowed = await client.get(f"/tickets/{ticket_id}", headers=auth_header_for_user(admin))
    assert allowed.status_code == 200
    assert allowed.json()["id"] == ticket_id


@pytest.mark.anyio
async def test_ticket_detail_returns_404_for_missing_ticket(
    client: httpx.AsyncClient,
    create_user,
    auth_header_for_user,
) -> None:
    admin = create_user(role=UserRole.ADMIN)

    response = await client.get("/tickets/999", headers=auth_header_for_user(admin))

    assert response.status_code == 404
    assert response.json() == {"detail": "Ticket not found."}
