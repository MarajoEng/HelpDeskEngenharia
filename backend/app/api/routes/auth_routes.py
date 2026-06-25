from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.database import get_db_session
from app.core.rate_limit import login_rate_limiter
from app.models.user import User
from app.schemas import CurrentUserResponse, LoginRequest, TokenResponse
from app.services.audit_service import log_action
from app.services.auth_service import AuthenticationError, authenticate_user, build_access_token


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request, session: Session = Depends(get_db_session)) -> TokenResponse:
    client_ip = request.client.host if request.client else "unknown"
    rate_key = f"{client_ip}:{payload.email}"

    if not login_rate_limiter.check_and_record(rate_key):
        log_action(
            session,
            actor_user=None,
            action="login_rate_limited",
            entity_type="auth",
            request=request,
            metadata={"email": payload.email},
        )
        session.commit()
        raise HTTPException(status_code=429, detail="Muitas tentativas de login. Aguarde antes de tentar novamente.")

    try:
        user = authenticate_user(session, payload.email, payload.password)
    except AuthenticationError as error:
        log_action(
            session,
            actor_user=None,
            action="login_failed",
            entity_type="auth",
            request=request,
            metadata={"email": payload.email},
        )
        session.commit()
        headers = {"WWW-Authenticate": "Bearer"} if error.status_code == 401 else None
        raise HTTPException(
            status_code=error.status_code,
            detail=error.detail,
            headers=headers,
        ) from error

    log_action(
        session,
        actor_user=user,
        action="login_success",
        entity_type="user",
        entity_id=user.id,
        request=request,
        metadata={"email": user.email},
    )
    session.commit()
    return TokenResponse(
        access_token=build_access_token(user),
        token_type="bearer",
    )


@router.get("/me", response_model=CurrentUserResponse)
def read_current_user(current_user: User = Depends(get_current_user)) -> CurrentUserResponse:
    return CurrentUserResponse.model_validate(current_user)
