from typing import Annotated

from email_validator import EmailNotValidError, validate_email
from pydantic import AfterValidator, BaseModel, ConfigDict, Field

from app.models.enums import UserRole


def validate_project_email(value: str) -> str:
    try:
        result = validate_email(
            value,
            check_deliverability=False,
            test_environment=value.lower().endswith(".test"),
        )
    except EmailNotValidError as exc:
        raise ValueError(str(exc)) from exc

    return result.normalized


ProjectEmail = Annotated[str, AfterValidator(validate_project_email)]


class LoginRequest(BaseModel):
    email: ProjectEmail
    password: str = Field(min_length=1, max_length=255)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class CurrentUserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: ProjectEmail
    role: UserRole
    unit_id: int | None
    is_active: bool


class UserCreateInternal(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    email: ProjectEmail
    password: str = Field(min_length=8, max_length=255)
    role: UserRole
    unit_id: int | None = None
    is_active: bool = True
