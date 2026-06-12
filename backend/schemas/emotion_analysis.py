from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel

from schemas.report import ReportPeriod, SpendingTriggerReportItem
from utils.emotion_rules import EmotionType


EmotionRole = Literal["reference", "candidate", "not_informed"]
AnalysisReason = Literal[
    "trigger",
    "not_trigger",
    "period_not_single_month",
    "insufficient_candidate_data",
    "insufficient_reference_data",
    "not_candidate",
]


class ReferenceStatistics(BaseModel):
    transaction_count: int
    total_amount: Decimal
    average_amount: Decimal


class EmotionTriggerAnalysis(BaseModel):
    emotion: EmotionType
    emotion_label: str
    role: EmotionRole
    transaction_count: int
    total_amount: Decimal
    average_amount: Decimal
    reference_transaction_count: int
    reference_average_amount: Decimal
    difference_percentage: float | None
    overall_average_amount: Decimal
    difference_from_overall_percentage: float | None
    sufficient_data: bool
    is_trigger: bool
    reason: AnalysisReason


class CategoryTriggerAnalysis(BaseModel):
    emotion: EmotionType
    emotion_label: str
    category_id: int | None
    category_name: str
    transaction_count: int
    average_amount: Decimal
    reference_transaction_count: int
    reference_average_amount: Decimal
    difference_percentage: float | None
    sufficient_data: bool
    is_trigger: bool
    reason: AnalysisReason


class EmotionTopCategory(BaseModel):
    category_id: int | None
    category_name: str
    transaction_count: int
    total_amount: Decimal
    average_amount: Decimal


class EmotionTopTransaction(BaseModel):
    transaction_id: int
    date: date
    description: str | None
    category_id: int | None
    category_name: str
    amount: Decimal


class EmotionSpendingDetail(BaseModel):
    emotion: EmotionType
    emotion_label: str
    top_categories: list[EmotionTopCategory]
    top_transactions: list[EmotionTopTransaction]


class EmotionSpendingAnalysisResponse(BaseModel):
    period: ReportPeriod
    conclusions_enabled: bool
    minimum_transactions: int
    trigger_threshold_percentage: int
    reference_emotions: list[EmotionType]
    candidate_emotions: list[EmotionType]
    overall_statistics: ReferenceStatistics
    reference_statistics: ReferenceStatistics
    emotion_analysis: list[EmotionTriggerAnalysis]
    category_distribution: list[SpendingTriggerReportItem]
    category_triggers: list[CategoryTriggerAnalysis]
    details_by_emotion: list[EmotionSpendingDetail]
