from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.dependencies import require_roles
from app.core.database import get_db_session
from app.models.enums import UserRole
from app.models.ticket import Ticket
from app.models.ticket_alert import TicketAlert
from app.models.unit import Unit
from app.models.user import User


router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live")
def live() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/demo")
def demo_health(
    _: User = Depends(require_roles(UserRole.ADMIN)),
    session: Session = Depends(get_db_session),
) -> dict[str, Any]:
    try:
        total_units = session.scalar(select(func.count()).select_from(Unit)) or 0
        total_users = session.scalar(select(func.count()).select_from(User)) or 0
        total_tickets = session.scalar(select(func.count()).select_from(Ticket)) or 0
        total_alerts = session.scalar(select(func.count()).select_from(TicketAlert)) or 0
        database_ok = True
    except Exception:
        database_ok = False
        total_units = total_users = total_tickets = total_alerts = 0

    return {
        "database_ok": database_ok,
        "total_units": total_units,
        "total_users": total_users,
        "total_tickets": total_tickets,
        "total_alerts": total_alerts,
    }
