"""FASE 9 — testes da API de fornecedores."""
from __future__ import annotations

import httpx
import pytest

from app.models.enums import UserRole
from app.models.supplier import Supplier


def make_supplier_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "name": "Fornecedor Teste",
        "document": "12.345.678/0001-99",
        "phone": "(11) 99999-0001",
        "email": "contato@fornecedor.com",
        "specialty": "Manutencao eletrica",
        "is_active": True,
    }
    payload.update(overrides)
    return payload


def create_supplier_in_db(db_session, **overrides: object) -> Supplier:
    data = {
        "name": "Fornecedor DB",
        "document": "98.765.432/0001-11",
        "phone": "(21) 88888-0002",
        "email": "db@fornecedor.com",
        "specialty": "Bombas hidraulicas",
        "is_active": True,
    }
    data.update(overrides)
    supplier = Supplier(**data)
    db_session.add(supplier)
    db_session.commit()
    db_session.refresh(supplier)
    return supplier


# ---------------------------------------------------------------------------
# POST /suppliers — criacao
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_admin_can_create_supplier(
    client: httpx.AsyncClient,
    create_user,
    auth_header_for_user,
) -> None:
    admin = create_user(role=UserRole.ADMIN)
    response = await client.post("/suppliers", headers=auth_header_for_user(admin), json=make_supplier_payload())
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Fornecedor Teste"
    assert data["document"] == "12.345.678/0001-99"
    assert data["is_active"] is True
    assert "id" in data
    assert "created_at" in data


@pytest.mark.anyio
async def test_engineering_cannot_create_supplier(
    client: httpx.AsyncClient,
    create_user,
    auth_header_for_user,
) -> None:
    eng = create_user(role=UserRole.ENGINEERING, email="eng@local.test")
    response = await client.post("/suppliers", headers=auth_header_for_user(eng), json=make_supplier_payload())
    assert response.status_code == 403


@pytest.mark.anyio
async def test_director_cannot_create_supplier(
    client: httpx.AsyncClient,
    create_user,
    auth_header_for_user,
) -> None:
    director = create_user(role=UserRole.DIRECTOR, email="dir@local.test")
    response = await client.post("/suppliers", headers=auth_header_for_user(director), json=make_supplier_payload())
    assert response.status_code == 403


@pytest.mark.anyio
async def test_create_supplier_strips_whitespace(
    client: httpx.AsyncClient,
    create_user,
    auth_header_for_user,
) -> None:
    admin = create_user(role=UserRole.ADMIN)
    payload = make_supplier_payload(name="  Teste  ", specialty="  Eletrica  ")
    response = await client.post("/suppliers", headers=auth_header_for_user(admin), json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Teste"
    assert data["specialty"] == "Eletrica"


@pytest.mark.anyio
async def test_create_supplier_empty_name_rejected(
    client: httpx.AsyncClient,
    create_user,
    auth_header_for_user,
) -> None:
    admin = create_user(role=UserRole.ADMIN)
    payload = make_supplier_payload(name="   ")
    response = await client.post("/suppliers", headers=auth_header_for_user(admin), json=payload)
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# GET /suppliers — listagem
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_admin_can_list_suppliers(
    client: httpx.AsyncClient,
    db_session,
    create_user,
    auth_header_for_user,
) -> None:
    admin = create_user(role=UserRole.ADMIN)
    create_supplier_in_db(db_session, name="Alpha")
    create_supplier_in_db(db_session, name="Beta", document="11.111.111/0001-11", email="beta@test.com")
    response = await client.get("/suppliers", headers=auth_header_for_user(admin))
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2


@pytest.mark.anyio
async def test_engineering_can_list_suppliers(
    client: httpx.AsyncClient,
    db_session,
    create_user,
    auth_header_for_user,
) -> None:
    eng = create_user(role=UserRole.ENGINEERING, email="eng2@local.test")
    create_supplier_in_db(db_session)
    response = await client.get("/suppliers", headers=auth_header_for_user(eng))
    assert response.status_code == 200


@pytest.mark.anyio
async def test_director_can_list_suppliers(
    client: httpx.AsyncClient,
    db_session,
    create_user,
    auth_header_for_user,
) -> None:
    director = create_user(role=UserRole.DIRECTOR, email="dir2@local.test")
    create_supplier_in_db(db_session)
    response = await client.get("/suppliers", headers=auth_header_for_user(director))
    assert response.status_code == 200


@pytest.mark.anyio
async def test_manager_cannot_list_suppliers(
    client: httpx.AsyncClient,
    create_unit,
    create_user,
    auth_header_for_user,
) -> None:
    unit = create_unit()
    manager = create_user(role=UserRole.MANAGER, email="mgr@local.test", unit_id=unit.id)
    response = await client.get("/suppliers", headers=auth_header_for_user(manager))
    assert response.status_code == 403


@pytest.mark.anyio
async def test_supplier_list_is_paginated(
    client: httpx.AsyncClient,
    db_session,
    create_user,
    auth_header_for_user,
) -> None:
    admin = create_user(role=UserRole.ADMIN)
    for i in range(5):
        create_supplier_in_db(
            db_session,
            name=f"Fornecedor {i:02d}",
            document=f"00.000.00{i}/0001-00",
            email=f"f{i}@test.com",
        )
    response = await client.get("/suppliers?page=1&page_size=2", headers=auth_header_for_user(admin))
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 5
    assert len(data["items"]) == 2
    assert data["pages"] == 3


@pytest.mark.anyio
async def test_supplier_list_filter_is_active(
    client: httpx.AsyncClient,
    db_session,
    create_user,
    auth_header_for_user,
) -> None:
    admin = create_user(role=UserRole.ADMIN)
    create_supplier_in_db(db_session, name="Ativo", is_active=True)
    create_supplier_in_db(db_session, name="Inativo", is_active=False, document="99.999.999/0001-99", email="inativo@test.com")
    response = await client.get("/suppliers?is_active=true", headers=auth_header_for_user(admin))
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["name"] == "Ativo"


@pytest.mark.anyio
async def test_supplier_list_search_by_name(
    client: httpx.AsyncClient,
    db_session,
    create_user,
    auth_header_for_user,
) -> None:
    admin = create_user(role=UserRole.ADMIN)
    create_supplier_in_db(db_session, name="Hidraulica Brasil")
    create_supplier_in_db(db_session, name="Eletrica Sul", document="22.222.222/0001-22", email="eletrica@test.com", specialty="Eletrica Industrial")
    response = await client.get("/suppliers?search=Hidraulica", headers=auth_header_for_user(admin))
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["name"] == "Hidraulica Brasil"


# ---------------------------------------------------------------------------
# PATCH /suppliers/{id} — atualizacao
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_admin_can_update_supplier(
    client: httpx.AsyncClient,
    db_session,
    create_user,
    auth_header_for_user,
) -> None:
    admin = create_user(role=UserRole.ADMIN)
    supplier = create_supplier_in_db(db_session)
    response = await client.patch(
        f"/suppliers/{supplier.id}",
        headers=auth_header_for_user(admin),
        json={"name": "Novo Nome", "is_active": False},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Novo Nome"
    assert data["is_active"] is False


@pytest.mark.anyio
async def test_engineering_cannot_update_supplier(
    client: httpx.AsyncClient,
    db_session,
    create_user,
    auth_header_for_user,
) -> None:
    eng = create_user(role=UserRole.ENGINEERING, email="eng3@local.test")
    supplier = create_supplier_in_db(db_session)
    response = await client.patch(
        f"/suppliers/{supplier.id}",
        headers=auth_header_for_user(eng),
        json={"name": "Tentativa"},
    )
    assert response.status_code == 403


@pytest.mark.anyio
async def test_update_supplier_not_found(
    client: httpx.AsyncClient,
    create_user,
    auth_header_for_user,
) -> None:
    admin = create_user(role=UserRole.ADMIN)
    response = await client.patch(
        "/suppliers/9999",
        headers=auth_header_for_user(admin),
        json={"name": "Inexistente"},
    )
    assert response.status_code == 404


@pytest.mark.anyio
async def test_update_supplier_partial(
    client: httpx.AsyncClient,
    db_session,
    create_user,
    auth_header_for_user,
) -> None:
    admin = create_user(role=UserRole.ADMIN)
    supplier = create_supplier_in_db(db_session, specialty="Hidraulica")
    response = await client.patch(
        f"/suppliers/{supplier.id}",
        headers=auth_header_for_user(admin),
        json={"specialty": "Pneumatica"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["specialty"] == "Pneumatica"
    assert data["name"] == supplier.name
