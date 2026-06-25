from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.security import InvalidTokenError, create_access_token, decode_access_token, verify_password
from app.models.user import User
from app.repositories.user_repository import get_user_by_email, get_user_by_id


class AuthenticationError(Exception):
    status_code = 401
    detail = "Invalid email or password."


class InvalidCredentialsError(AuthenticationError):
    detail = "Invalid email or password."


class InactiveUserError(AuthenticationError):
    status_code = 403
    detail = "Inactive user."


class TokenValidationError(AuthenticationError):
    detail = "Invalid or expired token."


class InsufficientPermissionsError(AuthenticationError):
    status_code = 403
    detail = "Insufficient permissions."


def authenticate_user(session: Session, email: str, password: str) -> User:
    user = get_user_by_email(session, email)
    if user is None or not verify_password(password, user.password_hash):
        raise InvalidCredentialsError

    if not user.is_active:
        raise InactiveUserError

    return user


def build_access_token(user: User) -> str:
    return create_access_token(
        user.id,
        extra_claims={"role": user.role.value},
    )


def get_authenticated_user(session: Session, token: str) -> User:
    try:
        payload = decode_access_token(token)
    except InvalidTokenError as exc:
        raise TokenValidationError from exc

    subject = payload.get("sub")
    try:
        user_id = int(subject)
    except (TypeError, ValueError) as exc:
        raise TokenValidationError from exc

    user = get_user_by_id(session, user_id)
    if user is None:
        raise TokenValidationError

    if not user.is_active:
        raise InactiveUserError

    return user
