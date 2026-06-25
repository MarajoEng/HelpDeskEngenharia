import httpx
import pytest

from app.models.enums import UserRole


@pytest.mark.anyio
async def test_admin_creates_unit(
    client: httpx.AsyncClient,
    create_user,
    auth_header_for_user,
) -> None:
    admin = create_user(role=UserRole.ADMIN)

    response = await client.post(
        "/units",
        headers=auth_header_for_user(admin),
        json={
            "code": "abc-01",
            "name": "Unidade Norte",
            "city": "Campinas",
            "state": "sp",
            "region": "Interior",
        },
    )

    assert response.status_code == 201
    assert response.json()["code"] == "ABC-01"
    assert response.json()["state"] == "SP"
    assert response.json()["is_active"] is True


@pytest.mark.anyio
async def test_non_admin_cannot_create_unit(
    client: httpx.AsyncClient,
    create_user,
    auth_header_for_user,
) -> None:
    engineering = create_user(role=UserRole.ENGINEERING)

    response = await client.post(
        "/units",
        headers=auth_header_for_user(engineering),
        json={
            "code": "U-100",
            "name": "Unidade Sul",
            "city": "Curitiba",
            "state": "PR",
            "region": "Sul",
        },
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "Insufficient permissions."}


@pytest.mark.anyio
async def test_duplicate_unit_code_is_blocked(
    client: httpx.AsyncClient,
    create_unit,
    create_user,
    auth_header_for_user,
) -> None:
    admin = create_user(role=UserRole.ADMIN)
    create_unit(code="U-001")

    response = await client.post(
        "/units",
        headers=auth_header_for_user(admin),
        json={
            "code": "u-001",
            "name": "Outra Unidade",
            "city": "Santos",
            "state": "SP",
            "region": "Litoral",
        },
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "Unit code already exists."}


@pytest.mark.anyio
async def test_units_list_is_paginated(
    client: httpx.AsyncClient,
    create_unit,
    create_user,
    auth_header_for_user,
) -> None:
    admin = create_user(role=UserRole.ADMIN)
    create_unit(code="U-001", name="Alpha")
    create_unit(code="U-002", name="Bravo")
    create_unit(code="U-003", name="Charlie")

    response = await client.get(
        "/units?page=2&page_size=2",
        headers=auth_header_for_user(admin),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert data["page"] == 2
    assert data["page_size"] == 2
    assert data["pages"] == 2
    assert len(data["items"]) == 1
    assert data["items"][0]["name"] == "Charlie"


@pytest.mark.anyio
async def test_units_search_filter_works(
    client: httpx.AsyncClient,
    create_unit,
    create_user,
    auth_header_for_user,
) -> None:
    admin = create_user(role=UserRole.ADMIN)
    create_unit(code="U-001", name="Matriz Paulista", city="Sao Paulo", region="Sudeste")
    create_unit(code="U-002", name="Filial Sul", city="Curitiba", region="Sul")

    response = await client.get(
        "/units?search=Paulista",
        headers=auth_header_for_user(admin),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["code"] == "U-001"


@pytest.mark.anyio
async def test_unit_update_works(
    client: httpx.AsyncClient,
    create_unit,
    create_user,
    auth_header_for_user,
) -> None:
    admin = create_user(role=UserRole.ADMIN)
    unit = create_unit(code="U-001", name="Original", city="Sao Paulo", region="Sudeste")

    response = await client.patch(
        f"/units/{unit.id}",
        headers=auth_header_for_user(admin),
        json={"name": "Atualizada", "is_active": False},
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Atualizada"
    assert response.json()["is_active"] is False


@pytest.mark.anyio
async def test_unit_not_found_returns_404(
    client: httpx.AsyncClient,
    create_user,
    auth_header_for_user,
) -> None:
    admin = create_user(role=UserRole.ADMIN)

    response = await client.get("/units/999", headers=auth_header_for_user(admin))

    assert response.status_code == 404
    assert response.json() == {"detail": "Unit not found."}
