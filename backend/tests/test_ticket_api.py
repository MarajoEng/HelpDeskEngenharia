from datetime import UTC, datetime, timedelta
from decimal import Decimal

import httpx
import pytest
from sqlalchemy import select

from app.models.enums import PriorityLevel, TicketCategory, TicketSeverity, TicketStatus, UserRole
from app.models.ticket import Ticket
from app.models.ticket_custom_field import TicketCustomField
from app.models.ticket_history import TicketHistory
from app.models.ticket_status import TicketStatusTransitionConfig
from app.models.ticket_subcategory import TicketSubcategoryConfig
from app.models.ticket_type import TicketTypeConfig
from app.services.ticket_configuration_seed import seed_ticket_configurations


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


def make_custom_field(category_id: int, **overrides: object) -> TicketCustomField:
    payload: dict[str, object] = {
        "category_id": category_id,
        "name": "pressao_linha",
        "label": "Pressao da linha",
        "field_type": "text",
        "is_required": False,
        "is_active": True,
        "display_order": 10,
        "options_json": [],
    }
    payload.update(overrides)
    return TicketCustomField(**payload)


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
async def test_new_ticket_uses_configured_initial_status(
    client: httpx.AsyncClient,
    db_session,
    create_unit,
    create_user,
    auth_header_for_user,
) -> None:
    unit = create_unit()
    admin = create_user(role=UserRole.ADMIN)
    seeded = seed_ticket_configurations(db_session)
    open_status = next(status for status in seeded["statuses"] if status.legacy_value == "open")
    open_status.name = "Recebido"
    db_session.commit()

    response = await client.post(
        "/tickets",
        headers=auth_header_for_user(admin),
        json=make_ticket_payload(unit.id),
    )

    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "open"
    assert data["status_id"] == open_status.id
    assert data["status_name"] == "Recebido"


@pytest.mark.anyio
async def test_legacy_ticket_without_status_id_still_returns_configured_status_fields(
    client: httpx.AsyncClient,
    db_session,
    create_unit,
    create_user,
    auth_header_for_user,
) -> None:
    unit = create_unit()
    admin = create_user(role=UserRole.ADMIN)
    seed_ticket_configurations(db_session)
    ticket = Ticket(
        ticket_number="ENG-LEGACY-000001",
        unit_id=unit.id,
        opened_by_user_id=admin.id,
        category=TicketCategory.FUEL_PUMP,
        problem_type="Falha",
        title="Chamado legado",
        description="Registro antigo sem status_id.",
        priority=PriorityLevel.HIGH,
        severity=TicketSeverity.CRITICAL,
        status=TicketStatus.OPEN,
        requires_approval=False,
        opened_at=datetime.now(UTC),
    )
    db_session.add(ticket)
    db_session.commit()

    response = await client.get(f"/tickets/{ticket.id}", headers=auth_header_for_user(admin))

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "open"
    assert data["status_id"] is None
    assert data["status_name"] == "Aberto"


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
async def test_ticket_list_filters_by_configured_status_and_returns_status_metadata(
    client: httpx.AsyncClient,
    db_session,
    create_unit,
    create_user,
    auth_header_for_user,
) -> None:
    unit = create_unit()
    admin = create_user(role=UserRole.ADMIN)
    seeded = seed_ticket_configurations(db_session)
    open_status = next(status for status in seeded["statuses"] if status.legacy_value == "open")
    db_session.commit()
    await client.post("/tickets", headers=auth_header_for_user(admin), json=make_ticket_payload(unit.id))

    response = await client.get(
        f"/tickets?status_id={open_status.id}",
        headers=auth_header_for_user(admin),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["status_id"] == open_status.id
    assert data["items"][0]["status_name"] == open_status.name
    assert data["items"][0]["status_color"] == open_status.color


@pytest.mark.anyio
async def test_configured_status_transition_validates_comment_role_and_history(
    client: httpx.AsyncClient,
    db_session,
    create_unit,
    create_user,
    auth_header_for_user,
) -> None:
    unit = create_unit()
    admin = create_user(role=UserRole.ADMIN)
    manager = create_user(name="Manager", email="workflow-manager@local.test", role=UserRole.MANAGER, unit_id=unit.id)
    seeded = seed_ticket_configurations(db_session)
    open_status = next(status for status in seeded["statuses"] if status.legacy_value == "open")
    triage_status = next(status for status in seeded["statuses"] if status.legacy_value == "triage")
    transition = db_session.scalar(
        select(TicketStatusTransitionConfig).where(
            TicketStatusTransitionConfig.from_status_id == open_status.id,
            TicketStatusTransitionConfig.to_status_id == triage_status.id,
        )
    )
    assert transition is not None
    transition.requires_comment = True
    transition.allowed_roles_json = ["engineering"]
    db_session.commit()

    create_response = await client.post(
        "/tickets",
        headers=auth_header_for_user(admin),
        json=make_ticket_payload(unit.id, requires_approval=False),
    )
    ticket_id = create_response.json()["id"]

    available_response = await client.get(
        f"/tickets/{ticket_id}/available-transitions",
        headers=auth_header_for_user(admin),
    )
    assert available_response.status_code == 200
    assert available_response.json()["transitions"] == []

    forbidden_response = await client.patch(
        f"/tickets/{ticket_id}/transition",
        headers=auth_header_for_user(admin),
        json={"to_status_id": triage_status.id, "comment": "Triagem"},
    )
    assert forbidden_response.status_code == 403

    transition.allowed_roles_json = ["admin"]
    db_session.commit()
    missing_comment_response = await client.patch(
        f"/tickets/{ticket_id}/transition",
        headers=auth_header_for_user(admin),
        json={"to_status_id": triage_status.id},
    )
    assert missing_comment_response.status_code == 422

    valid_response = await client.patch(
        f"/tickets/{ticket_id}/transition",
        headers=auth_header_for_user(admin),
        json={"to_status_id": triage_status.id, "comment": "Triagem validada"},
    )
    assert valid_response.status_code == 200
    assert valid_response.json()["status"] == "triage"
    assert valid_response.json()["status_id"] == triage_status.id

    history = db_session.scalars(
        select(TicketHistory).where(TicketHistory.ticket_id == ticket_id).order_by(TicketHistory.id.asc())
    ).all()
    assert history[-1].old_status == TicketStatus.OPEN
    assert history[-1].new_status == TicketStatus.TRIAGE
    assert history[-1].comment == "Triagem validada"

    invalid_response = await client.patch(
        f"/tickets/{ticket_id}/transition",
        headers=auth_header_for_user(manager),
        json={"to_status_id": open_status.id, "comment": "Voltar"},
    )
    assert invalid_response.status_code in {403, 409}


@pytest.mark.anyio
async def test_ticket_creation_accepts_configured_ids_and_returns_configured_names(
    client: httpx.AsyncClient,
    db_session,
    create_unit,
    create_user,
    auth_header_for_user,
) -> None:
    seeded = seed_ticket_configurations(db_session)
    db_session.commit()

    unit = create_unit()
    admin = create_user(role=UserRole.ADMIN)
    category = next(item for item in seeded["categories"] if item.legacy_value == "fuel_pump")
    priority = next(item for item in seeded["priorities"] if item.legacy_value == "high")
    subcategory = db_session.scalar(
        select(TicketSubcategoryConfig).where(TicketSubcategoryConfig.category_id == category.id)
    )
    ticket_type_id = category.category_types[0].type_id if category.category_types else None
    ticket_type = db_session.get(TicketTypeConfig, ticket_type_id) if ticket_type_id is not None else None
    assert subcategory is not None
    assert ticket_type is not None

    response = await client.post(
        "/tickets",
        headers=auth_header_for_user(admin),
        json=make_ticket_payload(
            unit.id,
            category=None,
            priority=None,
            category_id=category.id,
            subcategory_id=subcategory.id,
            type_id=ticket_type.id,
            priority_id=priority.id,
        ),
    )

    assert response.status_code == 201
    data = response.json()
    assert data["category_id"] == category.id
    assert data["subcategory_id"] == subcategory.id
    assert data["type_id"] == ticket_type.id
    assert data["priority_id"] == priority.id
    assert data["category"] == category.legacy_value
    assert data["priority"] == priority.legacy_value
    assert data["category_name"] == category.name
    assert data["subcategory_name"] == subcategory.name
    assert data["type_name"] == ticket_type.name
    assert data["priority_name"] == priority.name
    assert data["priority_color"] == priority.color
    assert data["priority_weight"] == priority.weight

    detail_response = await client.get(
        f"/tickets/{data['id']}",
        headers=auth_header_for_user(admin),
    )

    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert detail["category_name"] == category.name
    assert detail["priority_name"] == priority.name
    assert detail["priority_color"] == priority.color
    assert detail["priority_weight"] == priority.weight


@pytest.mark.anyio
async def test_ticket_creation_blocks_inactive_category_and_priority_configs(
    client: httpx.AsyncClient,
    db_session,
    create_unit,
    create_user,
    auth_header_for_user,
) -> None:
    seeded = seed_ticket_configurations(db_session)
    unit = create_unit()
    admin = create_user(role=UserRole.ADMIN)
    category = next(item for item in seeded["categories"] if item.legacy_value == "fuel_pump")
    priority = next(item for item in seeded["priorities"] if item.legacy_value == "high")
    category.is_active = False
    db_session.commit()

    inactive_category_response = await client.post(
        "/tickets",
        headers=auth_header_for_user(admin),
        json=make_ticket_payload(
            unit.id,
            category=None,
            priority=None,
            category_id=category.id,
            priority_id=priority.id,
        ),
    )

    assert inactive_category_response.status_code == 422
    assert inactive_category_response.json() == {
        "detail": "Ticket category configuration must be active."
    }

    category.is_active = True
    priority.is_active = False
    db_session.commit()

    inactive_priority_response = await client.post(
        "/tickets",
        headers=auth_header_for_user(admin),
        json=make_ticket_payload(
            unit.id,
            category=None,
            priority=None,
            category_id=category.id,
            priority_id=priority.id,
        ),
    )

    assert inactive_priority_response.status_code == 422
    assert inactive_priority_response.json() == {
        "detail": "Ticket priority configuration must be active."
    }


@pytest.mark.anyio
async def test_ticket_creation_blocks_subcategory_from_another_category(
    client: httpx.AsyncClient,
    db_session,
    create_unit,
    create_user,
    auth_header_for_user,
) -> None:
    seeded = seed_ticket_configurations(db_session)
    db_session.commit()

    unit = create_unit()
    admin = create_user(role=UserRole.ADMIN)
    first_category = seeded["categories"][0]
    second_category = seeded["categories"][1]
    priority = seeded["priorities"][0]
    foreign_subcategory = db_session.scalar(
        select(TicketSubcategoryConfig).where(TicketSubcategoryConfig.category_id == second_category.id)
    )
    assert foreign_subcategory is not None

    response = await client.post(
        "/tickets",
        headers=auth_header_for_user(admin),
        json=make_ticket_payload(
            unit.id,
            category=None,
            priority=None,
            category_id=first_category.id,
            subcategory_id=foreign_subcategory.id,
            priority_id=priority.id,
        ),
    )

    assert response.status_code == 422
    assert response.json() == {
        "detail": "Ticket subcategory does not belong to the selected category."
    }


@pytest.mark.anyio
async def test_ticket_creation_with_legacy_payload_still_works_after_config_support(
    client: httpx.AsyncClient,
    db_session,
    create_unit,
    create_user,
    auth_header_for_user,
) -> None:
    seed_ticket_configurations(db_session)
    db_session.commit()

    unit = create_unit()
    admin = create_user(role=UserRole.ADMIN)

    response = await client.post(
        "/tickets",
        headers=auth_header_for_user(admin),
        json=make_ticket_payload(unit.id, category="electrical", priority="medium"),
    )

    assert response.status_code == 201
    data = response.json()
    assert data["category"] == "electrical"
    assert data["priority"] == "medium"
    assert data["category_id"] is None
    assert data["priority_id"] is None
    assert data["category_name"] == "Electrical"
    assert data["priority_name"] == "Media"

    detail_response = await client.get(f"/tickets/{data['id']}", headers=auth_header_for_user(admin))
    assert detail_response.status_code == 200
    assert detail_response.json()["custom_fields"] == []


@pytest.mark.anyio
async def test_ticket_creation_persists_custom_field_values_and_returns_detail(
    client: httpx.AsyncClient,
    db_session,
    create_unit,
    create_user,
    auth_header_for_user,
) -> None:
    seeded = seed_ticket_configurations(db_session)
    category = next(item for item in seeded["categories"] if item.legacy_value == "fuel_pump")
    priority = next(item for item in seeded["priorities"] if item.legacy_value == "high")
    text_field = make_custom_field(category.id, is_required=True)
    boolean_field = make_custom_field(
        category.id,
        name="houve_vazamento",
        label="Houve vazamento",
        field_type="boolean",
        is_required=True,
        display_order=20,
    )
    date_field = make_custom_field(
        category.id,
        name="data_falha",
        label="Data da falha",
        field_type="date",
        display_order=30,
    )
    db_session.add_all([text_field, boolean_field, date_field])
    db_session.commit()

    unit = create_unit()
    admin = create_user(role=UserRole.ADMIN)

    create_response = await client.post(
        "/tickets",
        headers=auth_header_for_user(admin),
        json=make_ticket_payload(
            unit.id,
            category=None,
            priority=None,
            category_id=category.id,
            priority_id=priority.id,
            custom_fields=[
                {"field_id": text_field.id, "value": "Baixa pressao"},
                {"field_id": boolean_field.id, "value": False},
                {"field_id": date_field.id, "value": "2026-06-25"},
            ],
        ),
    )

    assert create_response.status_code == 201
    detail_response = await client.get(
        f"/tickets/{create_response.json()['id']}",
        headers=auth_header_for_user(admin),
    )
    assert detail_response.status_code == 200
    custom_fields = {field["name"]: field for field in detail_response.json()["custom_fields"]}
    assert custom_fields["pressao_linha"]["value"] == "Baixa pressao"
    assert custom_fields["houve_vazamento"]["value"] is False
    assert custom_fields["houve_vazamento"]["display_value"] == "Nao"
    assert custom_fields["data_falha"]["value"] == "2026-06-25"


@pytest.mark.anyio
async def test_required_custom_field_blocks_ticket_without_value(
    client: httpx.AsyncClient,
    db_session,
    create_unit,
    create_user,
    auth_header_for_user,
) -> None:
    seeded = seed_ticket_configurations(db_session)
    category = seeded["categories"][0]
    priority = seeded["priorities"][0]
    required_field = make_custom_field(category.id, is_required=True)
    db_session.add(required_field)
    db_session.commit()
    unit = create_unit()
    admin = create_user(role=UserRole.ADMIN)

    response = await client.post(
        "/tickets",
        headers=auth_header_for_user(admin),
        json=make_ticket_payload(
            unit.id,
            category=None,
            priority=None,
            category_id=category.id,
            priority_id=priority.id,
            custom_fields=[],
        ),
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "Custom field 'Pressao da linha' is required."


@pytest.mark.anyio
async def test_ticket_creation_rejects_custom_field_from_other_category(
    client: httpx.AsyncClient,
    db_session,
    create_unit,
    create_user,
    auth_header_for_user,
) -> None:
    seeded = seed_ticket_configurations(db_session)
    first_category = seeded["categories"][0]
    second_category = seeded["categories"][1]
    priority = seeded["priorities"][0]
    foreign_field = make_custom_field(second_category.id)
    db_session.add(foreign_field)
    db_session.commit()
    unit = create_unit()
    admin = create_user(role=UserRole.ADMIN)

    response = await client.post(
        "/tickets",
        headers=auth_header_for_user(admin),
        json=make_ticket_payload(
            unit.id,
            category=None,
            priority=None,
            category_id=first_category.id,
            priority_id=priority.id,
            custom_fields=[{"field_id": foreign_field.id, "value": "valor"}],
        ),
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "Custom field does not belong to the selected category or subcategory."


@pytest.mark.anyio
async def test_ticket_creation_rejects_invalid_select_and_number_values(
    client: httpx.AsyncClient,
    db_session,
    create_unit,
    create_user,
    auth_header_for_user,
) -> None:
    seeded = seed_ticket_configurations(db_session)
    category = seeded["categories"][0]
    priority = seeded["priorities"][0]
    select_field = make_custom_field(
        category.id,
        name="turno",
        label="Turno",
        field_type="select",
        options_json=[
            {"label": "Manha", "value": "manha", "display_order": 1, "is_active": True},
            {"label": "Noite", "value": "noite", "display_order": 2, "is_active": True},
        ],
    )
    number_field = make_custom_field(
        category.id,
        name="volume_estimado",
        label="Volume estimado",
        field_type="number",
        display_order=20,
    )
    db_session.add_all([select_field, number_field])
    db_session.commit()
    unit = create_unit()
    admin = create_user(role=UserRole.ADMIN)

    invalid_select = await client.post(
        "/tickets",
        headers=auth_header_for_user(admin),
        json=make_ticket_payload(
            unit.id,
            category=None,
            priority=None,
            category_id=category.id,
            priority_id=priority.id,
            custom_fields=[{"field_id": select_field.id, "value": "tarde"}],
        ),
    )
    invalid_number = await client.post(
        "/tickets",
        headers=auth_header_for_user(admin),
        json=make_ticket_payload(
            unit.id,
            category=None,
            priority=None,
            category_id=category.id,
            priority_id=priority.id,
            title="Numero invalido",
            custom_fields=[{"field_id": number_field.id, "value": "abc"}],
        ),
    )

    assert invalid_select.status_code == 422
    assert invalid_select.json()["detail"] == "Custom field 'Turno' has an invalid option."
    assert invalid_number.status_code == 422
    assert invalid_number.json()["detail"] == "Custom field 'Volume estimado' must be a valid number."


@pytest.mark.anyio
async def test_ticket_filters_support_configured_ids_and_legacy_values(
    client: httpx.AsyncClient,
    db_session,
    create_unit,
    create_user,
    auth_header_for_user,
) -> None:
    seeded = seed_ticket_configurations(db_session)
    db_session.commit()

    unit = create_unit()
    admin = create_user(role=UserRole.ADMIN)
    category = next(item for item in seeded["categories"] if item.legacy_value == "fuel_pump")
    priority = next(item for item in seeded["priorities"] if item.legacy_value == "high")

    configured_response = await client.post(
        "/tickets",
        headers=auth_header_for_user(admin),
        json=make_ticket_payload(
            unit.id,
            title="Configurado",
            category=None,
            priority=None,
            category_id=category.id,
            priority_id=priority.id,
        ),
    )
    legacy_response = await client.post(
        "/tickets",
        headers=auth_header_for_user(admin),
        json=make_ticket_payload(
            unit.id,
            title="Legado",
            category="fuel_pump",
            priority="high",
        ),
    )

    assert configured_response.status_code == 201
    assert legacy_response.status_code == 201

    response = await client.get(
        f"/tickets?category_id={category.id}&priority_id={priority.id}",
        headers=auth_header_for_user(admin),
    )

    assert response.status_code == 200
    data = response.json()
    titles = {item["title"] for item in data["items"]}
    assert data["total"] == 2
    assert {"Configurado", "Legado"} <= titles
    configured_item = next(item for item in data["items"] if item["title"] == "Configurado")
    legacy_item = next(item for item in data["items"] if item["title"] == "Legado")
    assert configured_item["category_name"] == category.name
    assert configured_item["priority_name"] == priority.name
    assert legacy_item["category_name"] == "Fuel Pump"
    assert legacy_item["priority_name"] == "Alta"


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


@pytest.mark.anyio
async def test_tickets_filter_by_group_code(
    client: httpx.AsyncClient,
    db_session,
    create_user,
    auth_header_for_user,
) -> None:
    from app.models.unit import Unit

    seed_ticket_configurations(db_session)
    admin = create_user(role=UserRole.ADMIN)

    unit_a = Unit(code="02-4301", group_code="02", branch_code="4301", name="Filial A", city="SP", state="SP", region="Sul", is_active=True)
    unit_b = Unit(code="09-0901", group_code="09", branch_code="0901", name="Filial B", city="AM", state="AM", region="Norte", is_active=True)
    db_session.add_all([unit_a, unit_b])
    db_session.commit()

    r1 = await client.post("/tickets", headers=auth_header_for_user(admin), json=make_ticket_payload(unit_a.id))
    r2 = await client.post("/tickets", headers=auth_header_for_user(admin), json=make_ticket_payload(unit_b.id))
    assert r1.status_code == 201
    assert r2.status_code == 201

    response = await client.get("/tickets?group_code=02", headers=auth_header_for_user(admin))
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["unit_id"] == unit_a.id


@pytest.mark.anyio
async def test_tickets_filter_by_branch_code(
    client: httpx.AsyncClient,
    db_session,
    create_user,
    auth_header_for_user,
) -> None:
    from app.models.unit import Unit

    seed_ticket_configurations(db_session)
    admin = create_user(role=UserRole.ADMIN)

    unit_a = Unit(code="02-4301", group_code="02", branch_code="4301", name="Filial A", city="SP", state="SP", region="Sul", is_active=True)
    unit_b = Unit(code="02-4302", group_code="02", branch_code="4302", name="Filial B", city="SP", state="SP", region="Sul", is_active=True)
    db_session.add_all([unit_a, unit_b])
    db_session.commit()

    r1 = await client.post("/tickets", headers=auth_header_for_user(admin), json=make_ticket_payload(unit_a.id))
    r2 = await client.post("/tickets", headers=auth_header_for_user(admin), json=make_ticket_payload(unit_b.id))
    assert r1.status_code == 201
    assert r2.status_code == 201

    response = await client.get("/tickets?branch_code=4301", headers=auth_header_for_user(admin))
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["unit_id"] == unit_a.id


@pytest.mark.anyio
async def test_ticket_creation_with_unit_id_continues_working(
    client: httpx.AsyncClient,
    db_session,
    create_user,
    auth_header_for_user,
) -> None:
    from app.models.unit import Unit

    seed_ticket_configurations(db_session)
    admin = create_user(role=UserRole.ADMIN)
    unit = Unit(code="02-4301", group_code="02", branch_code="4301", name="Filial A", city="SP", state="SP", region="Sul", is_active=True)
    db_session.add(unit)
    db_session.commit()

    response = await client.post("/tickets", headers=auth_header_for_user(admin), json=make_ticket_payload(unit.id))
    assert response.status_code == 201
    data = response.json()
    assert data["unit_id"] == unit.id
