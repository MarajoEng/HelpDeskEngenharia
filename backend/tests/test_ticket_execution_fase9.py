"""FASE 9 — testes do fluxo de execucao de chamados."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta

import httpx
import pytest

from app.models.enums import TicketStatus, UserRole
from app.models.supplier import Supplier
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
        "requires_approval": False,
    }
    payload.update(overrides)
    return payload


def create_supplier_in_db(db_session, **overrides: object) -> Supplier:
    data = {
        "name": "Fornecedor Execucao",
        "document": "12.345.678/0001-99",
        "phone": "(11) 99999-0001",
        "email": "exec@fornecedor.com",
        "specialty": "Manutencao hidraulica",
        "is_active": True,
    }
    data.update(overrides)
    supplier = Supplier(**data)
    db_session.add(supplier)
    db_session.commit()
    db_session.refresh(supplier)
    return supplier


def _create_ticket_at_triage(db_session, unit_id: int, opened_by_user_id: int, **overrides: object) -> Ticket:
    ticket = Ticket(
        ticket_number="ENG-20260625-000001",
        unit_id=unit_id,
        opened_by_user_id=opened_by_user_id,
        assigned_to_user_id=None,
        category="fuel_pump",
        problem_type="Falha",
        title="Bomba parada",
        description="Descricao do problema",
        priority="high",
        severity="critical",
        status=TicketStatus.TRIAGE,
        requires_approval=False,
        opened_at=datetime.now(UTC),
        triaged_at=datetime.now(UTC),
        expected_resolution_at=None,
        supplier_id=None,
    )
    for k, v in overrides.items():
        setattr(ticket, k, v)
    db_session.add(ticket)
    db_session.commit()
    db_session.refresh(ticket)
    return ticket


def _create_ticket_at_approved(db_session, unit_id: int, opened_by_user_id: int) -> Ticket:
    ticket = Ticket(
        ticket_number="ENG-20260625-000002",
        unit_id=unit_id,
        opened_by_user_id=opened_by_user_id,
        assigned_to_user_id=None,
        category="fuel_pump",
        problem_type="Falha",
        title="Bomba aprovada",
        description="Descricao",
        priority="high",
        severity="critical",
        status=TicketStatus.APPROVED,
        requires_approval=True,
        opened_at=datetime.now(UTC),
        triaged_at=datetime.now(UTC),
        approved_at=datetime.now(UTC),
        expected_resolution_at=None,
        supplier_id=None,
    )
    db_session.add(ticket)
    db_session.commit()
    db_session.refresh(ticket)
    return ticket


# ---------------------------------------------------------------------------
# PATCH /tickets/{id}/start-execution
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_start_execution_from_triage_no_approval(
    client: httpx.AsyncClient,
    db_session,
    create_unit,
    create_user,
    auth_header_for_user,
) -> None:
    unit = create_unit()
    admin = create_user(role=UserRole.ADMIN)
    ticket = _create_ticket_at_triage(db_session, unit.id, admin.id)
    future = (datetime.now(UTC) + timedelta(days=3)).isoformat()
    payload = {"execution_comment": "Iniciando execucao do chamado.", "expected_resolution_at": future}
    response = await client.patch(
        f"/tickets/{ticket.id}/start-execution",
        headers=auth_header_for_user(admin),
        json=payload,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "in_progress"
    assert data["started_at"] is not None
    assert data["expected_resolution_at"] is not None


@pytest.mark.anyio
async def test_start_execution_from_approved_with_approval(
    client: httpx.AsyncClient,
    db_session,
    create_unit,
    create_user,
    auth_header_for_user,
) -> None:
    unit = create_unit()
    admin = create_user(role=UserRole.ADMIN)
    ticket = _create_ticket_at_approved(db_session, unit.id, admin.id)
    payload = {"execution_comment": "Aprovado e iniciando execucao."}
    response = await client.patch(
        f"/tickets/{ticket.id}/start-execution",
        headers=auth_header_for_user(admin),
        json=payload,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "in_progress"


@pytest.mark.anyio
async def test_start_execution_creates_history(
    client: httpx.AsyncClient,
    db_session,
    create_unit,
    create_user,
    auth_header_for_user,
) -> None:
    unit = create_unit()
    admin = create_user(role=UserRole.ADMIN)
    ticket = _create_ticket_at_triage(db_session, unit.id, admin.id)
    payload = {"execution_comment": "Iniciando execucao."}
    response = await client.patch(
        f"/tickets/{ticket.id}/start-execution",
        headers=auth_header_for_user(admin),
        json=payload,
    )
    assert response.status_code == 200
    history = response.json()["history"]
    last = history[-1]
    assert last["new_status"] == "in_progress"
    assert last["comment"] == "Iniciando execucao."


@pytest.mark.anyio
async def test_start_execution_with_supplier(
    client: httpx.AsyncClient,
    db_session,
    create_unit,
    create_user,
    auth_header_for_user,
) -> None:
    unit = create_unit()
    admin = create_user(role=UserRole.ADMIN)
    supplier = create_supplier_in_db(db_session)
    ticket = _create_ticket_at_triage(db_session, unit.id, admin.id)
    payload = {"execution_comment": "Com fornecedor.", "supplier_id": supplier.id}
    response = await client.patch(
        f"/tickets/{ticket.id}/start-execution",
        headers=auth_header_for_user(admin),
        json=payload,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["supplier_id"] == supplier.id
    assert data["supplier"]["name"] == supplier.name


@pytest.mark.anyio
async def test_start_execution_with_assigned_user(
    client: httpx.AsyncClient,
    db_session,
    create_unit,
    create_user,
    auth_header_for_user,
) -> None:
    unit = create_unit()
    admin = create_user(role=UserRole.ADMIN)
    eng = create_user(role=UserRole.ENGINEERING, email="eng_exec@local.test")
    ticket = _create_ticket_at_triage(db_session, unit.id, admin.id)
    payload = {"execution_comment": "Atribuindo responsavel.", "assigned_to_user_id": eng.id}
    response = await client.patch(
        f"/tickets/{ticket.id}/start-execution",
        headers=auth_header_for_user(admin),
        json=payload,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["assigned_to_user_id"] == eng.id


@pytest.mark.anyio
async def test_start_execution_fails_from_open(
    client: httpx.AsyncClient,
    db_session,
    create_unit,
    create_user,
    auth_header_for_user,
) -> None:
    unit = create_unit()
    admin = create_user(role=UserRole.ADMIN)
    ticket = _create_ticket_at_triage(db_session, unit.id, admin.id, status=TicketStatus.OPEN)
    payload = {"execution_comment": "Nao pode executar de open."}
    response = await client.patch(
        f"/tickets/{ticket.id}/start-execution",
        headers=auth_header_for_user(admin),
        json=payload,
    )
    assert response.status_code == 409


@pytest.mark.anyio
async def test_start_execution_fails_triage_requires_approval(
    client: httpx.AsyncClient,
    db_session,
    create_unit,
    create_user,
    auth_header_for_user,
) -> None:
    unit = create_unit()
    admin = create_user(role=UserRole.ADMIN)
    ticket = _create_ticket_at_triage(db_session, unit.id, admin.id, requires_approval=True)
    payload = {"execution_comment": "Requer aprovacao, nao pode."}
    response = await client.patch(
        f"/tickets/{ticket.id}/start-execution",
        headers=auth_header_for_user(admin),
        json=payload,
    )
    assert response.status_code == 409


@pytest.mark.anyio
async def test_start_execution_permission_denied_for_director(
    client: httpx.AsyncClient,
    db_session,
    create_unit,
    create_user,
    auth_header_for_user,
) -> None:
    unit = create_unit()
    admin = create_user(role=UserRole.ADMIN)
    director = create_user(role=UserRole.DIRECTOR, email="dir@local.test")
    ticket = _create_ticket_at_triage(db_session, unit.id, admin.id)
    payload = {"execution_comment": "Diretor nao pode iniciar execucao."}
    response = await client.patch(
        f"/tickets/{ticket.id}/start-execution",
        headers=auth_header_for_user(director),
        json=payload,
    )
    assert response.status_code == 403


@pytest.mark.anyio
async def test_start_execution_inactive_supplier_rejected(
    client: httpx.AsyncClient,
    db_session,
    create_unit,
    create_user,
    auth_header_for_user,
) -> None:
    unit = create_unit()
    admin = create_user(role=UserRole.ADMIN)
    supplier = create_supplier_in_db(db_session, is_active=False, document="99.999.999/0001-99", email="inativo@test.com")
    ticket = _create_ticket_at_triage(db_session, unit.id, admin.id)
    payload = {"execution_comment": "Fornecedor inativo.", "supplier_id": supplier.id}
    response = await client.patch(
        f"/tickets/{ticket.id}/start-execution",
        headers=auth_header_for_user(admin),
        json=payload,
    )
    assert response.status_code == 422


@pytest.mark.anyio
async def test_start_execution_nonexistent_supplier_rejected(
    client: httpx.AsyncClient,
    db_session,
    create_unit,
    create_user,
    auth_header_for_user,
) -> None:
    unit = create_unit()
    admin = create_user(role=UserRole.ADMIN)
    ticket = _create_ticket_at_triage(db_session, unit.id, admin.id)
    payload = {"execution_comment": "Fornecedor nao existe.", "supplier_id": 9999}
    response = await client.patch(
        f"/tickets/{ticket.id}/start-execution",
        headers=auth_header_for_user(admin),
        json=payload,
    )
    assert response.status_code == 422


@pytest.mark.anyio
async def test_start_execution_expected_date_in_past_rejected(
    client: httpx.AsyncClient,
    db_session,
    create_unit,
    create_user,
    auth_header_for_user,
) -> None:
    unit = create_unit()
    admin = create_user(role=UserRole.ADMIN)
    ticket = _create_ticket_at_triage(db_session, unit.id, admin.id)
    past = (datetime.now(UTC) - timedelta(hours=1)).isoformat()
    payload = {"execution_comment": "Data no passado.", "expected_resolution_at": past}
    response = await client.patch(
        f"/tickets/{ticket.id}/start-execution",
        headers=auth_header_for_user(admin),
        json=payload,
    )
    assert response.status_code == 422


@pytest.mark.anyio
async def test_start_execution_comment_required(
    client: httpx.AsyncClient,
    db_session,
    create_unit,
    create_user,
    auth_header_for_user,
) -> None:
    unit = create_unit()
    admin = create_user(role=UserRole.ADMIN)
    ticket = _create_ticket_at_triage(db_session, unit.id, admin.id)
    response = await client.patch(
        f"/tickets/{ticket.id}/start-execution",
        headers=auth_header_for_user(admin),
        json={},
    )
    assert response.status_code == 422


@pytest.mark.anyio
async def test_start_execution_not_found(
    client: httpx.AsyncClient,
    create_user,
    auth_header_for_user,
) -> None:
    admin = create_user(role=UserRole.ADMIN)
    response = await client.patch(
        "/tickets/9999/start-execution",
        headers=auth_header_for_user(admin),
        json={"execution_comment": "Nao existe."},
    )
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# PATCH /tickets/{id}/progress
# ---------------------------------------------------------------------------


def _create_ticket_in_progress(db_session, unit_id: int, opened_by_user_id: int, **overrides: object) -> Ticket:
    ticket = Ticket(
        ticket_number="ENG-20260625-000003",
        unit_id=unit_id,
        opened_by_user_id=opened_by_user_id,
        assigned_to_user_id=None,
        category="fuel_pump",
        problem_type="Falha",
        title="Execucao em andamento",
        description="Descricao",
        priority="high",
        severity="critical",
        status=TicketStatus.IN_PROGRESS,
        requires_approval=False,
        opened_at=datetime.now(UTC),
        started_at=datetime.now(UTC),
        triaged_at=datetime.now(UTC),
        expected_resolution_at=None,
        supplier_id=None,
    )
    for k, v in overrides.items():
        setattr(ticket, k, v)
    db_session.add(ticket)
    db_session.commit()
    db_session.refresh(ticket)
    return ticket


@pytest.mark.anyio
async def test_progress_update_success(
    client: httpx.AsyncClient,
    db_session,
    create_unit,
    create_user,
    auth_header_for_user,
) -> None:
    unit = create_unit()
    admin = create_user(role=UserRole.ADMIN)
    ticket = _create_ticket_in_progress(db_session, unit.id, admin.id)
    payload = {"progress_comment": "Pecas substituidas, aguardando teste."}
    response = await client.patch(
        f"/tickets/{ticket.id}/progress",
        headers=auth_header_for_user(admin),
        json=payload,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "in_progress"


@pytest.mark.anyio
async def test_progress_update_creates_history_in_progress_to_in_progress(
    client: httpx.AsyncClient,
    db_session,
    create_unit,
    create_user,
    auth_header_for_user,
) -> None:
    unit = create_unit()
    admin = create_user(role=UserRole.ADMIN)
    ticket = _create_ticket_in_progress(db_session, unit.id, admin.id)
    payload = {"progress_comment": "Progresso registrado."}
    response = await client.patch(
        f"/tickets/{ticket.id}/progress",
        headers=auth_header_for_user(admin),
        json=payload,
    )
    assert response.status_code == 200
    history = response.json()["history"]
    last = history[-1]
    assert last["old_status"] == "in_progress"
    assert last["new_status"] == "in_progress"
    assert last["comment"] == "Progresso registrado."


@pytest.mark.anyio
async def test_progress_update_updates_expected_resolution(
    client: httpx.AsyncClient,
    db_session,
    create_unit,
    create_user,
    auth_header_for_user,
) -> None:
    unit = create_unit()
    admin = create_user(role=UserRole.ADMIN)
    ticket = _create_ticket_in_progress(db_session, unit.id, admin.id)
    future = (datetime.now(UTC) + timedelta(days=5)).isoformat()
    payload = {"progress_comment": "Nova previsao.", "expected_resolution_at": future}
    response = await client.patch(
        f"/tickets/{ticket.id}/progress",
        headers=auth_header_for_user(admin),
        json=payload,
    )
    assert response.status_code == 200
    assert response.json()["expected_resolution_at"] is not None


@pytest.mark.anyio
async def test_progress_update_updates_estimated_cost(
    client: httpx.AsyncClient,
    db_session,
    create_unit,
    create_user,
    auth_header_for_user,
) -> None:
    unit = create_unit()
    admin = create_user(role=UserRole.ADMIN)
    ticket = _create_ticket_in_progress(db_session, unit.id, admin.id)
    payload = {"progress_comment": "Custo revisado.", "estimated_cost": "3500.00"}
    response = await client.patch(
        f"/tickets/{ticket.id}/progress",
        headers=auth_header_for_user(admin),
        json=payload,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["estimated_cost"] == "3500.00"


@pytest.mark.anyio
async def test_progress_update_with_supplier(
    client: httpx.AsyncClient,
    db_session,
    create_unit,
    create_user,
    auth_header_for_user,
) -> None:
    unit = create_unit()
    admin = create_user(role=UserRole.ADMIN)
    supplier = create_supplier_in_db(db_session)
    ticket = _create_ticket_in_progress(db_session, unit.id, admin.id)
    payload = {"progress_comment": "Fornecedor atribuido.", "supplier_id": supplier.id}
    response = await client.patch(
        f"/tickets/{ticket.id}/progress",
        headers=auth_header_for_user(admin),
        json=payload,
    )
    assert response.status_code == 200
    assert response.json()["supplier_id"] == supplier.id


@pytest.mark.anyio
async def test_progress_fails_if_not_in_progress(
    client: httpx.AsyncClient,
    db_session,
    create_unit,
    create_user,
    auth_header_for_user,
) -> None:
    unit = create_unit()
    admin = create_user(role=UserRole.ADMIN)
    ticket = _create_ticket_at_triage(db_session, unit.id, admin.id)
    payload = {"progress_comment": "Nao pode, nao esta em execucao."}
    response = await client.patch(
        f"/tickets/{ticket.id}/progress",
        headers=auth_header_for_user(admin),
        json=payload,
    )
    assert response.status_code == 409


@pytest.mark.anyio
async def test_progress_comment_required(
    client: httpx.AsyncClient,
    db_session,
    create_unit,
    create_user,
    auth_header_for_user,
) -> None:
    unit = create_unit()
    admin = create_user(role=UserRole.ADMIN)
    ticket = _create_ticket_in_progress(db_session, unit.id, admin.id)
    response = await client.patch(
        f"/tickets/{ticket.id}/progress",
        headers=auth_header_for_user(admin),
        json={},
    )
    assert response.status_code == 422


@pytest.mark.anyio
async def test_progress_expected_date_in_past_rejected(
    client: httpx.AsyncClient,
    db_session,
    create_unit,
    create_user,
    auth_header_for_user,
) -> None:
    unit = create_unit()
    admin = create_user(role=UserRole.ADMIN)
    ticket = _create_ticket_in_progress(db_session, unit.id, admin.id)
    past = (datetime.now(UTC) - timedelta(hours=1)).isoformat()
    payload = {"progress_comment": "Data no passado.", "expected_resolution_at": past}
    response = await client.patch(
        f"/tickets/{ticket.id}/progress",
        headers=auth_header_for_user(admin),
        json=payload,
    )
    assert response.status_code == 422


@pytest.mark.anyio
async def test_progress_permission_denied_for_manager(
    client: httpx.AsyncClient,
    db_session,
    create_unit,
    create_user,
    auth_header_for_user,
) -> None:
    unit = create_unit()
    admin = create_user(role=UserRole.ADMIN)
    manager = create_user(role=UserRole.MANAGER, email="mgr2@local.test", unit_id=unit.id)
    ticket = _create_ticket_in_progress(db_session, unit.id, admin.id)
    payload = {"progress_comment": "Manager nao pode."}
    response = await client.patch(
        f"/tickets/{ticket.id}/progress",
        headers=auth_header_for_user(manager),
        json=payload,
    )
    assert response.status_code == 403


@pytest.mark.anyio
async def test_progress_inactive_supplier_rejected(
    client: httpx.AsyncClient,
    db_session,
    create_unit,
    create_user,
    auth_header_for_user,
) -> None:
    unit = create_unit()
    admin = create_user(role=UserRole.ADMIN)
    supplier = create_supplier_in_db(db_session, is_active=False, document="88.888.888/0001-88", email="inativo2@test.com")
    ticket = _create_ticket_in_progress(db_session, unit.id, admin.id)
    payload = {"progress_comment": "Fornecedor inativo.", "supplier_id": supplier.id}
    response = await client.patch(
        f"/tickets/{ticket.id}/progress",
        headers=auth_header_for_user(admin),
        json=payload,
    )
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Indicadores de execucao
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_execution_indicators_in_progress(
    client: httpx.AsyncClient,
    db_session,
    create_unit,
    create_user,
    auth_header_for_user,
) -> None:
    unit = create_unit()
    admin = create_user(role=UserRole.ADMIN)
    ticket = _create_ticket_in_progress(db_session, unit.id, admin.id)
    response = await client.get(f"/tickets/{ticket.id}", headers=auth_header_for_user(admin))
    assert response.status_code == 200
    indicators = response.json()["indicators"]
    assert indicators["elapsed_execution_hours"] is not None
    assert indicators["elapsed_execution_hours"] >= 0
    assert indicators["execution_is_late"] is False


@pytest.mark.anyio
async def test_execution_is_late_when_expected_passed(
    client: httpx.AsyncClient,
    db_session,
    create_unit,
    create_user,
    auth_header_for_user,
) -> None:
    unit = create_unit()
    admin = create_user(role=UserRole.ADMIN)
    past_expected = datetime.now(UTC) - timedelta(hours=2)
    ticket = _create_ticket_in_progress(db_session, unit.id, admin.id, expected_resolution_at=past_expected)
    response = await client.get(f"/tickets/{ticket.id}", headers=auth_header_for_user(admin))
    assert response.status_code == 200
    indicators = response.json()["indicators"]
    assert indicators["execution_is_late"] is True


@pytest.mark.anyio
async def test_execution_indicators_not_set_when_not_in_progress(
    client: httpx.AsyncClient,
    db_session,
    create_unit,
    create_user,
    auth_header_for_user,
) -> None:
    unit = create_unit()
    admin = create_user(role=UserRole.ADMIN)
    ticket = _create_ticket_at_triage(db_session, unit.id, admin.id)
    response = await client.get(f"/tickets/{ticket.id}", headers=auth_header_for_user(admin))
    assert response.status_code == 200
    indicators = response.json()["indicators"]
    assert indicators["elapsed_execution_hours"] is None
    assert indicators["execution_is_late"] is False


# ---------------------------------------------------------------------------
# Campos de execucao na listagem
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_list_returns_supplier_id_and_expected_resolution_at(
    client: httpx.AsyncClient,
    db_session,
    create_unit,
    create_user,
    auth_header_for_user,
) -> None:
    unit = create_unit()
    admin = create_user(role=UserRole.ADMIN)
    supplier = create_supplier_in_db(db_session)
    future = datetime.now(UTC) + timedelta(days=2)
    _create_ticket_in_progress(
        db_session,
        unit.id,
        admin.id,
        ticket_number="ENG-20260625-000010",
        supplier_id=supplier.id,
        expected_resolution_at=future,
    )
    response = await client.get("/tickets", headers=auth_header_for_user(admin))
    assert response.status_code == 200
    item = response.json()["items"][0]
    assert item["supplier_id"] == supplier.id
    assert item["supplier_name"] == supplier.name
    assert item["expected_resolution_at"] is not None
