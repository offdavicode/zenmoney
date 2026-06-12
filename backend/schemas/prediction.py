from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel


PredictionConfidence = Literal["insufficient", "low", "medium", "high"]


class PredictionHistoryMonth(BaseModel):
    month: str
    variable_expense: Decimal
    days_in_month: int


class BalancePredictionResponse(BaseModel):
    month: str
    calculated_on: date
    days_remaining: int
    current_income: Decimal
    current_expense: Decimal
    current_month_balance: Decimal
    expected_future_recurring_income: Decimal
    expected_future_recurring_expense: Decimal
    historical_daily_variable_expense_average: Decimal
    expected_remaining_variable_expense: Decimal
    predicted_end_balance: Decimal
    history_months_used: list[PredictionHistoryMonth]
    confidence_level: PredictionConfidence
