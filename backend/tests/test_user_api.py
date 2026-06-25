import httpx
import pytest

from app.core.security import verify_password
from app.models.enums import UserRole
from app.models.user import User


@pytest.mark.anyio
async def test_admin_creates_user(
    client: httpx.AsyncClient,
    create_user,
    create_unit,
    auth_header_for_user,
) -> None:
    admin = create_user(role=UserRole.ADMIN)
    unit = create_unit()

    response = await client.post(
        "/users",
        headers=auth_header_for_user(admin),
        json={
            "name": "Gestor Unidade",
            "email": "gestor@local.test",
            "password": "gestor123",
            "role": "manager",
            "unit_id": unit.id,
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "gestor@local.test"
    assert data["role"] == "manager"
    assert "password_hash" not in data


@pytest.mark.anyio
async def test_duplicate_user_email_is_blocked(
    client: httpx.AsyncClient,
    create_user,
    auth_header_for_user,
) -> None:
    admin = create_user(role=UserRole.ADMIN)
    create_user(email="duplicado@local.test")

    response = await client.post(
        "/users",
        headers=auth_header_for_user(admin),
        json={
            "name": "Usuario Duplicado",
            "email": "duplicado@local.test",
            "password": "senha123",
            "role": "supplier",
        },
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "User email already exists."}


@pytest.mark.anyio
async def test_password_is_saved_as_hash(
    client: httpx.AsyncClient,
    db_session,
    create_user,
    create_unit,
    auth_header_for_user,
) -> None:
    admin = create_user(role=UserRole.ADMIN)
    unit = create_unit()

    response = await client.post(
        "/users",
        headers=auth_header_for_user(admin),
        json={
            "name": "Gerente Hash",
            "email": "hash@local.test",
            "password": "senha123",
            "role": "manager",
            "unit_id": unit.id,
        },
    )

    assert response.status_code == 201
    created_user = db_session.get(User, response.json()["id"])
    assert created_user is not None
    assert created_user.password_hash != "senha123"
    assert verify_password("senha123", created_user.password_hash) is True


@pytest.mark.anyio
async def test_manager_without_unit_is_blocked(
    client: httpx.AsyncClient,
    create_user,
    auth_header_for_user,
) -> None:
    admin = create_user(role=UserRole.ADMIN)

    response = await client.post(
        "/users",
        headers=auth_header_for_user(admin),
        json={
            "name": "Manager Sem Unidade",
            "email": "manager.sem.unidade@local.test",
            "password": "senha123",
            "role": "manager",
        },
    )

    assert response.status_code == 422


@pytest.mark.anyio
async def test_nonexistent_unit_id_is_blocked_for_user_creation(
    client: httpx.AsyncClient,
    create_user,
    auth_header_for_user,
) -> None:
    admin = create_user(role=UserRole.ADMIN)

    response = await client.post(
        "/users",
        headers=auth_header_for_user(admin),
        json={
            "name": "Usuario Sem Unidade Valida",
            "email": "sem.unidade@local.test",
            "password": "senha123",
            "role": "manager",
            "unit_id": 999,
        },
    )

    assert response.status_code == 422
    assert response.json() == {"detail": "Provided unit does not exist."}


@pytest.mark.anyio
async def test_users_list_is_paginated(
    client: httpx.AsyncClient,
    create_user,
    auth_header_for_user,
) -> None:
    admin = create_user(email="admin.master@local.test", role=UserRole.ADMIN)
    create_user(name="Bruno", email="bruno@local.test", role=UserRole.SUPPLIER)
    create_user(name="Carlos", email="carlos@local.test", role=UserRole.ENGINEERING)

    response = await client.get(
        "/users?page=1&page_size=2",
        headers=auth_header_for_user(admin),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert data["page"] == 1
    assert data["page_size"] == 2
    assert len(data["items"]) == 2


@pytest.mark.anyio
async def test_users_filters_by_role_and_is_active(
    client: httpx.AsyncClient,
    create_user,
    create_unit,
    auth_header_for_user,
) -> None:
    admin = create_user(email="admin.filter@local.test", role=UserRole.ADMIN)
    unit = create_unit()
    create_user(
        name="Manager Ativo",
        email="manager.ativo@local.test",
        role=UserRole.MANAGER,
        unit_id=unit.id,
        is_active=True,
    )
    create_user(
        name="Manager Inativo",
        email="manager.inativo@local.test",
        role=UserRole.MANAGER,
        unit_id=unit.id,
        is_active=False,
    )

    response = await client.get(
        "/users?role=manager&is_active=false",
        headers=auth_header_for_user(admin),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["email"] == "manager.inativo@local.test"


@pytest.mark.anyio
async def test_non_admin_cannot_access_user_list(
    client: httpx.AsyncClient,
    create_user,
    create_unit,
    auth_header_for_user,
) -> None:
    unit = create_unit()
    manager = create_user(role=UserRole.MANAGER, unit_id=unit.id)

    response = await client.get("/users", headers=auth_header_for_user(manager))

    assert response.status_code == 403
    assert response.json() == {"detail": "Insufficient permissions."}
