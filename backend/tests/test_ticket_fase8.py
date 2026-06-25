from datetime import UTC, datetime, timedelta

import httpx
import pytest
from sqlalchemy import select

from app.models.approval import Approval
from app.models.enums import ApprovalStatus, TicketStatus, UserRole
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
        "technical_comment": "Analise tecnica inicial.",
    }
    payload.update(overrides)
    return payload


def make_approval_request_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "amount_requested": "800.00",
        "justification": "A intervencao exige aprovacao de custo.",
    }
    payload.update(overrides)
    return payload


def make_approval_decision_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "decision": "approved",
        "amount_approved": "800.00",
        "justification": "Valor aprovado dentro da alcada configurada.",
    }
    payload.update(overrides)
    return payload


async def create_triaged_ticket(
    client: httpx.AsyncClient,
    unit_id: int,
    creator,
    triage_actor,
    auth_header_for_user,
    *,
    requires_approval: bool = True,
) -> int:
    created = await client.post(
        "/tickets",
        headers=auth_header_for_user(creator),
        json=make_ticket_payload(unit_id, requires_approval=requires_approval),
    )
    ticket_id = created.json()["id"]
    triage_response = await client.patch(
        f"/tickets/{ticket_id}/triage",
        headers=auth_header_for_user(triage_actor),
        json=make_triage_payload(
            requires_approval=requires_approval,
            sla_due_at=(datetime.now(UTC) + timedelta(hours=4)).isoformat(),
        ),
    )
    assert triage_response.status_code == 200
    return ticket_id


@pytest.mark.anyio
async def test_engineering_requests_approval_with_active_level_and_links_correct_level(
    client: httpx.AsyncClient,
    db_session,
    create_unit,
    create_user,
    create_approval_level,
    auth_header_for_user,
) -> None:
    unit = create_unit()
    admin = create_user(role=UserRole.ADMIN)
    engineering = create_user(role=UserRole.ENGINEERING, email="eng.approval@local.test")
    level = create_approval_level(
        name="Engenharia ate 1000",
        min_amount="0.00",
        max_amount="1000.00",
        allowed_roles=["engineering", "admin"],
    )
    create_approval_level(
        name="Diretoria ate 5000",
        min_amount="1000.01",
        max_amount="5000.00",
        allowed_roles=["director", "admin"],
    )

    ticket_id = await create_triaged_ticket(client, unit.id, admin, engineering, auth_header_for_user)

    response = await client.post(
        f"/tickets/{ticket_id}/approval-request",
        headers=auth_header_for_user(engineering),
        json=make_approval_request_payload(amount_requested="800.00"),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "waiting_approval"
    assert data["approvals"][0]["approval_level_id"] == level.id
    assert data["approvals"][0]["status"] == "pending"

    approval = db_session.scalar(select(Approval).where(Approval.ticket_id == ticket_id))
    assert approval is not None
    assert approval.approval_level_id == level.id
    assert approval.status == ApprovalStatus.PENDING


@pytest.mark.anyio
async def test_approval_request_without_matching_level_is_blocked(
    client: httpx.AsyncClient,
    create_unit,
    create_user,
    create_approval_level,
    auth_header_for_user,
) -> None:
    unit = create_unit()
    admin = create_user(role=UserRole.ADMIN)
    engineering = create_user(role=UserRole.ENGINEERING, email="eng.no.level@local.test")
    create_approval_level(min_amount="0.00", max_amount="1000.00", allowed_roles=["engineering", "admin"])

    ticket_id = await create_triaged_ticket(client, unit.id, admin, engineering, auth_header_for_user)

    response = await client.post(
        f"/tickets/{ticket_id}/approval-request",
        headers=auth_header_for_user(engineering),
        json=make_approval_request_payload(amount_requested="2500.00"),
    )

    assert response.status_code == 422
    assert response.json() == {"detail": "No active approval level is configured for the requested amount."}


@pytest.mark.anyio
async def test_approval_request_blocks_when_requires_approval_is_false(
    client: httpx.AsyncClient,
    create_unit,
    create_user,
    create_approval_level,
    auth_header_for_user,
) -> None:
    unit = create_unit()
    admin = create_user(role=UserRole.ADMIN)
    engineering = create_user(role=UserRole.ENGINEERING, email="eng.no.req@local.test")
    create_approval_level(min_amount="0.00", max_amount="1000.00", allowed_roles=["engineering", "admin"])

    ticket_id = await create_triaged_ticket(
        client,
        unit.id,
        admin,
        engineering,
        auth_header_for_user,
        requires_approval=False,
    )

    response = await client.post(
        f"/tickets/{ticket_id}/approval-request",
        headers=auth_header_for_user(engineering),
        json=make_approval_request_payload(),
    )

    assert response.status_code == 422
    assert response.json() == {"detail": "Ticket does not require approval."}


@pytest.mark.anyio
async def test_approval_request_blocks_when_ticket_is_not_in_triage(
    client: httpx.AsyncClient,
    create_unit,
    create_user,
    create_approval_level,
    auth_header_for_user,
) -> None:
    unit = create_unit()
    admin = create_user(role=UserRole.ADMIN)
    engineering = create_user(role=UserRole.ENGINEERING, email="eng.not.triage@local.test")
    create_approval_level(min_amount="0.00", max_amount="1000.00", allowed_roles=["engineering", "admin"])

    created = await client.post(
        "/tickets",
        headers=auth_header_for_user(admin),
        json=make_ticket_payload(unit.id),
    )

    response = await client.post(
        f"/tickets/{created.json()['id']}/approval-request",
        headers=auth_header_for_user(engineering),
        json=make_approval_request_payload(),
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "Ticket cannot request approval from the current status."}


@pytest.mark.anyio
async def test_duplicate_pending_approval_is_blocked(
    client: httpx.AsyncClient,
    create_unit,
    create_user,
    create_approval_level,
    auth_header_for_user,
) -> None:
    unit = create_unit()
    admin = create_user(role=UserRole.ADMIN)
    engineering = create_user(role=UserRole.ENGINEERING, email="eng.dup@local.test")
    create_approval_level(min_amount="0.00", max_amount="1000.00", allowed_roles=["engineering", "admin"])

    ticket_id = await create_triaged_ticket(client, unit.id, admin, engineering, auth_header_for_user)

    first = await client.post(
        f"/tickets/{ticket_id}/approval-request",
        headers=auth_header_for_user(engineering),
        json=make_approval_request_payload(),
    )
    assert first.status_code == 200

    second = await client.post(
        f"/tickets/{ticket_id}/approval-request",
        headers=auth_header_for_user(engineering),
        json=make_approval_request_payload(),
    )

    assert second.status_code == 409
    assert second.json() == {"detail": "Ticket already has a pending approval request."}


@pytest.mark.anyio
async def test_approval_request_sets_waiting_approval_and_creates_history(
    client: httpx.AsyncClient,
    db_session,
    create_unit,
    create_user,
    create_approval_level,
    auth_header_for_user,
) -> None:
    unit = create_unit()
    admin = create_user(role=UserRole.ADMIN)
    engineering = create_user(role=UserRole.ENGINEERING, email="eng.history@local.test")
    create_approval_level(min_amount="0.00", max_amount="1000.00", allowed_roles=["engineering", "admin"])

    ticket_id = await create_triaged_ticket(client, unit.id, admin, engineering, auth_header_for_user)

    response = await client.post(
        f"/tickets/{ticket_id}/approval-request",
        headers=auth_header_for_user(engineering),
        json=make_approval_request_payload(),
    )

    assert response.status_code == 200
    ticket = db_session.get(Ticket, ticket_id)
    assert ticket is not None
    assert ticket.status == TicketStatus.WAITING_APPROVAL

    history_entries = list(
        db_session.scalars(
            select(TicketHistory)
            .where(TicketHistory.ticket_id == ticket_id)
            .order_by(TicketHistory.id.asc())
        )
    )
    assert history_entries[-1].old_status == TicketStatus.TRIAGE
    assert history_entries[-1].new_status == TicketStatus.WAITING_APPROVAL


@pytest.mark.anyio
async def test_role_within_level_can_approve_and_sets_cost_and_dates(
    client: httpx.AsyncClient,
    db_session,
    create_unit,
    create_user,
    create_approval_level,
    auth_header_for_user,
) -> None:
    unit = create_unit()
    admin = create_user(role=UserRole.ADMIN)
    engineering = create_user(role=UserRole.ENGINEERING, email="eng.approver@local.test")
    create_approval_level(min_amount="0.00", max_amount="1000.00", allowed_roles=["engineering", "admin"])

    ticket_id = await create_triaged_ticket(client, unit.id, admin, engineering, auth_header_for_user)
    await client.post(
        f"/tickets/{ticket_id}/approval-request",
        headers=auth_header_for_user(engineering),
        json=make_approval_request_payload(amount_requested="700.00"),
    )

    response = await client.patch(
        f"/tickets/{ticket_id}/approval-decision",
        headers=auth_header_for_user(engineering),
        json=make_approval_decision_payload(amount_approved="650.00"),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "approved"
    assert data["approved_cost"] == "650.00"
    assert data["approved_at"] is not None
    assert data["approvals"][0]["status"] == "approved"
    assert data["approvals"][0]["approved_by_user_id"] == engineering.id

    ticket = db_session.get(Ticket, ticket_id)
    assert ticket is not None
    assert ticket.approved_cost == 650
    assert ticket.approved_at is not None


@pytest.mark.anyio
async def test_role_outside_level_cannot_approve(
    client: httpx.AsyncClient,
    create_unit,
    create_user,
    create_approval_level,
    auth_header_for_user,
) -> None:
    unit = create_unit()
    admin = create_user(role=UserRole.ADMIN)
    engineering = create_user(role=UserRole.ENGINEERING, email="eng.outside@local.test")
    director = create_user(role=UserRole.DIRECTOR, email="director.outside@local.test")
    create_approval_level(min_amount="0.00", max_amount="1000.00", allowed_roles=["engineering"])

    ticket_id = await create_triaged_ticket(client, unit.id, admin, engineering, auth_header_for_user)
    await client.post(
        f"/tickets/{ticket_id}/approval-request",
        headers=auth_header_for_user(engineering),
        json=make_approval_request_payload(amount_requested="900.00"),
    )

    response = await client.patch(
        f"/tickets/{ticket_id}/approval-decision",
        headers=auth_header_for_user(director),
        json=make_approval_decision_payload(),
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "Your role is not allowed to approve this amount."}


@pytest.mark.anyio
async def test_director_approves_only_when_level_allows_director(
    client: httpx.AsyncClient,
    create_unit,
    create_user,
    create_approval_level,
    auth_header_for_user,
) -> None:
    unit = create_unit()
    admin = create_user(role=UserRole.ADMIN)
    engineering = create_user(role=UserRole.ENGINEERING, email="eng.requestor@local.test")
    director = create_user(role=UserRole.DIRECTOR, email="director.ok@local.test")
    create_approval_level(min_amount="1000.01", max_amount="5000.00", allowed_roles=["director", "admin"])

    ticket_id = await create_triaged_ticket(client, unit.id, admin, engineering, auth_header_for_user)
    await client.post(
        f"/tickets/{ticket_id}/approval-request",
        headers=auth_header_for_user(engineering),
        json=make_approval_request_payload(amount_requested="1500.00"),
    )

    response = await client.patch(
        f"/tickets/{ticket_id}/approval-decision",
        headers=auth_header_for_user(director),
        json=make_approval_decision_payload(amount_approved="1400.00"),
    )

    assert response.status_code == 200
    assert response.json()["status"] == "approved"


@pytest.mark.anyio
async def test_manager_and_supplier_cannot_approve_even_if_pending_exists(
    client: httpx.AsyncClient,
    create_unit,
    create_user,
    create_approval_level,
    auth_header_for_user,
) -> None:
    unit = create_unit()
    admin = create_user(role=UserRole.ADMIN)
    engineering = create_user(role=UserRole.ENGINEERING, email="eng.pending@local.test")
    manager = create_user(role=UserRole.MANAGER, email="manager.no.approve@local.test", unit_id=unit.id)
    supplier = create_user(role=UserRole.SUPPLIER, email="supplier.no.approve@local.test")
    create_approval_level(min_amount="0.00", max_amount="1000.00", allowed_roles=["engineering", "admin"])

    ticket_id = await create_triaged_ticket(client, unit.id, admin, engineering, auth_header_for_user)
    await client.post(
        f"/tickets/{ticket_id}/approval-request",
        headers=auth_header_for_user(engineering),
        json=make_approval_request_payload(),
    )

    manager_response = await client.patch(
        f"/tickets/{ticket_id}/approval-decision",
        headers=auth_header_for_user(manager),
        json=make_approval_decision_payload(),
    )
    supplier_response = await client.patch(
        f"/tickets/{ticket_id}/approval-decision",
        headers=auth_header_for_user(supplier),
        json=make_approval_decision_payload(),
    )

    assert manager_response.status_code == 403
    assert supplier_response.status_code == 403


@pytest.mark.anyio
async def test_rejection_sets_ticket_status_to_rejected_and_returns_approval_data(
    client: httpx.AsyncClient,
    db_session,
    create_unit,
    create_user,
    create_approval_level,
    auth_header_for_user,
) -> None:
    unit = create_unit()
    admin = create_user(role=UserRole.ADMIN)
    engineering = create_user(role=UserRole.ENGINEERING, email="eng.reject@local.test")
    director = create_user(role=UserRole.DIRECTOR, email="director.reject@local.test")
    level = create_approval_level(
        name="Diretoria ate 5000",
        min_amount="1000.01",
        max_amount="5000.00",
        allowed_roles=["director", "admin"],
    )

    ticket_id = await create_triaged_ticket(client, unit.id, admin, engineering, auth_header_for_user)
    await client.post(
        f"/tickets/{ticket_id}/approval-request",
        headers=auth_header_for_user(engineering),
        json=make_approval_request_payload(amount_requested="2200.00"),
    )

    response = await client.patch(
        f"/tickets/{ticket_id}/approval-decision",
        headers=auth_header_for_user(director),
        json=make_approval_decision_payload(decision="rejected", amount_approved=None, justification="Valor recusado nesta etapa."),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "rejected"
    assert data["approvals"][0]["status"] == "rejected"
    assert data["approvals"][0]["approval_level_id"] == level.id
    assert data["approvals"][0]["approval_level_name"] == level.name
    assert data["approvals"][0]["approval_allowed_roles"] == ["director", "admin"]

    ticket = db_session.get(Ticket, ticket_id)
    assert ticket is not None
    assert ticket.status == TicketStatus.REJECTED


@pytest.mark.anyio
async def test_ticket_detail_returns_approval_data_with_level_context(
    client: httpx.AsyncClient,
    create_unit,
    create_user,
    create_approval_level,
    auth_header_for_user,
) -> None:
    unit = create_unit()
    admin = create_user(role=UserRole.ADMIN)
    engineering = create_user(role=UserRole.ENGINEERING, email="eng.detail@local.test")
    level = create_approval_level(
        name="Engenharia ate 1000",
        min_amount="0.00",
        max_amount="1000.00",
        allowed_roles=["engineering", "admin"],
    )

    ticket_id = await create_triaged_ticket(client, unit.id, admin, engineering, auth_header_for_user)
    await client.post(
        f"/tickets/{ticket_id}/approval-request",
        headers=auth_header_for_user(engineering),
        json=make_approval_request_payload(amount_requested="500.00"),
    )

    detail = await client.get(f"/tickets/{ticket_id}", headers=auth_header_for_user(admin))

    assert detail.status_code == 200
    approval = detail.json()["approvals"][0]
    assert approval["status"] == "pending"
    assert approval["requested_by_user_id"] == engineering.id
    assert approval["approval_level_id"] == level.id
    assert approval["approval_level_name"] == "Engenharia ate 1000"
    assert approval["approval_allowed_roles"] == ["engineering", "admin"]
