from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.enums import UserRole
from app.schemas.auth import ProjectEmail
from app.schemas.pagination import PaginatedResponse, PageParams


class UserCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    email: ProjectEmail
    password: str = Field(min_length=8, max_length=255)
    role: UserRole
    unit_id: int | None = None
    is_active: bool = True

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Name is required.")
        return normalized

    @model_validator(mode="after")
    def validate_manager_unit(self) -> "UserCreate":
        if self.role == UserRole.MANAGER and self.unit_id is None:
            raise ValueError("Manager must have unit_id.")
        return self


class UserUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    email: ProjectEmail | None = None
    password: str | None = Field(default=None, min_length=8, max_length=255)
    role: UserRole | None = None
    unit_id: int | None = None
    is_active: bool | None = None

    @field_validator("name")
    @classmethod
    def normalize_optional_name(cls, value: str | None) -> str | None:
        if value is None:
            return value

        normalized = value.strip()
        if not normalized:
            raise ValueError("Name is required.")
        return normalized


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: ProjectEmail
    role: UserRole
    unit_id: int | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class UserListResponse(PaginatedResponse[UserResponse]):
    pass


class UserListParams(PageParams):
    search: str | None = None
    role: UserRole | None = None
    unit_id: int | None = Field(default=None, ge=1)
    is_active: bool | None = None
    sort: Literal["name_asc", "created_at_desc"] = "name_asc"

    @field_validator("search")
    @classmethod
    def strip_search(cls, value: str | None) -> str | None:
        if value is None:
            return value

        normalized = value.strip()
        return normalized or None
