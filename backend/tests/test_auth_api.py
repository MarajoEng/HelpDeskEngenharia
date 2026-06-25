from collections.abc import Generator

import httpx
import pytest
from fastapi import Depends

from app.api.dependencies import require_roles
from app.core.database import get_db_session
from app.main import create_application
from app.models.enums import UserRole
from app.models.user import User


@pytest.mark.anyio
async def test_login_returns_access_token_for_valid_credentials(
    client: httpx.AsyncClient,
    create_user,
) -> None:
    create_user(email="admin@local.test", password="admin123")

    response = await client.post(
        "/auth/login",
        json={"email": "admin@local.test", "password": "admin123"},
    )

    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    assert response.json()["access_token"]


@pytest.mark.anyio
async def test_login_rejects_invalid_password(
    client: httpx.AsyncClient,
    create_user,
) -> None:
    create_user(email="admin@local.test", password="admin123")

    response = await client.post(
        "/auth/login",
        json={"email": "admin@local.test", "password": "wrong-pass"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid email or password."}


@pytest.mark.anyio
async def test_login_blocks_inactive_user(
    client: httpx.AsyncClient,
    create_user,
) -> None:
    create_user(email="inactive@local.test", password="admin123", is_active=False)

    response = await client.post(
        "/auth/login",
        json={"email": "inactive@local.test", "password": "admin123"},
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "Inactive user."}


@pytest.mark.anyio
async def test_auth_me_returns_current_user(
    client: httpx.AsyncClient,
    create_user,
    auth_header_for_user,
) -> None:
    user = create_user(email="manager@local.test", password="admin123", role=UserRole.MANAGER)

    response = await client.get("/auth/me", headers=auth_header_for_user(user))

    assert response.status_code == 200
    assert response.json() == {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role.value,
        "unit_id": user.unit_id,
        "is_active": True,
    }


@pytest.mark.anyio
async def test_auth_me_requires_bearer_token(client: httpx.AsyncClient) -> None:
    response = await client.get("/auth/me")

    assert response.status_code == 401
    assert response.json() == {"detail": "Authentication credentials were not provided."}


@pytest.mark.anyio
async def test_auth_me_blocks_inactive_user(
    client: httpx.AsyncClient,
    create_user,
    auth_header_for_user,
) -> None:
    user = create_user(email="inactive@local.test", password="admin123", is_active=False)

    response = await client.get("/auth/me", headers=auth_header_for_user(user))

    assert response.status_code == 403
    assert response.json() == {"detail": "Inactive user."}


@pytest.mark.anyio
async def test_require_roles_allows_expected_role(
    db_session,
    create_user,
    auth_header_for_user,
) -> None:
    user = create_user(email="admin@local.test", role=UserRole.ADMIN)
    test_app = create_application()

    @test_app.get("/authz/admin")
    def admin_only(current_user: User = Depends(require_roles(UserRole.ADMIN))) -> dict[str, str]:
        return {"email": current_user.email}

    def override_get_db_session() -> Generator:
        yield db_session

    test_app.dependency_overrides[get_db_session] = override_get_db_session
    transport = httpx.ASGITransport(app=test_app)

    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as role_client:
        response = await role_client.get("/authz/admin", headers=auth_header_for_user(user))

    test_app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json() == {"email": "admin@local.test"}


@pytest.mark.anyio
async def test_require_roles_blocks_unexpected_role(
    db_session,
    create_user,
    auth_header_for_user,
) -> None:
    user = create_user(email="manager@local.test", role=UserRole.MANAGER)
    test_app = create_application()

    @test_app.get("/authz/admin")
    def admin_only(current_user: User = Depends(require_roles(UserRole.ADMIN))) -> dict[str, str]:
        return {"email": current_user.email}

    def override_get_db_session() -> Generator:
        yield db_session

    test_app.dependency_overrides[get_db_session] = override_get_db_session
    transport = httpx.ASGITransport(app=test_app)

    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as role_client:
        response = await role_client.get("/authz/admin", headers=auth_header_for_user(user))

    test_app.dependency_overrides.clear()
    assert response.status_code == 403
    assert response.json() == {"detail": "Insufficient permissions."}
