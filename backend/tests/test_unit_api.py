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


@pytest.mark.anyio
async def test_create_unit_with_group_and_branch_code(
    client: httpx.AsyncClient,
    create_user,
    auth_header_for_user,
) -> None:
    admin = create_user(role=UserRole.ADMIN)

    response = await client.post(
        "/units",
        headers=auth_header_for_user(admin),
        json={
            "group_code": "02",
            "branch_code": "4301",
            "name": "Posto Piloto",
            "city": "Curitiba",
            "state": "PR",
            "region": "Sul",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["group_code"] == "02"
    assert data["branch_code"] == "4301"
    assert data["code"] == "02-4301"


@pytest.mark.anyio
async def test_group_branch_preserves_leading_zeros(
    client: httpx.AsyncClient,
    create_user,
    auth_header_for_user,
) -> None:
    admin = create_user(role=UserRole.ADMIN)

    response = await client.post(
        "/units",
        headers=auth_header_for_user(admin),
        json={
            "group_code": "01",
            "branch_code": "0101",
            "name": "Matriz SP",
            "city": "São Paulo",
            "state": "SP",
            "region": "Sudeste",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["code"] == "01-0101"
    assert data["group_code"] == "01"
    assert data["branch_code"] == "0101"


@pytest.mark.anyio
async def test_legacy_unit_without_group_branch_continues_working(
    client: httpx.AsyncClient,
    create_unit,
    create_user,
    auth_header_for_user,
) -> None:
    admin = create_user(role=UserRole.ADMIN)
    unit = create_unit(code="0901")

    response = await client.get(f"/units/{unit.id}", headers=auth_header_for_user(admin))

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == "0901"
    assert data["group_code"] is None
    assert data["branch_code"] is None


@pytest.mark.anyio
async def test_update_unit_group_branch_recomputes_code(
    client: httpx.AsyncClient,
    create_unit,
    create_user,
    auth_header_for_user,
) -> None:
    admin = create_user(role=UserRole.ADMIN)
    unit = create_unit(code="U-001")

    response = await client.patch(
        f"/units/{unit.id}",
        headers=auth_header_for_user(admin),
        json={"group_code": "05", "branch_code": "5001"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == "05-5001"
    assert data["group_code"] == "05"
    assert data["branch_code"] == "5001"


@pytest.mark.anyio
async def test_search_by_group_code(
    client: httpx.AsyncClient,
    create_user,
    auth_header_for_user,
    db_session,
) -> None:
    from app.models.unit import Unit

    admin = create_user(role=UserRole.ADMIN)
    db_session.add(Unit(code="02-4301", group_code="02", branch_code="4301", name="Posto Sul", city="Curitiba", state="PR", region="Sul", is_active=True))
    db_session.add(Unit(code="09-0901", group_code="09", branch_code="0901", name="Posto Norte", city="Manaus", state="AM", region="Norte", is_active=True))
    db_session.commit()

    response = await client.get("/units?search=02", headers=auth_header_for_user(admin))

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["code"] == "02-4301"


@pytest.mark.anyio
async def test_create_unit_without_code_or_group_branch_fails(
    client: httpx.AsyncClient,
    create_user,
    auth_header_for_user,
) -> None:
    admin = create_user(role=UserRole.ADMIN)

    response = await client.post(
        "/units",
        headers=auth_header_for_user(admin),
        json={
            "name": "Sem Código",
            "city": "Brasília",
            "state": "DF",
            "region": "Centro-Oeste",
        },
    )

    assert response.status_code == 422


@pytest.mark.anyio
async def test_filter_units_by_group_code(
    client: httpx.AsyncClient,
    create_user,
    auth_header_for_user,
    db_session,
) -> None:
    from app.models.unit import Unit

    admin = create_user(role=UserRole.ADMIN)
    db_session.add(Unit(code="02-4301", group_code="02", branch_code="4301", name="Filial A", city="SP", state="SP", region="Sudeste", is_active=True))
    db_session.add(Unit(code="02-4302", group_code="02", branch_code="4302", name="Filial B", city="SP", state="SP", region="Sudeste", is_active=True))
    db_session.add(Unit(code="03-0101", group_code="03", branch_code="0101", name="Outro Grupo", city="RJ", state="RJ", region="Sudeste", is_active=True))
    db_session.commit()

    response = await client.get("/units?group_code=02", headers=auth_header_for_user(admin))

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    codes = [item["code"] for item in data["items"]]
    assert "02-4301" in codes
    assert "02-4302" in codes
    assert "03-0101" not in codes


@pytest.mark.anyio
async def test_filter_units_by_branch_code(
    client: httpx.AsyncClient,
    create_user,
    auth_header_for_user,
    db_session,
) -> None:
    from app.models.unit import Unit

    admin = create_user(role=UserRole.ADMIN)
    db_session.add(Unit(code="02-4301", group_code="02", branch_code="4301", name="Filial A", city="SP", state="SP", region="Sudeste", is_active=True))
    db_session.add(Unit(code="03-4301", group_code="03", branch_code="4301", name="Outra Filial", city="RJ", state="RJ", region="Sudeste", is_active=True))
    db_session.add(Unit(code="02-4302", group_code="02", branch_code="4302", name="Filial B", city="SP", state="SP", region="Sudeste", is_active=True))
    db_session.commit()

    response = await client.get("/units?branch_code=4301", headers=auth_header_for_user(admin))

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    codes = [item["code"] for item in data["items"]]
    assert "02-4301" in codes
    assert "03-4301" in codes
    assert "02-4302" not in codes


@pytest.mark.anyio
async def test_units_groups_endpoint_returns_distinct_groups(
    client: httpx.AsyncClient,
    create_user,
    auth_header_for_user,
    db_session,
) -> None:
    from app.models.unit import Unit

    admin = create_user(role=UserRole.ADMIN)
    db_session.add(Unit(code="02-4301", group_code="02", branch_code="4301", name="Filial A", city="SP", state="SP", region="Sudeste", is_active=True))
    db_session.add(Unit(code="02-4302", group_code="02", branch_code="4302", name="Filial B", city="SP", state="SP", region="Sudeste", is_active=True))
    db_session.add(Unit(code="03-0101", group_code="03", branch_code="0101", name="Outro", city="RJ", state="RJ", region="Sudeste", is_active=True))
    db_session.add(Unit(code="LEG-001", name="Legado", city="BH", state="MG", region="Sudeste", is_active=True))
    db_session.commit()

    response = await client.get("/units/groups", headers=auth_header_for_user(admin))

    assert response.status_code == 200
    data = response.json()
    group_codes = [item["group_code"] for item in data]
    assert "02" in group_codes
    assert "03" in group_codes
    group_02 = next(item for item in data if item["group_code"] == "02")
    assert group_02["total_units"] == 2


@pytest.mark.anyio
async def test_legacy_unit_without_group_branch_still_lists(
    client: httpx.AsyncClient,
    create_user,
    auth_header_for_user,
    db_session,
) -> None:
    from app.models.unit import Unit

    admin = create_user(role=UserRole.ADMIN)
    db_session.add(Unit(code="LEG-001", name="Legado", city="BH", state="MG", region="Sudeste", is_active=True))
    db_session.commit()

    response = await client.get("/units", headers=auth_header_for_user(admin))

    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    legacy = next((item for item in data["items"] if item["code"] == "LEG-001"), None)
    assert legacy is not None
    assert legacy["group_code"] is None
    assert legacy["branch_code"] is None
