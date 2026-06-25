from __future__ import annotations

from pathlib import Path
import sys


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from app.core.config import get_settings
from app.core.database import get_session_factory
from app.core.security import hash_password
from app.models.enums import UserRole
from app.models.user import User
from app.repositories.user_repository import get_user_by_email
from app.schemas import UserCreateInternal


DEV_ADMIN = UserCreateInternal(
    name="Admin",
    email="admin@local.test",
    password="admin123",
    role=UserRole.ADMIN,
)


def main() -> None:
    settings = get_settings()
    if settings.app_env.lower() == "production":
        raise SystemExit("Refusing to create development admin in production.")

    session_factory = get_session_factory()
    session = session_factory()

    try:
        user = get_user_by_email(session, DEV_ADMIN.email)
        action = "updated"

        if user is None:
            user = User(
                name=DEV_ADMIN.name,
                email=DEV_ADMIN.email,
                password_hash=hash_password(DEV_ADMIN.password),
                role=DEV_ADMIN.role,
                unit_id=DEV_ADMIN.unit_id,
                is_active=DEV_ADMIN.is_active,
            )
            session.add(user)
            action = "created"
        else:
            user.name = DEV_ADMIN.name
            user.password_hash = hash_password(DEV_ADMIN.password)
            user.role = DEV_ADMIN.role
            user.unit_id = DEV_ADMIN.unit_id
            user.is_active = DEV_ADMIN.is_active

        session.commit()
        print(f"Development admin {action}: {DEV_ADMIN.email}")
    finally:
        session.close()


if __name__ == "__main__":
    main()
