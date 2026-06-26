from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.pagination import PageParams, PaginatedResponse


class TicketConfigurationPageParams(PageParams):
    search: str | None = None
    is_active: bool | None = None
    sort: Literal["display_order_asc", "created_at_desc", "name_asc"] = "display_order_asc"

    @field_validator("search")
    @classmethod
    def strip_search(cls, value: str | None) -> str | None:
        if value is None:
            return value
        normalized = value.strip()
        return normalized or None


class TicketSubcategoryListParams(TicketConfigurationPageParams):
    category_id: int | None = None


class TicketCustomFieldListParams(TicketConfigurationPageParams):
    category_id: int | None = None
    subcategory_id: int | None = None


class TicketStatusTransitionListParams(PageParams):
    from_status_id: int | None = Field(default=None, ge=1)
    is_active: bool | None = None


CustomFieldType = Literal["text", "textarea", "number", "boolean", "select", "date"]


class TicketCustomFieldOption(BaseModel):
    label: str = Field(min_length=1, max_length=255)
    value: str = Field(min_length=1, max_length=255)
    display_order: int = Field(default=0, ge=0)
    is_active: bool = True

    @field_validator("label", "value")
    @classmethod
    def strip_option_text(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Field cannot be empty.")
        return normalized


class TicketCustomFieldBase(BaseModel):
    category_id: int = Field(ge=1)
    subcategory_id: int | None = Field(default=None, ge=1)
    name: str = Field(min_length=1, max_length=100)
    label: str = Field(min_length=1, max_length=255)
    description: str | None = None
    field_type: CustomFieldType
    is_required: bool = False
    is_active: bool = True
    display_order: int = Field(default=0, ge=0)
    placeholder: str | None = None
    help_text: str | None = None
    validation_json: dict[str, Any] | None = None
    options: list[TicketCustomFieldOption] = Field(default_factory=list)

    @field_validator("name", "label")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Field cannot be empty.")
        return normalized

    @field_validator("description", "placeholder", "help_text")
    @classmethod
    def strip_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return value
        normalized = value.strip()
        return normalized or None


class TicketCustomFieldCreate(TicketCustomFieldBase):
    pass


class TicketCustomFieldUpdate(BaseModel):
    category_id: int | None = Field(default=None, ge=1)
    subcategory_id: int | None = Field(default=None, ge=1)
    name: str | None = Field(default=None, min_length=1, max_length=100)
    label: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    field_type: CustomFieldType | None = None
    is_required: bool | None = None
    is_active: bool | None = None
    display_order: int | None = Field(default=None, ge=0)
    placeholder: str | None = None
    help_text: str | None = None
    validation_json: dict[str, Any] | None = None
    options: list[TicketCustomFieldOption] | None = None

    @field_validator("name", "label")
    @classmethod
    def strip_optional_required_text(cls, value: str | None) -> str | None:
        if value is None:
            return value
        normalized = value.strip()
        if not normalized:
            raise ValueError("Field cannot be empty.")
        return normalized

    @field_validator("description", "placeholder", "help_text")
    @classmethod
    def strip_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return value
        normalized = value.strip()
        return normalized or None


class TicketCustomFieldResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    category_id: int
    category_name: str
    subcategory_id: int | None = None
    subcategory_name: str | None = None
    name: str
    label: str
    description: str | None
    field_type: CustomFieldType
    is_required: bool
    is_active: bool
    display_order: int
    placeholder: str | None
    help_text: str | None
    validation_json: dict[str, Any] | None = None
    options: list[TicketCustomFieldOption] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class TicketCustomFieldListResponse(PaginatedResponse[TicketCustomFieldResponse]):
    pass


class TicketFormSchemaResponse(BaseModel):
    category_id: int
    subcategory_id: int | None = None
    fields: list[TicketCustomFieldResponse]


class TicketCategoryBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    is_active: bool = True
    display_order: int = Field(default=0, ge=0)
    requires_attachment: bool = False
    requires_location: bool = False
    type_ids: list[int] = Field(default_factory=list)

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Field cannot be empty.")
        return normalized

    @field_validator("description")
    @classmethod
    def strip_description(cls, value: str | None) -> str | None:
        if value is None:
            return value
        normalized = value.strip()
        return normalized or None

    @field_validator("type_ids")
    @classmethod
    def deduplicate_type_ids(cls, value: list[int]) -> list[int]:
        seen: list[int] = []
        for item in value:
            if item not in seen:
                seen.append(item)
        return seen


class TicketCategoryCreate(TicketCategoryBase):
    pass


class TicketCategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    is_active: bool | None = None
    display_order: int | None = Field(default=None, ge=0)
    requires_attachment: bool | None = None
    requires_location: bool | None = None
    type_ids: list[int] | None = None

    @field_validator("name")
    @classmethod
    def strip_optional_name(cls, value: str | None) -> str | None:
        if value is None:
            return value
        normalized = value.strip()
        if not normalized:
            raise ValueError("Field cannot be empty.")
        return normalized

    @field_validator("description")
    @classmethod
    def strip_optional_description(cls, value: str | None) -> str | None:
        if value is None:
            return value
        normalized = value.strip()
        return normalized or None

    @field_validator("type_ids")
    @classmethod
    def deduplicate_optional_type_ids(cls, value: list[int] | None) -> list[int] | None:
        if value is None:
            return value
        seen: list[int] = []
        for item in value:
            if item not in seen:
                seen.append(item)
        return seen


class TicketCategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    legacy_value: str | None = None
    description: str | None
    is_active: bool
    display_order: int
    requires_attachment: bool
    requires_location: bool
    type_ids: list[int] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class TicketCategoryListResponse(PaginatedResponse[TicketCategoryResponse]):
    pass


class TicketSubcategoryBase(BaseModel):
    category_id: int
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    is_active: bool = True
    display_order: int = Field(default=0, ge=0)

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Field cannot be empty.")
        return normalized

    @field_validator("description")
    @classmethod
    def strip_description(cls, value: str | None) -> str | None:
        if value is None:
            return value
        normalized = value.strip()
        return normalized or None


class TicketSubcategoryCreate(TicketSubcategoryBase):
    pass


class TicketSubcategoryUpdate(BaseModel):
    category_id: int | None = None
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    is_active: bool | None = None
    display_order: int | None = Field(default=None, ge=0)

    @field_validator("name")
    @classmethod
    def strip_optional_name(cls, value: str | None) -> str | None:
        if value is None:
            return value
        normalized = value.strip()
        if not normalized:
            raise ValueError("Field cannot be empty.")
        return normalized

    @field_validator("description")
    @classmethod
    def strip_optional_description(cls, value: str | None) -> str | None:
        if value is None:
            return value
        normalized = value.strip()
        return normalized or None


class TicketSubcategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    category_id: int
    category_name: str
    name: str
    description: str | None
    is_active: bool
    display_order: int
    created_at: datetime
    updated_at: datetime


class TicketSubcategoryListResponse(PaginatedResponse[TicketSubcategoryResponse]):
    pass


class TicketTypeBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    is_active: bool = True
    display_order: int = Field(default=0, ge=0)

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Field cannot be empty.")
        return normalized

    @field_validator("description")
    @classmethod
    def strip_description(cls, value: str | None) -> str | None:
        if value is None:
            return value
        normalized = value.strip()
        return normalized or None


class TicketTypeCreate(TicketTypeBase):
    pass


class TicketTypeUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    is_active: bool | None = None
    display_order: int | None = Field(default=None, ge=0)

    @field_validator("name")
    @classmethod
    def strip_optional_name(cls, value: str | None) -> str | None:
        if value is None:
            return value
        normalized = value.strip()
        if not normalized:
            raise ValueError("Field cannot be empty.")
        return normalized

    @field_validator("description")
    @classmethod
    def strip_optional_description(cls, value: str | None) -> str | None:
        if value is None:
            return value
        normalized = value.strip()
        return normalized or None


class TicketTypeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    is_active: bool
    display_order: int
    created_at: datetime
    updated_at: datetime


class TicketTypeListResponse(PaginatedResponse[TicketTypeResponse]):
    pass


class TicketPriorityBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    color: str = Field(min_length=1, max_length=32)
    weight: int = Field(ge=0)
    sla_hours: int = Field(ge=1)
    requires_reason: bool = False
    is_active: bool = True
    display_order: int = Field(default=0, ge=0)

    @field_validator("name", "color")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Field cannot be empty.")
        return normalized

    @field_validator("description")
    @classmethod
    def strip_description(cls, value: str | None) -> str | None:
        if value is None:
            return value
        normalized = value.strip()
        return normalized or None


class TicketPriorityCreate(TicketPriorityBase):
    pass


class TicketPriorityUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    color: str | None = Field(default=None, min_length=1, max_length=32)
    weight: int | None = Field(default=None, ge=0)
    sla_hours: int | None = Field(default=None, ge=1)
    requires_reason: bool | None = None
    is_active: bool | None = None
    display_order: int | None = Field(default=None, ge=0)

    @field_validator("name", "color")
    @classmethod
    def strip_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return value
        normalized = value.strip()
        if not normalized:
            raise ValueError("Field cannot be empty.")
        return normalized

    @field_validator("description")
    @classmethod
    def strip_optional_description(cls, value: str | None) -> str | None:
        if value is None:
            return value
        normalized = value.strip()
        return normalized or None


class TicketPriorityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    legacy_value: str | None = None
    description: str | None
    color: str
    weight: int
    sla_hours: int
    requires_reason: bool
    is_active: bool
    display_order: int
    created_at: datetime
    updated_at: datetime


class TicketPriorityListResponse(PaginatedResponse[TicketPriorityResponse]):
    pass


class TicketStatusBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    legacy_value: str | None = Field(default=None, max_length=50)
    description: str | None = None
    color: str = Field(min_length=1, max_length=32)
    is_initial: bool = False
    is_final: bool = False
    pauses_sla: bool = False
    allows_reopen: bool = False
    is_active: bool = True
    display_order: int = Field(default=0, ge=0)

    @field_validator("name", "color")
    @classmethod
    def strip_required_status_text(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Field cannot be empty.")
        return normalized

    @field_validator("legacy_value", "description")
    @classmethod
    def strip_optional_status_text(cls, value: str | None) -> str | None:
        if value is None:
            return value
        normalized = value.strip()
        return normalized or None


class TicketStatusCreate(TicketStatusBase):
    pass


class TicketStatusUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    legacy_value: str | None = Field(default=None, max_length=50)
    description: str | None = None
    color: str | None = Field(default=None, min_length=1, max_length=32)
    is_initial: bool | None = None
    is_final: bool | None = None
    pauses_sla: bool | None = None
    allows_reopen: bool | None = None
    is_active: bool | None = None
    display_order: int | None = Field(default=None, ge=0)

    @field_validator("name", "color")
    @classmethod
    def strip_optional_required_status_text(cls, value: str | None) -> str | None:
        if value is None:
            return value
        normalized = value.strip()
        if not normalized:
            raise ValueError("Field cannot be empty.")
        return normalized

    @field_validator("legacy_value", "description")
    @classmethod
    def strip_optional_status_text(cls, value: str | None) -> str | None:
        if value is None:
            return value
        normalized = value.strip()
        return normalized or None


class TicketStatusResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    legacy_value: str | None = None
    description: str | None
    color: str
    is_initial: bool
    is_final: bool
    pauses_sla: bool
    allows_reopen: bool
    is_active: bool
    display_order: int
    created_at: datetime
    updated_at: datetime


class TicketStatusListResponse(PaginatedResponse[TicketStatusResponse]):
    pass


class TicketStatusTransitionBase(BaseModel):
    from_status_id: int = Field(ge=1)
    to_status_id: int = Field(ge=1)
    requires_comment: bool = False
    requires_attachment: bool = False
    allowed_roles_json: list[str] | None = None
    is_active: bool = True

    @field_validator("allowed_roles_json")
    @classmethod
    def normalize_allowed_roles(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return value
        normalized: list[str] = []
        for item in value:
            role = item.strip().lower()
            if role and role not in normalized:
                normalized.append(role)
        return normalized or None


class TicketStatusTransitionCreate(TicketStatusTransitionBase):
    pass


class TicketStatusTransitionUpdate(BaseModel):
    from_status_id: int | None = Field(default=None, ge=1)
    to_status_id: int | None = Field(default=None, ge=1)
    requires_comment: bool | None = None
    requires_attachment: bool | None = None
    allowed_roles_json: list[str] | None = None
    is_active: bool | None = None

    @field_validator("allowed_roles_json")
    @classmethod
    def normalize_allowed_roles(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return value
        normalized: list[str] = []
        for item in value:
            role = item.strip().lower()
            if role and role not in normalized:
                normalized.append(role)
        return normalized or None


class TicketStatusTransitionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    from_status_id: int
    from_status_name: str
    to_status_id: int
    to_status_name: str
    to_status_color: str
    requires_comment: bool
    requires_attachment: bool
    allowed_roles_json: list[str] | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class TicketStatusTransitionListResponse(PaginatedResponse[TicketStatusTransitionResponse]):
    pass
