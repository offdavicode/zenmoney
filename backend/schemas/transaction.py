from datetime import date as date_type
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class TransactionCreate(BaseModel):
    category_id: int | None = None
    type: str = Field(pattern="^(income|expense)$")
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    date: date_type
    description: str | None = Field(default=None, max_length=256)
    emotion: str = Field(default="not_specified", max_length=50)


class TransactionUpdate(BaseModel):
    category_id: int | None = None
    type: str | None = Field(default=None, pattern="^(income|expense)$")
    amount: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    date: date_type | None = None
    description: str | None = Field(default=None, max_length=256)
    emotion: str | None = Field(default=None, max_length=50)


class TransactionResponse(BaseModel):
    id: int
    user_id: int
    category_id: int | None = None
    recurrence_id: int | None = None
    type: str
    amount: Decimal
    date: date_type
    description: str | None = None
    emotion: str

    model_config = ConfigDict(from_attributes=True)
