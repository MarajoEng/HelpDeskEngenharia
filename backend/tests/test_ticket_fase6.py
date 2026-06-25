"""FASE 6 — testes de listagem enriquecida, filtros avancados e detalhe com indicadores."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import httpx
import pytest

from app.models.enums import TicketStatus, UserRole
from app.models.ticket import Ticket


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
        "fuel_nozzles_stopped": 3,
        "estimated_daily_loss": "1000.00",
        "estimated_cost": "5000.00",
        "requires_approval": True,
    }
    payload.update(overrides)
    return payload


# ---------------------------------------------------------------------------
# listagem enriquecida
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_list_returns_unit_code_and_name(
    client: httpx.AsyncClient,
    create_unit,
    create_user,
    auth_header_for_user,
) -> None:
    unit = create_unit(code="U-LISTA", name="Unidade Lista")
    admin = create_user(role=UserRole.ADMIN)

    await client.post("/tickets", headers=auth_header_for_user(admin), json=make_ticket_payload(unit.id))

    response = await client.get("/tickets", headers=auth_header_for_user(admin))
    assert response.status_code == 200
    item = response.json()["items"][0]
    assert item["unit_code"] == "U-LISTA"
    assert item["unit_name"] == "Unidade Lista"


@pytest.mark.anyio
async def test_list_returns_opened_by_user_name(
    client: httpx.AsyncClient,
    create_unit,
    create_user,
    auth_header_for_user,
) -> None:
    unit = create_unit()
    admin = create_user(name="Carlos Admin", role=UserRole.ADMIN)

    await client.post("/tickets", headers=auth_header_for_user(admin), json=make_ticket_payload(unit.id))

    response = await client.get("/tickets", headers=auth_header_for_user(admin))
    assert response.status_code == 200
    item = response.json()["items"][0]
    assert item["opened_by_user_name"] == "Carlos Admin"


@pytest.mark.anyio
async def test_list_assigned_to_user_name_is_null_when_not_assigned(
    client: httpx.AsyncClient,
    create_unit,
    create_user,
    auth_header_for_user,
) -> None:
    unit = create_unit()
    admin = create_user(role=UserRole.ADMIN)

    await client.post("/tickets", headers=auth_header_for_user(admin), json=make_ticket_payload(unit.id))

    response = await client.get("/tickets", headers=auth_header_for_user(admin))
    assert response.status_code == 200
    item = response.json()["items"][0]
    assert item["assigned_to_user_name"] is None


# ---------------------------------------------------------------------------
# filtros de busca textual
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_search_by_ticket_number(
    client: httpx.AsyncClient,
    create_unit,
    create_user,
    auth_header_for_user,
) -> None:
    unit = create_unit()
    admin = create_user(role=UserRole.ADMIN)

    resp = await client.post("/tickets", headers=auth_header_for_user(admin), json=make_ticket_payload(unit.id))
    ticket_number = resp.json()["ticket_number"]

    # busca pelo numero exato
    response = await client.get(f"/tickets?search={ticket_number}", headers=auth_header_for_user(admin))
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["ticket_number"] == ticket_number


@pytest.mark.anyio
async def test_search_by_title(
    client: httpx.AsyncClient,
    create_unit,
    create_user,
    auth_header_for_user,
) -> None:
    unit = create_unit()
    admin = create_user(role=UserRole.ADMIN)

    await client.post("/tickets", headers=auth_header_for_user(admin), json=make_ticket_payload(unit.id, title="Vazamento critico na pista"))
    await client.post("/tickets", headers=auth_header_for_user(admin), json=make_ticket_payload(unit.id, title="Falha eletrica no painel"))

    response = await client.get("/tickets?search=Vazamento", headers=auth_header_for_user(admin))
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert "Vazamento" in data["items"][0]["title"]


@pytest.mark.anyio
async def test_search_by_unit_name(
    client: httpx.AsyncClient,
    create_unit,
    create_user,
    auth_header_for_user,
) -> None:
    unit_norte = create_unit(code="U-NORTE", name="Posto Norte")
    unit_sul = create_unit(code="U-SUL", name="Posto Sul", city="Curitiba")
    admin = create_user(role=UserRole.ADMIN)

    await client.post("/tickets", headers=auth_header_for_user(admin), json=make_ticket_payload(unit_norte.id, title="Ticket Norte"))
    await client.post("/tickets", headers=auth_header_for_user(admin), json=make_ticket_payload(unit_sul.id, title="Ticket Sul"))

    response = await client.get("/tickets?search=Norte", headers=auth_header_for_user(admin))
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["unit_name"] == "Posto Norte"


@pytest.mark.anyio
async def test_search_by_unit_code(
    client: httpx.AsyncClient,
    create_unit,
    create_user,
    auth_header_for_user,
) -> None:
    unit = create_unit(code="XYZ-99", name="Posto Unico")
    admin = create_user(role=UserRole.ADMIN)

    await client.post("/tickets", headers=auth_header_for_user(admin), json=make_ticket_payload(unit.id))

    response = await client.get("/tickets?search=XYZ-99", headers=auth_header_for_user(admin))
    assert response.status_code == 200
    assert response.json()["total"] == 1


# ---------------------------------------------------------------------------
# filtros avancados
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_filter_only_late(
    client: httpx.AsyncClient,
    db_session,
    create_unit,
    create_user,
    auth_header_for_user,
) -> None:
    unit = create_unit()
    admin = create_user(role=UserRole.ADMIN)

    resp_late = await client.post("/tickets", headers=auth_header_for_user(admin), json=make_ticket_payload(unit.id, title="Chamado atrasado"))
    resp_ok = await client.post("/tickets", headers=auth_header_for_user(admin), json=make_ticket_payload(unit.id, title="Chamado no prazo"))

    past = datetime.now(UTC) - timedelta(days=2)
    future = datetime.now(UTC) + timedelta(days=5)

    ticket_late = db_session.get(Ticket, resp_late.json()["id"])
    ticket_ok = db_session.get(Ticket, resp_ok.json()["id"])
    ticket_late.sla_due_at = past
    ticket_ok.sla_due_at = future
    db_session.commit()

    response = await client.get("/tickets?only_late=true", headers=auth_header_for_user(admin))
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["id"] == ticket_late.id


@pytest.mark.anyio
async def test_filter_only_late_excludes_closed_tickets(
    client: httpx.AsyncClient,
    db_session,
    create_unit,
    create_user,
    auth_header_for_user,
) -> None:
    unit = create_unit()
    admin = create_user(role=UserRole.ADMIN)

    resp = await client.post("/tickets", headers=auth_header_for_user(admin), json=make_ticket_payload(unit.id))

    past = datetime.now(UTC) - timedelta(days=2)
    ticket = db_session.get(Ticket, resp.json()["id"])
    ticket.sla_due_at = past
    ticket.status = TicketStatus.CLOSED
    db_session.commit()

    response = await client.get("/tickets?only_late=true", headers=auth_header_for_user(admin))
    assert response.status_code == 200
    assert response.json()["total"] == 0


@pytest.mark.anyio
async def test_filter_has_fuel_nozzles_stopped(
    client: httpx.AsyncClient,
    create_unit,
    create_user,
    auth_header_for_user,
) -> None:
    unit = create_unit()
    admin = create_user(role=UserRole.ADMIN)

    await client.post(
        "/tickets",
        headers=auth_header_for_user(admin),
        json=make_ticket_payload(unit.id, title="Com bicos parados", fuel_nozzles_stopped=4),
    )
    await client.post(
        "/tickets",
        headers=auth_header_for_user(admin),
        json=make_ticket_payload(unit.id, title="Sem bicos", fuel_nozzles_stopped=0),
    )

    response = await client.get("/tickets?has_fuel_nozzles_stopped=true", headers=auth_header_for_user(admin))
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["fuel_nozzles_stopped"] == 4


@pytest.mark.anyio
async def test_filter_min_estimated_cost(
    client: httpx.AsyncClient,
    create_unit,
    create_user,
    auth_header_for_user,
) -> None:
    unit = create_unit()
    admin = create_user(role=UserRole.ADMIN)

    await client.post("/tickets", headers=auth_header_for_user(admin), json=make_ticket_payload(unit.id, estimated_cost="200.00"))
    await client.post("/tickets", headers=auth_header_for_user(admin), json=make_ticket_payload(unit.id, estimated_cost="5000.00"))

    response = await client.get("/tickets?min_estimated_cost=1000", headers=auth_header_for_user(admin))
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert Decimal(data["items"][0]["estimated_cost"]) >= Decimal("1000")


@pytest.mark.anyio
async def test_filter_max_estimated_cost(
    client: httpx.AsyncClient,
    create_unit,
    create_user,
    auth_header_for_user,
) -> None:
    unit = create_unit()
    admin = create_user(role=UserRole.ADMIN)

    await client.post("/tickets", headers=auth_header_for_user(admin), json=make_ticket_payload(unit.id, estimated_cost="200.00"))
    await client.post("/tickets", headers=auth_header_for_user(admin), json=make_ticket_payload(unit.id, estimated_cost="5000.00"))

    response = await client.get("/tickets?max_estimated_cost=500", headers=auth_header_for_user(admin))
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert Decimal(data["items"][0]["estimated_cost"]) <= Decimal("500")


@pytest.mark.anyio
async def test_negative_cost_filter_is_blocked(
    client: httpx.AsyncClient,
    create_user,
    auth_header_for_user,
) -> None:
    admin = create_user(role=UserRole.ADMIN)

    response = await client.get("/tickets?min_estimated_cost=-100", headers=auth_header_for_user(admin))
    assert response.status_code == 422

    response2 = await client.get("/tickets?max_estimated_cost=-1", headers=auth_header_for_user(admin))
    assert response2.status_code == 422


@pytest.mark.anyio
async def test_supplier_cannot_list_tickets(
    client: httpx.AsyncClient,
    create_user,
    auth_header_for_user,
) -> None:
    supplier = create_user(role=UserRole.SUPPLIER)

    response = await client.get("/tickets", headers=auth_header_for_user(supplier))
    assert response.status_code == 403
    assert response.json() == {"detail": "Insufficient permissions."}


# ---------------------------------------------------------------------------
# detalhe do chamado
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_detail_returns_unit_summary(
    client: httpx.AsyncClient,
    create_unit,
    create_user,
    auth_header_for_user,
) -> None:
    unit = create_unit(code="U-DET", name="Unidade Detalhe", city="Fortaleza", state="CE")
    admin = create_user(role=UserRole.ADMIN)

    resp = await client.post("/tickets", headers=auth_header_for_user(admin), json=make_ticket_payload(unit.id))
    ticket_id = resp.json()["id"]

    response = await client.get(f"/tickets/{ticket_id}", headers=auth_header_for_user(admin))
    assert response.status_code == 200
    data = response.json()
    assert data["unit"] is not None
    assert data["unit"]["code"] == "U-DET"
    assert data["unit"]["name"] == "Unidade Detalhe"
    assert data["unit"]["city"] == "Fortaleza"
    assert data["unit"]["state"] == "CE"


@pytest.mark.anyio
async def test_detail_returns_opened_by_summary(
    client: httpx.AsyncClient,
    create_unit,
    create_user,
    auth_header_for_user,
) -> None:
    unit = create_unit()
    admin = create_user(name="Fabio Engenheiro", role=UserRole.ADMIN)

    resp = await client.post("/tickets", headers=auth_header_for_user(admin), json=make_ticket_payload(unit.id))
    ticket_id = resp.json()["id"]

    response = await client.get(f"/tickets/{ticket_id}", headers=auth_header_for_user(admin))
    assert response.status_code == 200
    data = response.json()
    assert data["opened_by"] is not None
    assert data["opened_by"]["name"] == "Fabio Engenheiro"
    assert data["opened_by"]["id"] == admin.id


@pytest.mark.anyio
async def test_detail_returns_history(
    client: httpx.AsyncClient,
    create_unit,
    create_user,
    auth_header_for_user,
) -> None:
    unit = create_unit()
    admin = create_user(role=UserRole.ADMIN)

    resp = await client.post("/tickets", headers=auth_header_for_user(admin), json=make_ticket_payload(unit.id))
    ticket_id = resp.json()["id"]

    response = await client.get(f"/tickets/{ticket_id}", headers=auth_header_for_user(admin))
    assert response.status_code == 200
    data = response.json()
    assert "history" in data
    assert len(data["history"]) >= 1
    first = data["history"][0]
    assert first["new_status"] == "open"
    assert first["old_status"] is None
    assert first["comment"] == "Chamado aberto"
    assert first["user_id"] == admin.id


@pytest.mark.anyio
async def test_detail_calculates_elapsed_hours(
    client: httpx.AsyncClient,
    create_unit,
    create_user,
    auth_header_for_user,
) -> None:
    unit = create_unit()
    admin = create_user(role=UserRole.ADMIN)

    resp = await client.post("/tickets", headers=auth_header_for_user(admin), json=make_ticket_payload(unit.id))
    ticket_id = resp.json()["id"]

    response = await client.get(f"/tickets/{ticket_id}", headers=auth_header_for_user(admin))
    assert response.status_code == 200
    indicators = response.json()["indicators"]
    assert indicators["elapsed_hours"] is not None
    assert indicators["elapsed_hours"] >= 0


@pytest.mark.anyio
async def test_detail_is_late_false_when_no_sla(
    client: httpx.AsyncClient,
    create_unit,
    create_user,
    auth_header_for_user,
) -> None:
    unit = create_unit()
    admin = create_user(role=UserRole.ADMIN)

    resp = await client.post("/tickets", headers=auth_header_for_user(admin), json=make_ticket_payload(unit.id))
    ticket_id = resp.json()["id"]

    response = await client.get(f"/tickets/{ticket_id}", headers=auth_header_for_user(admin))
    assert response.status_code == 200
    indicators = response.json()["indicators"]
    assert indicators["is_late"] is False
    assert indicators["sla_status"] == "no_sla"


@pytest.mark.anyio
async def test_detail_is_late_true_when_sla_past(
    client: httpx.AsyncClient,
    db_session,
    create_unit,
    create_user,
    auth_header_for_user,
) -> None:
    unit = create_unit()
    admin = create_user(role=UserRole.ADMIN)

    resp = await client.post("/tickets", headers=auth_header_for_user(admin), json=make_ticket_payload(unit.id))
    ticket_id = resp.json()["id"]

    past = datetime.now(UTC) - timedelta(days=3)
    ticket = db_session.get(Ticket, ticket_id)
    ticket.sla_due_at = past
    db_session.commit()

    response = await client.get(f"/tickets/{ticket_id}", headers=auth_header_for_user(admin))
    assert response.status_code == 200
    indicators = response.json()["indicators"]
    assert indicators["is_late"] is True
    assert indicators["sla_status"] == "late"


@pytest.mark.anyio
async def test_detail_sla_status_on_track(
    client: httpx.AsyncClient,
    db_session,
    create_unit,
    create_user,
    auth_header_for_user,
) -> None:
    unit = create_unit()
    admin = create_user(role=UserRole.ADMIN)

    resp = await client.post("/tickets", headers=auth_header_for_user(admin), json=make_ticket_payload(unit.id))
    ticket_id = resp.json()["id"]

    future = datetime.now(UTC) + timedelta(days=10)
    ticket = db_session.get(Ticket, ticket_id)
    ticket.sla_due_at = future
    db_session.commit()

    response = await client.get(f"/tickets/{ticket_id}", headers=auth_header_for_user(admin))
    assert response.status_code == 200
    indicators = response.json()["indicators"]
    assert indicators["is_late"] is False
    assert indicators["sla_status"] == "on_track"


@pytest.mark.anyio
async def test_detail_sla_status_closed_for_final_status(
    client: httpx.AsyncClient,
    db_session,
    create_unit,
    create_user,
    auth_header_for_user,
) -> None:
    unit = create_unit()
    admin = create_user(role=UserRole.ADMIN)

    resp = await client.post("/tickets", headers=auth_header_for_user(admin), json=make_ticket_payload(unit.id))
    ticket_id = resp.json()["id"]

    past = datetime.now(UTC) - timedelta(days=1)
    ticket = db_session.get(Ticket, ticket_id)
    ticket.sla_due_at = past
    ticket.status = TicketStatus.CLOSED
    db_session.commit()

    response = await client.get(f"/tickets/{ticket_id}", headers=auth_header_for_user(admin))
    assert response.status_code == 200
    indicators = response.json()["indicators"]
    assert indicators["is_late"] is False
    assert indicators["sla_status"] == "closed"


@pytest.mark.anyio
async def test_detail_404_for_missing_ticket(
    client: httpx.AsyncClient,
    create_user,
    auth_header_for_user,
) -> None:
    admin = create_user(role=UserRole.ADMIN)

    response = await client.get("/tickets/99999", headers=auth_header_for_user(admin))
    assert response.status_code == 404
    assert response.json() == {"detail": "Ticket not found."}


@pytest.mark.anyio
async def test_detail_permission_enforced(
    client: httpx.AsyncClient,
    create_unit,
    create_user,
    auth_header_for_user,
) -> None:
    own_unit = create_unit(code="U-OWN")
    other_unit = create_unit(code="U-OTHER", name="Outra", city="Rio")
    admin = create_user(role=UserRole.ADMIN)
    manager = create_user(
        name="Gerente Centro",
        email="gerente.centro@local.test",
        role=UserRole.MANAGER,
        unit_id=own_unit.id,
    )

    resp = await client.post(
        "/tickets",
        headers=auth_header_for_user(admin),
        json=make_ticket_payload(other_unit.id),
    )
    ticket_id = resp.json()["id"]

    forbidden = await client.get(f"/tickets/{ticket_id}", headers=auth_header_for_user(manager))
    assert forbidden.status_code == 403

    allowed = await client.get(f"/tickets/{ticket_id}", headers=auth_header_for_user(admin))
    assert allowed.status_code == 200


@pytest.mark.anyio
async def test_supplier_cannot_access_detail(
    client: httpx.AsyncClient,
    create_unit,
    create_user,
    auth_header_for_user,
) -> None:
    unit = create_unit()
    admin = create_user(role=UserRole.ADMIN)
    supplier = create_user(
        name="Fornecedor X",
        email="fornecedor@local.test",
        role=UserRole.SUPPLIER,
    )

    resp = await client.post("/tickets", headers=auth_header_for_user(admin), json=make_ticket_payload(unit.id))
    ticket_id = resp.json()["id"]

    response = await client.get(f"/tickets/{ticket_id}", headers=auth_header_for_user(supplier))
    assert response.status_code == 403
