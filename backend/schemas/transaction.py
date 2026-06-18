from datetime import date as date_type
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from utils.category_rules import CategoryType
from utils.emotion_rules import (
    EmotionType,
    SelectableEmotionType,
    normalize_required_emotion,
)


class TransactionCreate(BaseModel):
    category_id: int | None = None
    type: CategoryType
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    date: date_type
    description: str | None = Field(default=None, max_length=256)
    emotion: SelectableEmotionType

    @field_validator("emotion", mode="before")
    @classmethod
    def normalize_emotion_value(cls, value: str | None) -> SelectableEmotionType:
        return normalize_required_emotion(value)


class TransactionUpdate(BaseModel):
    category_id: int | None = None
    type: CategoryType | None = None
    amount: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    date: date_type | None = None
    description: str | None = Field(default=None, max_length=256)
    emotion: SelectableEmotionType | None = None

    @field_validator("emotion", mode="before")
    @classmethod
    def normalize_emotion_value(cls, value: str | None) -> SelectableEmotionType | None:
        if value is None:
            raise ValueError("Emotion cannot be null.")
        return normalize_required_emotion(value)


class TransactionResponse(BaseModel):
    id: int
    user_id: int
    category_id: int | None = None
    recurrence_id: int | None = None
    is_recurring: bool
    type: CategoryType
    amount: Decimal
    date: date_type
    registered_at: datetime
    description: str | None = None
    emotion: EmotionType

    model_config = ConfigDict(from_attributes=True)
