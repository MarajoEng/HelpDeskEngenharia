from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.schemas.pagination import PaginatedResponse, PageParams


class UnitBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    city: str = Field(min_length=1, max_length=120)
    state: str = Field(min_length=2, max_length=2)
    region: str = Field(min_length=1, max_length=120)
    is_active: bool = True

    @field_validator("name", "city", "region")
    @classmethod
    def strip_text_fields(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Field cannot be empty.")
        return normalized

    @field_validator("state")
    @classmethod
    def normalize_state(cls, value: str) -> str:
        normalized = value.strip().upper()
        if len(normalized) != 2:
            raise ValueError("State must have 2 characters.")
        return normalized


class UnitCreate(UnitBase):
    code: str | None = Field(default=None, min_length=1, max_length=50)
    group_code: str | None = Field(default=None, min_length=1, max_length=20)
    branch_code: str | None = Field(default=None, min_length=1, max_length=20)

    @field_validator("code", "group_code", "branch_code")
    @classmethod
    def strip_code_fields(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        if not normalized:
            raise ValueError("Field cannot be empty.")
        return normalized

    @model_validator(mode="after")
    def resolve_code_from_group_branch(self) -> "UnitCreate":
        if self.group_code and self.branch_code:
            self.code = f"{self.group_code}-{self.branch_code}"
        elif not self.code:
            raise ValueError("Forneça group_code e branch_code, ou code legado.")
        return self


class UnitUpdate(BaseModel):
    code: str | None = Field(default=None, min_length=1, max_length=50)
    group_code: str | None = Field(default=None, min_length=1, max_length=20)
    branch_code: str | None = Field(default=None, min_length=1, max_length=20)
    name: str | None = Field(default=None, min_length=1, max_length=255)
    city: str | None = Field(default=None, min_length=1, max_length=120)
    state: str | None = Field(default=None, min_length=2, max_length=2)
    region: str | None = Field(default=None, min_length=1, max_length=120)
    is_active: bool | None = None

    @field_validator("code", "group_code", "branch_code", "name", "city", "region")
    @classmethod
    def strip_optional_text_fields(cls, value: str | None) -> str | None:
        if value is None:
            return value
        normalized = value.strip()
        if not normalized:
            raise ValueError("Field cannot be empty.")
        return normalized

    @field_validator("state")
    @classmethod
    def normalize_optional_state(cls, value: str | None) -> str | None:
        if value is None:
            return value
        normalized = value.strip().upper()
        if len(normalized) != 2:
            raise ValueError("State must have 2 characters.")
        return normalized


class UnitResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    group_code: str | None
    branch_code: str | None
    name: str
    city: str
    state: str
    region: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class UnitListResponse(PaginatedResponse[UnitResponse]):
    pass


class UnitListParams(PageParams):
    search: str | None = None
    is_active: bool | None = None
    state: str | None = Field(default=None, min_length=2, max_length=2)
    region: str | None = Field(default=None, min_length=1, max_length=120)
    group_code: str | None = Field(default=None, min_length=1, max_length=20)
    branch_code: str | None = Field(default=None, min_length=1, max_length=20)
    sort: Literal["name_asc", "created_at_desc"] = "name_asc"

    @field_validator("search", "region", "group_code", "branch_code")
    @classmethod
    def strip_optional_filters(cls, value: str | None) -> str | None:
        if value is None:
            return value
        normalized = value.strip()
        return normalized or None

    @field_validator("state")
    @classmethod
    def normalize_optional_filter_state(cls, value: str | None) -> str | None:
        if value is None:
            return value
        normalized = value.strip().upper()
        if len(normalized) != 2:
            raise ValueError("State must have 2 characters.")
        return normalized


class UnitGroupResponse(BaseModel):
    group_code: str
    total_units: int
