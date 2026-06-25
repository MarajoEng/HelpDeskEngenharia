from collections.abc import AsyncGenerator, Generator

import httpx
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings
from app.core.database import get_db_session
from app.core.security import create_access_token, hash_password
from app.main import app
from app.models import Base
from app.models.enums import UserRole
from app.models.approval_level import ApprovalLevel
from app.models.unit import Unit
from app.models.user import User


@pytest.fixture(autouse=True)
def auth_settings(monkeypatch: pytest.MonkeyPatch, tmp_path) -> Generator[None, None, None]:
    monkeypatch.setenv("SECRET_KEY", "test-secret-key")
    monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
    monkeypatch.setenv("ALGORITHM", "HS256")
    monkeypatch.setenv("MAX_UPLOAD_SIZE_MB", "1")
    monkeypatch.setenv("UPLOAD_DIR", str(tmp_path / "uploads"))
    get_settings.cache_clear()
    from app.core.rate_limit import login_rate_limiter
    login_rate_limiter.clear_all()
    yield
    get_settings.cache_clear()
    login_rate_limiter.clear_all()


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session_factory = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )

    Base.metadata.create_all(bind=engine)
    session = testing_session_factory()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture
async def client(db_session: Session) -> AsyncGenerator[httpx.AsyncClient, None]:
    def override_get_db_session() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db_session] = override_get_db_session
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as async_client:
        yield async_client

    app.dependency_overrides.clear()


@pytest.fixture
def create_user(db_session: Session):
    def factory(
        *,
        name: str = "Admin",
        email: str = "admin@local.test",
        password: str = "admin123",
        role: UserRole = UserRole.ADMIN,
        unit_id: int | None = None,
        is_active: bool = True,
    ) -> User:
        user = User(
            name=name,
            email=email,
            password_hash=hash_password(password),
            role=role,
            unit_id=unit_id,
            is_active=is_active,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user

    return factory


@pytest.fixture
def create_unit(db_session: Session):
    def factory(
        *,
        code: str = "U-001",
        name: str = "Unidade Centro",
        city: str = "Sao Paulo",
        state: str = "SP",
        region: str = "Sudeste",
        is_active: bool = True,
    ) -> Unit:
        unit = Unit(
            code=code,
            name=name,
            city=city,
            state=state,
            region=region,
            is_active=is_active,
        )
        db_session.add(unit)
        db_session.commit()
        db_session.refresh(unit)
        return unit

    return factory


@pytest.fixture
def create_approval_level(db_session: Session):
    def factory(
        *,
        name: str = "Engenharia ate 1000",
        min_amount="0.00",
        max_amount="1000.00",
        allowed_roles: list[str] | None = None,
        is_active: bool = True,
    ) -> ApprovalLevel:
        approval_level = ApprovalLevel(
            name=name,
            min_amount=min_amount,
            max_amount=max_amount,
            allowed_roles=allowed_roles or [UserRole.ENGINEERING.value, UserRole.ADMIN.value],
            is_active=is_active,
        )
        db_session.add(approval_level)
        db_session.commit()
        db_session.refresh(approval_level)
        return approval_level

    return factory


@pytest.fixture
def auth_header_for_user():
    def factory(user: User) -> dict[str, str]:
        token = create_access_token(
            user.id,
            extra_claims={"role": user.role.value},
        )
        return {"Authorization": f"Bearer {token}"}

    return factory
