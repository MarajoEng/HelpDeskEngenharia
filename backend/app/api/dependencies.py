from collections.abc import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db_session
from app.models.enums import UserRole
from app.models.user import User
from app.services.auth_service import (
    AuthenticationError,
    InsufficientPermissionsError,
    get_authenticated_user,
)


bearer_scheme = HTTPBearer(auto_error=False)


def _raise_http_auth_error(error: AuthenticationError) -> None:
    headers = {"WWW-Authenticate": "Bearer"} if error.status_code == status.HTTP_401_UNAUTHORIZED else None
    raise HTTPException(
        status_code=error.status_code,
        detail=error.detail,
        headers=headers,
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: Session = Depends(get_db_session),
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        return get_authenticated_user(session, credentials.credentials)
    except AuthenticationError as error:
        _raise_http_auth_error(error)


def require_roles(*allowed_roles: UserRole) -> Callable[[User], User]:
    allowed_role_set = set(allowed_roles)

    def dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_role_set:
            _raise_http_auth_error(InsufficientPermissionsError())

        return current_user

    return dependency
