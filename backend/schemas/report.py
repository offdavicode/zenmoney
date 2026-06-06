from decimal import Decimal

from pydantic import BaseModel

from utils.emotion_rules import EmotionType


class EmotionReportItem(BaseModel):
    emotion: EmotionType
    label: str
    transaction_count: int
    total_amount: Decimal
    percentage: float


class SummaryReport(BaseModel):
    transaction_count: int
    income_count: int
    expense_count: int
    total_income: Decimal
    total_expense: Decimal
    balance: Decimal
    average_expense: Decimal
    essential_expense: Decimal
    essential_expense_percentage: float
    non_essential_expense: Decimal
    non_essential_expense_percentage: float
    uncategorized_expense: Decimal


class CategoryReportItem(BaseModel):
    category_id: int | None
    category_name: str
    is_default: bool
    is_essential: bool
    transaction_count: int
    total_amount: Decimal
    percentage: float


class SpendingTriggerReportItem(BaseModel):
    emotion: EmotionType
    emotion_label: str
    category_id: int | None
    category_name: str
    transaction_count: int
    total_amount: Decimal
    average_amount: Decimal
    percentage: float
