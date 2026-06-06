from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


class CategoryBudgetLimitUpdate(BaseModel):
    category_id: int
    amount: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)


class BudgetSettingsUpdate(BaseModel):
    global_limit: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    category_limits: list[CategoryBudgetLimitUpdate] = Field(default_factory=list)


class BudgetLimitStatus(BaseModel):
    category_id: int | None
    category_name: str
    limit_amount: Decimal
    spent_amount: Decimal
    remaining_amount: Decimal
    usage_percentage: float
    is_exceeded: bool


class BudgetSettingsResponse(BaseModel):
    month: str
    global_limit: BudgetLimitStatus | None
    category_limits: list[BudgetLimitStatus]
    alerts_enabled: bool


class BudgetAlertResponse(BaseModel):
    month: str
    scope: Literal["global", "category"]
    category_id: int | None
    category_name: str
    threshold_percent: int
    limit_amount: Decimal
    spent_amount: Decimal
    usage_percentage: float
    message: str


class BudgetAlertCheckResponse(BaseModel):
    month: str
    alert: BudgetAlertResponse | None
