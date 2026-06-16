from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


class SurvivalSettingUpdate(BaseModel):
    activation_percentage: int = Field(ge=50, le=90)


class SurvivalSettingResponse(BaseModel):
    activation_percentage: int
    is_default: bool


class SurvivalTrigger(BaseModel):
    scope: Literal["global", "category"]
    category_id: int | None
    category_name: str
    limit_amount: Decimal
    spent_amount: Decimal
    usage_percentage: float


class SurvivalRecommendation(BaseModel):
    category_id: int
    category_name: str
    spent_amount: Decimal
    limit_amount: Decimal | None
    exceeded_amount: Decimal
    usage_percentage: float | None
    suggest_block_new_transactions: bool = True
    message: str


class SurvivalModeResponse(BaseModel):
    month: str
    activation_percentage: int
    is_active: bool
    activation_reason: Literal["no_limits", "below_threshold", "global_limit", "category_limit"]
    trigger: SurvivalTrigger | None
    recommendations: list[SurvivalRecommendation]
    highlighted_transaction_ids: list[int]
