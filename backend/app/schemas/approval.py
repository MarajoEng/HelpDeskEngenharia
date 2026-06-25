from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.enums import ApprovalStatus, UserRole
from app.schemas.pagination import PageParams, PaginatedResponse

_APPROVER_ROLES = {UserRole.ADMIN, UserRole.ENGINEERING, UserRole.DIRECTOR}


class ApprovalLevelCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    min_amount: Decimal = Field(ge=0, decimal_places=2)
    max_amount: Decimal | None = Field(default=None, ge=0, decimal_places=2)
    allowed_roles: list[UserRole]
    is_active: bool = True

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Name is required.")
        return normalized

    @field_validator("allowed_roles")
    @classmethod
    def validate_allowed_roles(cls, value: list[UserRole]) -> list[UserRole]:
        if not value:
            raise ValueError("Allowed roles cannot be empty.")
        if any(role not in _APPROVER_ROLES for role in value):
            raise ValueError("Allowed roles must contain only approver roles.")
        return list(dict.fromkeys(value))

    @model_validator(mode="after")
    def validate_range(self) -> "ApprovalLevelCreate":
        if self.max_amount is not None and self.max_amount < self.min_amount:
            raise ValueError("max_amount must be greater than or equal to min_amount.")
        return self


class ApprovalLevelUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    min_amount: Decimal | None = Field(default=None, ge=0, decimal_places=2)
    max_amount: Decimal | None = Field(default=None, ge=0, decimal_places=2)
    allowed_roles: list[UserRole] | None = None
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

    @field_validator("allowed_roles")
    @classmethod
    def validate_optional_allowed_roles(cls, value: list[UserRole] | None) -> list[UserRole] | None:
        if value is None:
            return value
        if not value:
            raise ValueError("Allowed roles cannot be empty.")
        if any(role not in _APPROVER_ROLES for role in value):
            raise ValueError("Allowed roles must contain only approver roles.")
        return list(dict.fromkeys(value))


class ApprovalLevelResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    min_amount: Decimal
    max_amount: Decimal | None
    allowed_roles: list[UserRole]
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ApprovalLevelListResponse(PaginatedResponse[ApprovalLevelResponse]):
    pass


class ApprovalLevelListParams(PageParams):
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


class ApprovalRequestCreate(BaseModel):
    amount_requested: Decimal = Field(gt=0, decimal_places=2)
    justification: str = Field(min_length=1)

    @field_validator("justification")
    @classmethod
    def normalize_request_justification(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Justification is required.")
        return normalized


class ApprovalDecisionRequest(BaseModel):
    decision: Literal["approved", "rejected"]
    amount_approved: Decimal | None = Field(default=None, ge=0, decimal_places=2)
    justification: str = Field(min_length=1)

    @field_validator("justification")
    @classmethod
    def normalize_decision_justification(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Justification is required.")
        return normalized


class ApprovalResponse(BaseModel):
    id: int
    ticket_id: int
    requested_by_user_id: int
    requested_by_user_name: str | None
    approved_by_user_id: int | None
    approved_by_user_name: str | None
    approval_level_id: int | None
    approval_level_name: str | None
    approval_allowed_roles: list[UserRole]
    status: ApprovalStatus
    amount_requested: Decimal
    amount_approved: Decimal | None
    justification: str
    approved_at: datetime | None
    created_at: datetime
