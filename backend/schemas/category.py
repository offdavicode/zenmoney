from pydantic import BaseModel, ConfigDict, Field, field_validator

from utils.category_rules import CategoryType, normalize_category_name


class CategoryCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=100)
    type: CategoryType
    is_essential: bool = False

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        normalized = normalize_category_name(value)
        if not normalized:
            raise ValueError("Category name cannot be blank.")
        return normalized


class CategoryUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=100)
    is_essential: bool | None = None

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str | None) -> str | None:
        if value is None:
            return value

        normalized = normalize_category_name(value)
        if not normalized:
            raise ValueError("Category name cannot be blank.")
        return normalized


class CategoryResponse(BaseModel):
    id: int
    name: str
    type: CategoryType
    is_default: bool
    is_essential: bool

    model_config = ConfigDict(from_attributes=True)
