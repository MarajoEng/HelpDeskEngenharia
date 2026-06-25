from __future__ import annotations

from decimal import Decimal
from pathlib import Path
import sys


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from app.core.config import get_settings
from app.core.database import get_session_factory
from app.models.approval_level import ApprovalLevel
from app.models.enums import UserRole
from app.repositories.approval_level_repository import get_approval_level_by_id


DEFAULT_APPROVAL_LEVELS = [
    {
        "id": 1,
        "name": "Engenharia ate 1000",
        "min_amount": Decimal("0.00"),
        "max_amount": Decimal("1000.00"),
        "allowed_roles": [UserRole.ENGINEERING.value, UserRole.ADMIN.value],
    },
    {
        "id": 2,
        "name": "Diretoria ate 5000",
        "min_amount": Decimal("1000.01"),
        "max_amount": Decimal("5000.00"),
        "allowed_roles": [UserRole.DIRECTOR.value, UserRole.ADMIN.value],
    },
    {
        "id": 3,
        "name": "Alta alcada acima de 5000",
        "min_amount": Decimal("5000.01"),
        "max_amount": None,
        "allowed_roles": [UserRole.ADMIN.value],
    },
]


def main() -> None:
    settings = get_settings()
    if settings.app_env.lower() == "production":
        raise SystemExit("Refusing to seed approval levels in production.")

    session_factory = get_session_factory()
    session = session_factory()

    try:
        for payload in DEFAULT_APPROVAL_LEVELS:
            approval_level = get_approval_level_by_id(session, payload["id"])
            action = "updated"

            if approval_level is None:
                approval_level = ApprovalLevel(**payload, is_active=True)
                session.add(approval_level)
                action = "created"
            else:
                approval_level.name = payload["name"]
                approval_level.min_amount = payload["min_amount"]
                approval_level.max_amount = payload["max_amount"]
                approval_level.allowed_roles = payload["allowed_roles"]
                approval_level.is_active = True

            print(f"Approval level {action}: {payload['name']}")

        session.commit()
    finally:
        session.close()


if __name__ == "__main__":
    main()
