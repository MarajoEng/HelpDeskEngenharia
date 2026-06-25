from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.database import get_db_session
from app.models.user import User
from app.schemas import CurrentUserResponse, LoginRequest, TokenResponse
from app.services.auth_service import AuthenticationError, authenticate_user, build_access_token


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, session: Session = Depends(get_db_session)) -> TokenResponse:
    try:
        user = authenticate_user(session, payload.email, payload.password)
    except AuthenticationError as error:
        headers = {"WWW-Authenticate": "Bearer"} if error.status_code == 401 else None
        raise HTTPException(
            status_code=error.status_code,
            detail=error.detail,
            headers=headers,
        ) from error

    return TokenResponse(
        access_token=build_access_token(user),
        token_type="bearer",
    )


@router.get("/me", response_model=CurrentUserResponse)
def read_current_user(current_user: User = Depends(get_current_user)) -> CurrentUserResponse:
    return CurrentUserResponse.model_validate(current_user)
