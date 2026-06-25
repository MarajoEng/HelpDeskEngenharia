"""FASE 7 — testes de triagem da engenharia."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta

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


def make_triage_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "technical_comment": "Analise tecnica iniciada pela engenharia central.",
    }
    payload.update(overrides)
    return payload


def parse_iso_datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed.replace(tzinfo=UTC) if parsed.tzinfo is None else parsed.astimezone(UTC)


@pytest.mark.anyio
async def test_engineering_triages_open_ticket_and_returns_updated_detail(
    client: httpx.AsyncClient,
    db_session,
    create_unit,
    create_user,
    auth_header_for_user,
) -> None:
    unit = create_unit()
    admin = create_user(role=UserRole.ADMIN)
    engineering = create_user(
        name="Eng Responsavel",
        email="eng.responsavel@local.test",
        role=UserRole.ENGINEERING,
    )
    owner = create_user(
        name="Eng Owner",
        email="eng.owner@local.test",
        role=UserRole.ENGINEERING,
    )

    created = await client.post(
        "/tickets",
        headers=auth_header_for_user(admin),
        json=make_ticket_payload(unit.id),
    )
    ticket_id = created.json()["id"]
    sla_due_at = (datetime.now(UTC) + timedelta(hours=6)).isoformat()

    response = await client.patch(
        f"/tickets/{ticket_id}/triage",
        headers=auth_header_for_user(engineering),
        json=make_triage_payload(
            assigned_to_user_id=owner.id,
            priority="medium",
            severity="high",
            requires_approval=False,
            sla_due_at=sla_due_at,
        ),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == ticket_id
    assert data["status"] == "triage"
    assert data["assigned_to_user_id"] == owner.id
    assert data["assigned_to"]["id"] == owner.id
    assert data["priority"] == "medium"
    assert data["severity"] == "high"
    assert data["requires_approval"] is False
    assert data["triaged_at"] is not None
    assert data["sla_due_at"] is not None
    assert data["history"][-1]["old_status"] == "open"
    assert data["history"][-1]["new_status"] == "triage"
    assert data["history"][-1]["comment"] == "Analise tecnica iniciada pela engenharia central."
    assert data["history"][-1]["user_id"] == engineering.id

    ticket = db_session.get(Ticket, ticket_id)
    assert ticket is not None
    assert ticket.status == TicketStatus.TRIAGE
    assert ticket.triaged_at is not None
    assert ticket.assigned_to_user_id == owner.id


@pytest.mark.anyio
async def test_admin_triages_open_ticket(
    client: httpx.AsyncClient,
    create_unit,
    create_user,
    auth_header_for_user,
) -> None:
    unit = create_unit()
    admin = create_user(role=UserRole.ADMIN)

    created = await client.post(
        "/tickets",
        headers=auth_header_for_user(admin),
        json=make_ticket_payload(unit.id),
    )

    response = await client.patch(
        f"/tickets/{created.json()['id']}/triage",
        headers=auth_header_for_user(admin),
        json=make_triage_payload(),
    )

    assert response.status_code == 200
    assert response.json()["status"] == "triage"


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("role", "email"),
    [
        (UserRole.DIRECTOR, "director@local.test"),
        (UserRole.MANAGER, "manager@local.test"),
        (UserRole.SUPPLIER, "supplier@local.test"),
    ],
)
async def test_roles_without_triage_permission_are_blocked(
    client: httpx.AsyncClient,
    create_unit,
    create_user,
    auth_header_for_user,
    role: UserRole,
    email: str,
) -> None:
    unit = create_unit()
    admin = create_user(role=UserRole.ADMIN)
    if role == UserRole.MANAGER:
        actor = create_user(email=email, role=role, unit_id=unit.id)
    else:
        actor = create_user(email=email, role=role)

    created = await client.post(
        "/tickets",
        headers=auth_header_for_user(admin),
        json=make_ticket_payload(unit.id),
    )

    response = await client.patch(
        f"/tickets/{created.json()['id']}/triage",
        headers=auth_header_for_user(actor),
        json=make_triage_payload(),
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "Insufficient permissions."}


@pytest.mark.anyio
async def test_triage_missing_ticket_returns_404(
    client: httpx.AsyncClient,
    create_user,
    auth_header_for_user,
) -> None:
    engineering = create_user(role=UserRole.ENGINEERING)

    response = await client.patch(
        "/tickets/99999/triage",
        headers=auth_header_for_user(engineering),
        json=make_triage_payload(),
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Ticket not found."}


@pytest.mark.anyio
@pytest.mark.parametrize(
    "blocked_status",
    [TicketStatus.CLOSED, TicketStatus.RESOLVED, TicketStatus.CANCELED],
)
async def test_triage_blocks_closed_resolved_and_canceled(
    client: httpx.AsyncClient,
    db_session,
    create_unit,
    create_user,
    auth_header_for_user,
    blocked_status: TicketStatus,
) -> None:
    unit = create_unit()
    admin = create_user(role=UserRole.ADMIN)
    engineering = create_user(
        email=f"eng.{blocked_status.value}@local.test",
        role=UserRole.ENGINEERING,
    )

    created = await client.post(
        "/tickets",
        headers=auth_header_for_user(admin),
        json=make_ticket_payload(unit.id),
    )
    ticket = db_session.get(Ticket, created.json()["id"])
    assert ticket is not None
    ticket.status = blocked_status
    db_session.commit()

    response = await client.patch(
        f"/tickets/{ticket.id}/triage",
        headers=auth_header_for_user(engineering),
        json=make_triage_payload(),
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "Ticket cannot be triaged from the current status."}


@pytest.mark.anyio
@pytest.mark.parametrize(
    "blocked_status",
    [TicketStatus.WAITING_APPROVAL, TicketStatus.IN_PROGRESS],
)
async def test_triage_blocks_waiting_approval_and_in_progress(
    client: httpx.AsyncClient,
    db_session,
    create_unit,
    create_user,
    auth_header_for_user,
    blocked_status: TicketStatus,
) -> None:
    unit = create_unit()
    admin = create_user(role=UserRole.ADMIN)
    engineering = create_user(
        email=f"eng.block.{blocked_status.value}@local.test",
        role=UserRole.ENGINEERING,
    )

    created = await client.post(
        "/tickets",
        headers=auth_header_for_user(admin),
        json=make_ticket_payload(unit.id),
    )
    ticket = db_session.get(Ticket, created.json()["id"])
    assert ticket is not None
    ticket.status = blocked_status
    db_session.commit()

    response = await client.patch(
        f"/tickets/{ticket.id}/triage",
        headers=auth_header_for_user(engineering),
        json=make_triage_payload(),
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "Ticket cannot be triaged from the current status."}


@pytest.mark.anyio
async def test_triage_from_waiting_unit_moves_back_to_triage(
    client: httpx.AsyncClient,
    db_session,
    create_unit,
    create_user,
    auth_header_for_user,
) -> None:
    unit = create_unit()
    admin = create_user(role=UserRole.ADMIN)
    engineering = create_user(role=UserRole.ENGINEERING, email="eng.waiting.unit@local.test")

    created = await client.post(
        "/tickets",
        headers=auth_header_for_user(admin),
        json=make_ticket_payload(unit.id),
    )
    ticket = db_session.get(Ticket, created.json()["id"])
    assert ticket is not None
    ticket.status = TicketStatus.WAITING_UNIT
    db_session.commit()

    response = await client.patch(
        f"/tickets/{ticket.id}/triage",
        headers=auth_header_for_user(engineering),
        json=make_triage_payload(technical_comment="Retomada tecnica da analise."),
    )

    assert response.status_code == 200
    assert response.json()["status"] == "triage"
    assert response.json()["history"][-1]["old_status"] == "waiting_unit"


@pytest.mark.anyio
async def test_triage_on_existing_triage_updates_data_adds_history_and_keeps_first_triaged_at(
    client: httpx.AsyncClient,
    db_session,
    create_unit,
    create_user,
    auth_header_for_user,
) -> None:
    unit = create_unit()
    admin = create_user(role=UserRole.ADMIN)

    created = await client.post(
        "/tickets",
        headers=auth_header_for_user(admin),
        json=make_ticket_payload(unit.id),
    )
    ticket_id = created.json()["id"]

    first_response = await client.patch(
        f"/tickets/{ticket_id}/triage",
        headers=auth_header_for_user(admin),
        json=make_triage_payload(priority="critical"),
    )
    first_triaged_at = first_response.json()["triaged_at"]

    second_response = await client.patch(
        f"/tickets/{ticket_id}/triage",
        headers=auth_header_for_user(admin),
        json=make_triage_payload(
            priority="low",
            severity="low",
            requires_approval=False,
            technical_comment="Ajuste de classificacao apos revisao tecnica.",
        ),
    )

    assert second_response.status_code == 200
    data = second_response.json()
    assert data["status"] == "triage"
    assert data["priority"] == "low"
    assert data["severity"] == "low"
    assert data["requires_approval"] is False
    assert parse_iso_datetime(data["triaged_at"]) == parse_iso_datetime(first_triaged_at)
    assert data["history"][-1]["old_status"] == "triage"
    assert data["history"][-1]["new_status"] == "triage"
    assert data["history"][-1]["comment"] == "Ajuste de classificacao apos revisao tecnica."

    history_entries = list(
        db_session.scalars(
            select(TicketHistory)
            .where(TicketHistory.ticket_id == ticket_id)
            .order_by(TicketHistory.id.asc())
        )
    )
    assert len(history_entries) == 3


@pytest.mark.anyio
async def test_triage_blocks_invalid_assigned_user_role_and_missing_user(
    client: httpx.AsyncClient,
    create_unit,
    create_user,
    auth_header_for_user,
) -> None:
    unit = create_unit()
    admin = create_user(role=UserRole.ADMIN)
    manager = create_user(
        email="manager.assignee@local.test",
        role=UserRole.MANAGER,
        unit_id=unit.id,
    )

    created = await client.post(
        "/tickets",
        headers=auth_header_for_user(admin),
        json=make_ticket_payload(unit.id),
    )
    ticket_id = created.json()["id"]

    manager_response = await client.patch(
        f"/tickets/{ticket_id}/triage",
        headers=auth_header_for_user(admin),
        json=make_triage_payload(assigned_to_user_id=manager.id),
    )
    assert manager_response.status_code == 422
    assert manager_response.json() == {"detail": "Assigned user must have admin or engineering role."}

    missing_response = await client.patch(
        f"/tickets/{ticket_id}/triage",
        headers=auth_header_for_user(admin),
        json=make_triage_payload(assigned_to_user_id=99999),
    )
    assert missing_response.status_code == 422
    assert missing_response.json() == {"detail": "Assigned user not found."}


@pytest.mark.anyio
async def test_triage_blocks_past_sla_and_empty_comment(
    client: httpx.AsyncClient,
    create_unit,
    create_user,
    auth_header_for_user,
) -> None:
    unit = create_unit()
    admin = create_user(role=UserRole.ADMIN)

    created = await client.post(
        "/tickets",
        headers=auth_header_for_user(admin),
        json=make_ticket_payload(unit.id),
    )
    ticket_id = created.json()["id"]

    past_response = await client.patch(
        f"/tickets/{ticket_id}/triage",
        headers=auth_header_for_user(admin),
        json=make_triage_payload(
            sla_due_at=(datetime.now(UTC) - timedelta(hours=1)).isoformat(),
        ),
    )
    assert past_response.status_code == 422

    comment_response = await client.patch(
        f"/tickets/{ticket_id}/triage",
        headers=auth_header_for_user(admin),
        json=make_triage_payload(technical_comment="   "),
    )
    assert comment_response.status_code == 422


@pytest.mark.anyio
async def test_engineering_queue_returns_open_triage_and_waiting_unit_only(
    client: httpx.AsyncClient,
    db_session,
    create_unit,
    create_user,
    auth_header_for_user,
) -> None:
    unit = create_unit()
    admin = create_user(role=UserRole.ADMIN)

    open_ticket = await client.post(
        "/tickets",
        headers=auth_header_for_user(admin),
        json=make_ticket_payload(unit.id, title="Aberto"),
    )
    triage_ticket = await client.post(
        "/tickets",
        headers=auth_header_for_user(admin),
        json=make_ticket_payload(unit.id, title="Em triagem"),
    )
    waiting_unit_ticket = await client.post(
        "/tickets",
        headers=auth_header_for_user(admin),
        json=make_ticket_payload(unit.id, title="Aguardando unidade"),
    )
    closed_ticket = await client.post(
        "/tickets",
        headers=auth_header_for_user(admin),
        json=make_ticket_payload(unit.id, title="Fechado"),
    )

    db_session.get(Ticket, triage_ticket.json()["id"]).status = TicketStatus.TRIAGE
    db_session.get(Ticket, waiting_unit_ticket.json()["id"]).status = TicketStatus.WAITING_UNIT
    db_session.get(Ticket, closed_ticket.json()["id"]).status = TicketStatus.CLOSED
    db_session.commit()

    response = await client.get(
        "/tickets?queue=engineering&page=1&page_size=20",
        headers=auth_header_for_user(admin),
    )

    assert response.status_code == 200
    data = response.json()
    statuses = {item["status"] for item in data["items"]}
    ids = {item["id"] for item in data["items"]}

    assert data["total"] == 3
    assert statuses == {"open", "triage", "waiting_unit"}
    assert open_ticket.json()["id"] in ids
    assert triage_ticket.json()["id"] in ids
    assert waiting_unit_ticket.json()["id"] in ids


@pytest.mark.anyio
async def test_triage_assignees_endpoint_returns_active_admin_and_engineering_only(
    client: httpx.AsyncClient,
    create_unit,
    create_user,
    auth_header_for_user,
) -> None:
    unit = create_unit()
    engineering = create_user(role=UserRole.ENGINEERING, email="eng.queue@local.test")
    create_user(role=UserRole.ADMIN, email="admin.triage@local.test", name="Admin Triage")
    create_user(role=UserRole.ENGINEERING, email="eng.active@local.test", name="Engenharia Ativa")
    create_user(role=UserRole.ENGINEERING, email="eng.inactive@local.test", name="Engenharia Inativa", is_active=False)
    create_user(role=UserRole.MANAGER, email="manager.exclude@local.test", unit_id=unit.id, name="Manager Fora")

    response = await client.get(
        "/tickets/triage-assignees?page=1&page_size=20",
        headers=auth_header_for_user(engineering),
    )

    assert response.status_code == 200
    data = response.json()
    roles = {item["role"] for item in data["items"]}
    emails = {item["email"] for item in data["items"]}

    assert data["total"] == 3
    assert roles == {"admin", "engineering"}
    assert "eng.inactive@local.test" not in emails
    assert "manager.exclude@local.test" not in emails


@pytest.mark.anyio
async def test_triage_assignees_endpoint_blocks_non_triage_roles(
    client: httpx.AsyncClient,
    create_unit,
    create_user,
    auth_header_for_user,
) -> None:
    unit = create_unit()
    manager = create_user(role=UserRole.MANAGER, unit_id=unit.id)

    response = await client.get(
        "/tickets/triage-assignees",
        headers=auth_header_for_user(manager),
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "Insufficient permissions."}
