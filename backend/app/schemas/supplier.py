from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.pagination import PageParams, PaginatedResponse


class SupplierCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    document: str = Field(min_length=1, max_length=50)
    phone: str = Field(min_length=1, max_length=50)
    email: str = Field(min_length=1, max_length=255)
    specialty: str = Field(min_length=1, max_length=255)
    is_active: bool = True

    @field_validator("name", "document", "phone", "email", "specialty")
    @classmethod
    def strip_text(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Field cannot be empty.")
        return normalized


class SupplierUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    document: str | None = Field(default=None, min_length=1, max_length=50)
    phone: str | None = Field(default=None, min_length=1, max_length=50)
    email: str | None = Field(default=None, min_length=1, max_length=255)
    specialty: str | None = Field(default=None, min_length=1, max_length=255)
    is_active: bool | None = None

    @field_validator("name", "document", "phone", "email", "specialty")
    @classmethod
    def strip_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return value
        normalized = value.strip()
        if not normalized:
            raise ValueError("Field cannot be empty.")
        return normalized


class SupplierResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    document: str
    phone: str
    email: str
    specialty: str
    is_active: bool
    created_at: datetime


class SupplierListResponse(PaginatedResponse[SupplierResponse]):
    pass


class SupplierListParams(PageParams):
    search: str | None = None
    is_active: bool | None = None
    sort: Literal["name_asc", "created_at_desc"] = "name_asc"

    @field_validator("search")
    @classmethod
    def strip_search(cls, value: str | None) -> str | None:
        if value is None:
            return value
        normalized = value.strip()
        return normalized or None
