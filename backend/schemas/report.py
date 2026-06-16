from datetime import date
from decimal import Decimal

from pydantic import BaseModel

from utils.emotion_rules import EmotionType


class EmotionReportItem(BaseModel):
    emotion: EmotionType
    label: str
    transaction_count: int
    total_amount: Decimal
    average_amount: Decimal
    percentage: float
    insight_eligible: bool


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


class ReportPeriod(BaseModel):
    start_date: date | None
    end_date: date | None
    category_id: int | None


class VisualReportItem(BaseModel):
    key: str
    label: str
    transaction_count: int
    total_amount: Decimal
    percentage: float
    is_aggregated: bool = False
    insight_eligible: bool = False


class VisualReportSection(BaseModel):
    pie_items: list[VisualReportItem]
    bar_items: list[VisualReportItem]
    textual_items: list[VisualReportItem]


class VisualReportResponse(BaseModel):
    period: ReportPeriod
    total_expense: Decimal
    category_distribution: VisualReportSection
    emotion_distribution: VisualReportSection
