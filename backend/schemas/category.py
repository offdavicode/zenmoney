from pydantic import BaseModel, ConfigDict, Field


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    type: str = Field(pattern="^(income|expense)$")
    parent_id: int | None = None
    is_essential: bool = False


class CategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    parent_id: int | None = None
    is_essential: bool | None = None


class CategoryResponse(BaseModel):
    id: int
    name: str
    type: str
    is_default: bool
    is_essential: bool
    parent_id: int | None = None

    model_config = ConfigDict(from_attributes=True)

