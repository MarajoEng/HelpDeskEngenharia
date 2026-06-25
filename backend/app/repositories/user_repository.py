from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.user import User


def get_user_by_email(session: Session, email: str) -> User | None:
    normalized_email = email.strip().lower()
    statement = select(User).where(func.lower(User.email) == normalized_email).limit(1)
    return session.scalar(statement)


def get_user_by_id(session: Session, user_id: int) -> User | None:
    statement = select(User).where(User.id == user_id).limit(1)
    return session.scalar(statement)
