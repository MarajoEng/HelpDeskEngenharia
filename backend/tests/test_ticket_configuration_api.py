import httpx
import pytest
from sqlalchemy import select

from app.models.enums import UserRole
from app.models.ticket import Ticket
from app.models.ticket_custom_field import TicketCustomField
from app.models.ticket_priority import TicketPriorityConfig
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


@pytest.mark.anyio
async def test_public_ticket_categories_hide_inactive_records(
    client: httpx.AsyncClient,
    db_session,
) -> None:
    seeded = seed_ticket_configurations(db_session)
    inactive_category = seeded["categories"][0]
    inactive_category.is_active = False
    db_session.commit()

    response = await client.get("/ticket-categories")

    assert response.status_code == 200
    data = response.json()
    names = [item["name"] for item in data["items"]]
    assert inactive_category.name not in names
    assert all(item["is_active"] is True for item in data["items"])


@pytest.mark.anyio
async def test_public_subcategories_are_scoped_to_the_requested_category(
    client: httpx.AsyncClient,
    db_session,
) -> None:
    seeded = seed_ticket_configurations(db_session)
    category = seeded["categories"][0]
    db_session.commit()

    response = await client.get(f"/ticket-categories/{category.id}/subcategories")

    assert response.status_code == 200
    items = response.json()["items"]
    assert items
    assert all(item["category_id"] == category.id for item in items)
    assert all(item["category_name"] == category.name for item in items)


@pytest.mark.anyio
async def test_public_ticket_types_and_priorities_hide_inactive_records(
    client: httpx.AsyncClient,
    db_session,
) -> None:
    seed_ticket_configurations(db_session)
    inactive_type = db_session.scalar(select(TicketTypeConfig).where(TicketTypeConfig.name == "Orcamento"))
    inactive_priority = db_session.scalar(select(TicketPriorityConfig).where(TicketPriorityConfig.name == "Baixa"))
    assert inactive_type is not None
    assert inactive_priority is not None

    inactive_type.is_active = False
    inactive_priority.is_active = False
    db_session.commit()

    types_response = await client.get("/ticket-types")
    priorities_response = await client.get("/ticket-priorities")

    assert types_response.status_code == 200
    assert priorities_response.status_code == 200
    assert all(item["is_active"] is True for item in types_response.json()["items"])
    assert all(item["is_active"] is True for item in priorities_response.json()["items"])
    assert inactive_type.name not in [item["name"] for item in types_response.json()["items"]]
    assert inactive_priority.name not in [item["name"] for item in priorities_response.json()["items"]]


@pytest.mark.anyio
async def test_admin_ticket_categories_list_can_filter_inactive_records(
    client: httpx.AsyncClient,
    db_session,
    create_user,
    auth_header_for_user,
) -> None:
    seeded = seed_ticket_configurations(db_session)
    inactive_category = seeded["categories"][0]
    inactive_category.is_active = False
    db_session.commit()
    admin = create_user(email="config-admin@local.test", role=UserRole.ADMIN)

    response = await client.get(
        "/admin/ticket-categories?is_active=false",
        headers=auth_header_for_user(admin),
    )

    assert response.status_code == 200
    items = response.json()["items"]
    assert items
    assert all(item["is_active"] is False for item in items)
    assert inactive_category.name in [item["name"] for item in items]


@pytest.mark.anyio
async def test_admin_crud_requires_admin_permissions(
    client: httpx.AsyncClient,
    db_session,
    create_user,
    auth_header_for_user,
) -> None:
    seeded = seed_ticket_configurations(db_session)
    db_session.commit()
    manager = create_user(email="manager-config@local.test", role=UserRole.MANAGER)

    get_response = await client.get(
        "/admin/ticket-categories",
        headers=auth_header_for_user(manager),
    )
    post_response = await client.post(
        "/admin/ticket-categories",
        headers=auth_header_for_user(manager),
        json={
            "name": "Nova categoria bloqueada",
            "description": "Nao deve ser criada por manager.",
            "is_active": True,
            "display_order": 999,
            "requires_attachment": False,
            "requires_location": False,
            "type_ids": [seeded["types"][0].id],
        },
    )

    assert get_response.status_code == 403
    assert post_response.status_code == 403


@pytest.mark.anyio
async def test_admin_can_create_and_update_ticket_configuration_records(
    client: httpx.AsyncClient,
    db_session,
    create_user,
    auth_header_for_user,
) -> None:
    seeded = seed_ticket_configurations(db_session)
    db_session.commit()
    admin = create_user(email="ticket-config-admin@local.test", role=UserRole.ADMIN)
    category = seeded["categories"][0]

    create_subcategory_response = await client.post(
        "/admin/ticket-subcategories",
        headers=auth_header_for_user(admin),
        json={
            "category_id": category.id,
            "name": "Teste operacional",
            "description": "Subcategoria criada para validar o CRUD.",
            "is_active": True,
            "display_order": 999,
        },
    )
    assert create_subcategory_response.status_code == 201
    subcategory_data = create_subcategory_response.json()
    assert subcategory_data["category_id"] == category.id
    assert subcategory_data["category_name"] == category.name

    create_category_response = await client.post(
        "/admin/ticket-categories",
        headers=auth_header_for_user(admin),
        json={
            "name": "Infra complementar",
            "description": "Categoria criada via CRUD administrativo.",
            "is_active": True,
            "display_order": 220,
            "requires_attachment": True,
            "requires_location": False,
            "type_ids": [seeded["types"][0].id, seeded["types"][1].id],
        },
    )
    assert create_category_response.status_code == 201
    created_category = create_category_response.json()
    assert created_category["type_ids"] == sorted([seeded["types"][0].id, seeded["types"][1].id])

    patch_priority_response = await client.patch(
        f"/admin/ticket-priorities/{seeded['priorities'][0].id}",
        headers=auth_header_for_user(admin),
        json={
            "is_active": False,
            "weight": 99,
            "sla_hours": 12,
        },
    )
    assert patch_priority_response.status_code == 200
    patched_priority = patch_priority_response.json()
    assert patched_priority["is_active"] is False
    assert patched_priority["weight"] == 99
    assert patched_priority["sla_hours"] == 12


@pytest.mark.anyio
async def test_admin_can_create_custom_text_and_select_fields(
    client: httpx.AsyncClient,
    db_session,
    create_user,
    auth_header_for_user,
) -> None:
    seeded = seed_ticket_configurations(db_session)
    db_session.commit()
    admin = create_user(email="custom-fields-admin@local.test", role=UserRole.ADMIN)
    category = seeded["categories"][0]
    subcategory = seeded["subcategories"][0]

    text_response = await client.post(
        "/admin/ticket-custom-fields",
        headers=auth_header_for_user(admin),
        json={
            "category_id": category.id,
            "name": "pressao_linha",
            "label": "Pressao da linha",
            "description": "Valor informado pela unidade.",
            "field_type": "text",
            "is_required": True,
            "is_active": True,
            "display_order": 10,
            "placeholder": "Ex.: baixa",
            "help_text": "Informe a leitura atual.",
            "options": [],
        },
    )
    assert text_response.status_code == 201
    assert text_response.json()["category_name"] == category.name

    select_response = await client.post(
        "/admin/ticket-custom-fields",
        headers=auth_header_for_user(admin),
        json={
            "category_id": category.id,
            "subcategory_id": subcategory.id,
            "name": "turno",
            "label": "Turno da ocorrencia",
            "description": None,
            "field_type": "select",
            "is_required": False,
            "is_active": True,
            "display_order": 20,
            "placeholder": None,
            "help_text": None,
            "options": [
                {"label": "Manha", "value": "manha", "display_order": 1, "is_active": True},
                {"label": "Noite", "value": "noite", "display_order": 2, "is_active": True},
            ],
        },
    )
    assert select_response.status_code == 201
    assert select_response.json()["subcategory_name"] == subcategory.name
    assert [option["value"] for option in select_response.json()["options"]] == ["manha", "noite"]

    schema_response = await client.get(
        f"/tickets/form-schema?category_id={category.id}&subcategory_id={subcategory.id}",
    )
    assert schema_response.status_code == 200
    schema_fields = schema_response.json()["fields"]
    assert [field["name"] for field in schema_fields] == ["pressao_linha", "turno"]


@pytest.mark.anyio
async def test_inactive_custom_field_is_not_returned_in_form_schema(
    client: httpx.AsyncClient,
    db_session,
) -> None:
    seeded = seed_ticket_configurations(db_session)
    category = seeded["categories"][0]
    active_field = TicketCustomField(
        category_id=category.id,
        name="active_field",
        label="Campo ativo",
        field_type="text",
        is_required=False,
        is_active=True,
        display_order=10,
        options_json=[],
    )
    inactive_field = TicketCustomField(
        category_id=category.id,
        name="inactive_field",
        label="Campo inativo",
        field_type="text",
        is_required=False,
        is_active=False,
        display_order=20,
        options_json=[],
    )
    db_session.add_all([active_field, inactive_field])
    db_session.commit()

    response = await client.get(f"/tickets/form-schema?category_id={category.id}")

    assert response.status_code == 200
    names = [field["name"] for field in response.json()["fields"]]
    assert names == ["active_field"]


@pytest.mark.anyio
async def test_existing_ticket_flow_still_works_after_ticket_configuration_seed(
    client: httpx.AsyncClient,
    db_session,
    create_unit,
    create_user,
    auth_header_for_user,
) -> None:
    seed_ticket_configurations(db_session)
    db_session.commit()
    unit = create_unit()
    admin = create_user(email="tickets-admin@local.test", role=UserRole.ADMIN)

    response = await client.post(
        "/tickets",
        headers=auth_header_for_user(admin),
        json=make_ticket_payload(unit.id, estimated_cost="5000.00"),
    )

    assert response.status_code == 201
    created_ticket = db_session.get(Ticket, response.json()["id"])
    assert created_ticket is not None
    assert created_ticket.ticket_number.startswith("ENG-")
