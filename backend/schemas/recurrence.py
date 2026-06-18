from datetime import date as date_type
from decimal import Decimal
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    computed_field,
    field_validator,
    model_validator,
)

from schemas.transaction import TransactionResponse
from utils.category_rules import CategoryType
from utils.date_utils import now_in_brasilia
from utils.emotion_rules import (
    EmotionType,
    SelectableEmotionType,
    normalize_required_emotion,
)
from utils.recurrence_dates import first_scheduled_on_or_after


RecurrenceFrequency = Literal["monthly"]
RecurrenceStatus = Literal["active", "paused", "completed"]


class RecurrenceCreate(BaseModel):
    category_id: int | None = None
    type: CategoryType
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    description: str | None = Field(default=None, max_length=256)
    emotion: SelectableEmotionType
    frequency: RecurrenceFrequency = "monthly"
    day_of_month: int | None = Field(default=None, ge=1, le=31)
    start_date: date_type
    end_date: date_type | None = None

    @field_validator("emotion", mode="before")
    @classmethod
    def normalize_emotion_value(cls, value: str | None) -> SelectableEmotionType:
        return normalize_required_emotion(value)

    @model_validator(mode="after")
    def validate_date_range(self):
        if self.end_date is not None and self.end_date < self.start_date:
            raise ValueError("End date must be on or after start date.")
        return self


class RecurrenceUpdate(BaseModel):
    category_id: int | None = None
    type: CategoryType | None = None
    amount: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    description: str | None = Field(default=None, max_length=256)
    emotion: SelectableEmotionType | None = None
    frequency: RecurrenceFrequency | None = None
    day_of_month: int | None = Field(default=None, ge=1, le=31)
    start_date: date_type | None = None
    end_date: date_type | None = None

    @field_validator("emotion", mode="before")
    @classmethod
    def normalize_emotion_value(cls, value: str | None) -> SelectableEmotionType | None:
        if value is None:
            raise ValueError("Emotion cannot be null.")
        return normalize_required_emotion(value)

    @model_validator(mode="after")
    def reject_null_required_fields(self):
        for field_name in ("type", "amount", "frequency", "start_date"):
            if field_name in self.model_fields_set and getattr(self, field_name) is None:
                raise ValueError(f"{field_name} cannot be null.")
        return self


class RecurrenceResponse(BaseModel):
    id: int
    user_id: int
    category_id: int | None = None
    type: CategoryType
    amount: Decimal
    description: str | None = None
    emotion: EmotionType
    frequency: RecurrenceFrequency
    day_of_month: int
    start_date: date_type
    end_date: date_type | None = None
    next_run_date: date_type
    is_active: bool

    model_config = ConfigDict(from_attributes=True)

    @computed_field
    @property
    def status(self) -> RecurrenceStatus:
        if self.is_active:
            return "active"
        if self.end_date is not None:
            reference_date = max(self.start_date, now_in_brasilia().date())
            next_possible_date = first_scheduled_on_or_after(
                reference_date,
                self.day_of_month,
            )
            if self.next_run_date > self.end_date or next_possible_date > self.end_date:
                return "completed"
        return "paused"


class RecurrenceRunDueRequest(BaseModel):
    through_date: date_type | None = None


class RecurrenceRunDueResponse(BaseModel):
    through_date: date_type
    generated_count: int
    generated_transactions: list[TransactionResponse]
