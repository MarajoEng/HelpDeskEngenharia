import httpx
import pytest

from app.models.enums import UserRole


def make_approval_level_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "name": "Engenharia ate 1000",
        "min_amount": "0.00",
        "max_amount": "1000.00",
        "allowed_roles": ["engineering", "admin"],
        "is_active": True,
    }
    payload.update(overrides)
    return payload


@pytest.mark.anyio
async def test_admin_creates_approval_level(
    client: httpx.AsyncClient,
    create_user,
    auth_header_for_user,
) -> None:
    admin = create_user(role=UserRole.ADMIN)

    response = await client.post(
        "/approval-levels",
        headers=auth_header_for_user(admin),
        json=make_approval_level_payload(),
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Engenharia ate 1000"
    assert data["allowed_roles"] == ["engineering", "admin"]


@pytest.mark.anyio
async def test_manager_cannot_create_approval_level(
    client: httpx.AsyncClient,
    create_unit,
    create_user,
    auth_header_for_user,
) -> None:
    unit = create_unit()
    manager = create_user(role=UserRole.MANAGER, unit_id=unit.id)

    response = await client.post(
        "/approval-levels",
        headers=auth_header_for_user(manager),
        json=make_approval_level_payload(),
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "Insufficient permissions."}


@pytest.mark.anyio
async def test_supplier_cannot_access_approval_levels(
    client: httpx.AsyncClient,
    create_user,
    auth_header_for_user,
) -> None:
    supplier = create_user(role=UserRole.SUPPLIER)

    response = await client.get("/approval-levels", headers=auth_header_for_user(supplier))

    assert response.status_code == 403
    assert response.json() == {"detail": "Insufficient permissions."}


@pytest.mark.anyio
async def test_approval_levels_list_is_paginated(
    client: httpx.AsyncClient,
    create_user,
    create_approval_level,
    auth_header_for_user,
) -> None:
    director = create_user(role=UserRole.DIRECTOR)
    create_approval_level(name="Faixa 1")
    create_approval_level(name="Faixa 2", min_amount="1000.01", max_amount="5000.00", allowed_roles=["director", "admin"])
    create_approval_level(name="Faixa 3", min_amount="5000.01", max_amount=None, allowed_roles=["admin"])

    response = await client.get("/approval-levels?page=2&page_size=2", headers=auth_header_for_user(director))

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert data["page"] == 2
    assert data["page_size"] == 2
    assert data["pages"] == 2
    assert len(data["items"]) == 1


@pytest.mark.anyio
async def test_approval_level_invalid_allowed_roles_are_blocked(
    client: httpx.AsyncClient,
    create_user,
    auth_header_for_user,
) -> None:
    admin = create_user(role=UserRole.ADMIN)

    response = await client.post(
        "/approval-levels",
        headers=auth_header_for_user(admin),
        json=make_approval_level_payload(allowed_roles=["supplier"]),
    )

    assert response.status_code == 422


@pytest.mark.anyio
async def test_approval_level_min_greater_than_max_is_blocked(
    client: httpx.AsyncClient,
    create_user,
    auth_header_for_user,
) -> None:
    admin = create_user(role=UserRole.ADMIN)

    response = await client.post(
        "/approval-levels",
        headers=auth_header_for_user(admin),
        json=make_approval_level_payload(min_amount="2000.00", max_amount="1000.00"),
    )

    assert response.status_code == 422


@pytest.mark.anyio
async def test_approval_level_negative_range_is_blocked(
    client: httpx.AsyncClient,
    create_user,
    auth_header_for_user,
) -> None:
    admin = create_user(role=UserRole.ADMIN)

    response = await client.post(
        "/approval-levels",
        headers=auth_header_for_user(admin),
        json=make_approval_level_payload(min_amount="-1.00"),
    )

    assert response.status_code == 422


@pytest.mark.anyio
async def test_approval_level_overlapping_active_range_is_blocked(
    client: httpx.AsyncClient,
    create_user,
    create_approval_level,
    auth_header_for_user,
) -> None:
    admin = create_user(role=UserRole.ADMIN)
    create_approval_level(min_amount="0.00", max_amount="1000.00")

    response = await client.post(
        "/approval-levels",
        headers=auth_header_for_user(admin),
        json=make_approval_level_payload(name="Faixa sobreposta", min_amount="900.00", max_amount="1500.00"),
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "Active approval level range overlaps an existing active range."}


@pytest.mark.anyio
async def test_approval_level_null_max_amount_works_as_open_ended(
    client: httpx.AsyncClient,
    create_user,
    auth_header_for_user,
) -> None:
    admin = create_user(role=UserRole.ADMIN)

    response = await client.post(
        "/approval-levels",
        headers=auth_header_for_user(admin),
        json=make_approval_level_payload(
            name="Topo aberto",
            min_amount="5000.01",
            max_amount=None,
            allowed_roles=["admin"],
        ),
    )

    assert response.status_code == 201
    assert response.json()["max_amount"] is None


@pytest.mark.anyio
async def test_inactivate_approval_level_works(
    client: httpx.AsyncClient,
    create_user,
    create_approval_level,
    auth_header_for_user,
) -> None:
    admin = create_user(role=UserRole.ADMIN)
    approval_level = create_approval_level()

    response = await client.patch(
        f"/approval-levels/{approval_level.id}",
        headers=auth_header_for_user(admin),
        json={"is_active": False},
    )

    assert response.status_code == 200
    assert response.json()["is_active"] is False
