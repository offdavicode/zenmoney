from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from models.category import Category
from models.transaction import Transaction
from models.user import User
from schemas.emotion_analysis import (
    CategoryTriggerAnalysis,
    EmotionSpendingAnalysisResponse,
    EmotionSpendingDetail,
    EmotionTopCategory,
    EmotionTopTransaction,
    EmotionTriggerAnalysis,
    ReferenceStatistics,
)
from schemas.report import ReportPeriod, SpendingTriggerReportItem
from services.report_service import ReportService, ReportServiceError, UNCATEGORIZED_CATEGORY_NAME
from utils.emotion_rules import DEFAULT_EMOTION, EMOTION_LABELS, EmotionType, VALID_EMOTIONS
from utils.month_utils import parse_month_label


REFERENCE_EMOTIONS: tuple[EmotionType, ...] = (
    "calma",
    "felicidade",
    "indiferenca",
    "satisfacao",
)
CANDIDATE_EMOTIONS: tuple[EmotionType, ...] = (
    "raiva",
    "frustracao",
    "empolgacao",
    "ansiedade",
    "estresse",
    "tedio",
)
MINIMUM_TRANSACTIONS = 5
TRIGGER_THRESHOLD_PERCENTAGE = 20
TOP_ITEMS_LIMIT = 10
CENTS = Decimal("0.01")


class EmotionAnalysisService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_analysis(
        self,
        current_user: User,
        month: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        category_id: int | None = None,
    ) -> EmotionSpendingAnalysisResponse:
        resolved_start, resolved_end = self._resolve_period(month, start_date, end_date)
        if category_id is not None:
            self._resolve_expense_category(current_user, category_id)

        conditions = self._expense_conditions(
            current_user,
            resolved_start,
            resolved_end,
            category_id,
        )
        conclusions_enabled = self._is_single_month_period(resolved_start, resolved_end)
        category_names = self._get_category_names(current_user)
        emotion_totals = self._get_emotion_totals(conditions)
        overall_statistics = self._build_statistics(
            emotion_totals,
            tuple(emotion for emotion in VALID_EMOTIONS if emotion != DEFAULT_EMOTION),
        )
        reference_statistics = self._build_reference_statistics(emotion_totals)
        category_distribution = ReportService(self.db).get_spending_triggers(
            current_user,
            month,
            start_date,
            end_date,
            category_id,
        )
        category_distribution = [
            item.model_copy(update={"emotion_label": "Nao Informado"})
            if item.emotion == DEFAULT_EMOTION
            else item
            for item in category_distribution
        ]

        return EmotionSpendingAnalysisResponse(
            period=ReportPeriod(
                start_date=resolved_start,
                end_date=resolved_end,
                category_id=category_id,
            ),
            conclusions_enabled=conclusions_enabled,
            minimum_transactions=MINIMUM_TRANSACTIONS,
            trigger_threshold_percentage=TRIGGER_THRESHOLD_PERCENTAGE,
            reference_emotions=list(REFERENCE_EMOTIONS),
            candidate_emotions=list(CANDIDATE_EMOTIONS),
            overall_statistics=overall_statistics,
            reference_statistics=reference_statistics,
            emotion_analysis=self._build_emotion_analysis(
                emotion_totals,
                overall_statistics,
                reference_statistics,
                conclusions_enabled,
            ),
            category_distribution=category_distribution,
            category_triggers=self._build_category_triggers(
                category_distribution,
                conclusions_enabled,
            ),
            details_by_emotion=self._build_emotion_details(
                conditions,
                category_names,
                emotion_totals,
            ),
        )

    def _get_emotion_totals(self, conditions: list) -> dict[str, tuple[int, Decimal]]:
        statement = (
            select(
                Transaction.emotion,
                func.count(Transaction.id).label("transaction_count"),
                func.coalesce(func.sum(Transaction.amount), 0).label("total_amount"),
            )
            .where(*conditions)
            .group_by(Transaction.emotion)
        )
        totals = {
            emotion: (0, Decimal("0.00"))
            for emotion in VALID_EMOTIONS
        }
        for row in self.db.execute(statement):
            emotion = row.emotion if row.emotion in VALID_EMOTIONS else DEFAULT_EMOTION
            previous_count, previous_total = totals[emotion]
            totals[emotion] = (
                previous_count + row.transaction_count,
                previous_total + (row.total_amount or Decimal("0.00")),
            )
        return totals

    @staticmethod
    def _build_reference_statistics(
        emotion_totals: dict[str, tuple[int, Decimal]],
    ) -> ReferenceStatistics:
        return EmotionAnalysisService._build_statistics(
            emotion_totals,
            REFERENCE_EMOTIONS,
        )

    @staticmethod
    def _build_statistics(
        emotion_totals: dict[str, tuple[int, Decimal]],
        emotions: tuple[EmotionType, ...],
    ) -> ReferenceStatistics:
        transaction_count = sum(emotion_totals[emotion][0] for emotion in emotions)
        total_amount = sum(
            (emotion_totals[emotion][1] for emotion in emotions),
            Decimal("0.00"),
        )
        average_amount = Decimal("0.00")
        if transaction_count > 0:
            average_amount = (total_amount / transaction_count).quantize(CENTS)
        return ReferenceStatistics(
            transaction_count=transaction_count,
            total_amount=total_amount,
            average_amount=average_amount,
        )

    def _build_emotion_analysis(
        self,
        emotion_totals: dict[str, tuple[int, Decimal]],
        overall: ReferenceStatistics,
        reference: ReferenceStatistics,
        conclusions_enabled: bool,
    ) -> list[EmotionTriggerAnalysis]:
        items: list[EmotionTriggerAnalysis] = []
        for emotion in VALID_EMOTIONS:
            transaction_count, total_amount = emotion_totals[emotion]
            average_amount = self._average(total_amount, transaction_count)
            role = self._emotion_role(emotion)
            sufficient_data, is_trigger, reason = self._classify_trigger(
                role=role,
                conclusions_enabled=conclusions_enabled,
                candidate_count=transaction_count,
                candidate_total=total_amount,
                reference_count=reference.transaction_count,
                reference_total=reference.total_amount,
            )
            items.append(
                EmotionTriggerAnalysis(
                    emotion=emotion,
                    emotion_label=self._emotion_label(emotion),
                    role=role,
                    transaction_count=transaction_count,
                    total_amount=total_amount,
                    average_amount=average_amount,
                    reference_transaction_count=reference.transaction_count,
                    reference_average_amount=reference.average_amount,
                    difference_percentage=self._difference_percentage(
                        total_amount,
                        transaction_count,
                        reference.total_amount,
                        reference.transaction_count,
                    ),
                    overall_average_amount=overall.average_amount,
                    difference_from_overall_percentage=self._difference_percentage(
                        total_amount,
                        transaction_count,
                        overall.total_amount,
                        overall.transaction_count,
                    ),
                    sufficient_data=sufficient_data,
                    is_trigger=is_trigger,
                    reason=reason,
                )
            )
        return items

    def _build_category_triggers(
        self,
        distribution: list[SpendingTriggerReportItem],
        conclusions_enabled: bool,
    ) -> list[CategoryTriggerAnalysis]:
        grouped = {
            (item.emotion, item.category_id): item
            for item in distribution
        }
        category_keys = {
            (item.category_id, item.category_name)
            for item in distribution
        }
        results: list[CategoryTriggerAnalysis] = []

        for category_id, category_name in category_keys:
            reference_items = [
                grouped.get((emotion, category_id))
                for emotion in REFERENCE_EMOTIONS
            ]
            reference_count = sum(
                item.transaction_count for item in reference_items if item is not None
            )
            reference_total = sum(
                (item.total_amount for item in reference_items if item is not None),
                Decimal("0.00"),
            )
            reference_average = self._average(reference_total, reference_count)

            for emotion in CANDIDATE_EMOTIONS:
                candidate = grouped.get((emotion, category_id))
                if candidate is None:
                    continue
                sufficient_data, is_trigger, reason = self._classify_trigger(
                    role="candidate",
                    conclusions_enabled=conclusions_enabled,
                    candidate_count=candidate.transaction_count,
                    candidate_total=candidate.total_amount,
                    reference_count=reference_count,
                    reference_total=reference_total,
                )
                results.append(
                    CategoryTriggerAnalysis(
                        emotion=emotion,
                        emotion_label=EMOTION_LABELS[emotion],
                        category_id=category_id,
                        category_name=category_name,
                        transaction_count=candidate.transaction_count,
                        average_amount=candidate.average_amount,
                        reference_transaction_count=reference_count,
                        reference_average_amount=reference_average,
                        difference_percentage=self._difference_percentage(
                            candidate.total_amount,
                            candidate.transaction_count,
                            reference_total,
                            reference_count,
                        ),
                        sufficient_data=sufficient_data,
                        is_trigger=is_trigger,
                        reason=reason,
                    )
                )

        return sorted(
            results,
            key=lambda item: (
                not item.is_trigger,
                -(item.difference_percentage or 0),
                -item.average_amount,
                item.category_name,
                item.emotion,
            ),
        )

    def _build_emotion_details(
        self,
        conditions: list,
        category_names: dict[int, str],
        emotion_totals: dict[str, tuple[int, Decimal]],
    ) -> list[EmotionSpendingDetail]:
        details: list[EmotionSpendingDetail] = []
        for emotion in VALID_EMOTIONS:
            if emotion_totals[emotion][0] == 0:
                continue
            top_categories = self._get_top_categories(conditions, emotion, category_names)
            top_transactions = self._get_top_transactions(conditions, emotion, category_names)
            details.append(
                EmotionSpendingDetail(
                    emotion=emotion,
                    emotion_label=self._emotion_label(emotion),
                    top_categories=top_categories,
                    top_transactions=top_transactions,
                )
            )
        return details

    def _get_top_categories(
        self,
        conditions: list,
        emotion: EmotionType,
        category_names: dict[int, str],
    ) -> list[EmotionTopCategory]:
        statement = (
            select(
                Transaction.category_id,
                func.count(Transaction.id).label("transaction_count"),
                func.coalesce(func.sum(Transaction.amount), 0).label("total_amount"),
            )
            .where(*conditions, Transaction.emotion == emotion)
            .group_by(Transaction.category_id)
            .order_by(func.sum(Transaction.amount).desc(), func.count(Transaction.id).desc())
            .limit(TOP_ITEMS_LIMIT)
        )
        return [
            EmotionTopCategory(
                category_id=row.category_id,
                category_name=category_names.get(row.category_id, UNCATEGORIZED_CATEGORY_NAME),
                transaction_count=row.transaction_count,
                total_amount=row.total_amount or Decimal("0.00"),
                average_amount=self._average(
                    row.total_amount or Decimal("0.00"),
                    row.transaction_count,
                ),
            )
            for row in self.db.execute(statement)
        ]

    def _get_top_transactions(
        self,
        conditions: list,
        emotion: EmotionType,
        category_names: dict[int, str],
    ) -> list[EmotionTopTransaction]:
        statement = (
            select(Transaction)
            .where(*conditions, Transaction.emotion == emotion)
            .order_by(Transaction.amount.desc(), Transaction.date.desc(), Transaction.id.desc())
            .limit(TOP_ITEMS_LIMIT)
        )
        return [
            EmotionTopTransaction(
                transaction_id=transaction.id,
                date=transaction.date,
                description=transaction.description,
                category_id=transaction.category_id,
                category_name=category_names.get(
                    transaction.category_id,
                    UNCATEGORIZED_CATEGORY_NAME,
                ),
                amount=transaction.amount,
            )
            for transaction in self.db.scalars(statement)
        ]

    def _get_category_names(self, current_user: User) -> dict[int, str]:
        statement = select(Category.id, Category.name).where(
            Category.type == "expense",
            (Category.user_id == current_user.id) | (Category.user_id.is_(None)),
        )
        return {row.id: row.name for row in self.db.execute(statement)}

    def _resolve_expense_category(self, current_user: User, category_id: int) -> None:
        statement = select(Category.id).where(
            Category.id == category_id,
            Category.type == "expense",
            (Category.user_id == current_user.id) | (Category.user_id.is_(None)),
        )
        if self.db.scalar(statement) is None:
            raise ReportServiceError("Categoria de despesa não encontrada.", 404)

    @staticmethod
    def _resolve_period(
        month: str | None,
        start_date: date | None,
        end_date: date | None,
    ) -> tuple[date | None, date | None]:
        if month is not None and (start_date is not None or end_date is not None):
            raise ReportServiceError("Use o mês ou a data de início/fim, mas não ambos.", 400)
        if start_date is not None and end_date is not None and start_date > end_date:
            raise ReportServiceError("A data de início deve ser anterior ou igual à data de fim.", 400)
        if month is None:
            return start_date, end_date
        try:
            _, resolved_start, next_month_start = parse_month_label(month)
        except ValueError as exc:
            raise ReportServiceError(str(exc), 400) from exc
        return resolved_start, next_month_start - timedelta(days=1)

    @staticmethod
    def _expense_conditions(
        current_user: User,
        start_date: date | None,
        end_date: date | None,
        category_id: int | None,
    ) -> list:
        conditions = [
            Transaction.user_id == current_user.id,
            Transaction.type == "expense",
        ]
        if start_date is not None:
            conditions.append(Transaction.date >= start_date)
        if end_date is not None:
            conditions.append(Transaction.date <= end_date)
        if category_id is not None:
            conditions.append(Transaction.category_id == category_id)
        return conditions

    @staticmethod
    def _classify_trigger(
        role: str,
        conclusions_enabled: bool,
        candidate_count: int,
        candidate_total: Decimal,
        reference_count: int,
        reference_total: Decimal,
    ) -> tuple[bool, bool, str]:
        if role != "candidate":
            return False, False, "not_candidate"
        if not conclusions_enabled:
            return False, False, "period_not_single_month"
        if candidate_count < MINIMUM_TRANSACTIONS:
            return False, False, "insufficient_candidate_data"
        if reference_count < MINIMUM_TRANSACTIONS:
            return False, False, "insufficient_reference_data"

        is_trigger = (
            candidate_total * reference_count * Decimal("100")
            >= reference_total * candidate_count * Decimal(
                str(100 + TRIGGER_THRESHOLD_PERCENTAGE)
            )
        )
        return True, is_trigger, "trigger" if is_trigger else "not_trigger"

    @staticmethod
    def _difference_percentage(
        candidate_total: Decimal,
        candidate_count: int,
        reference_total: Decimal,
        reference_count: int,
    ) -> float | None:
        if candidate_count <= 0 or reference_count <= 0 or reference_total <= 0:
            return None
        candidate_average = candidate_total / candidate_count
        reference_average = reference_total / reference_count
        return round(float(((candidate_average / reference_average) - 1) * Decimal("100")), 2)

    @staticmethod
    def _average(total: Decimal, count: int) -> Decimal:
        if count <= 0:
            return Decimal("0.00")
        return (total / count).quantize(CENTS)

    @staticmethod
    def _emotion_role(emotion: str) -> str:
        if emotion == DEFAULT_EMOTION:
            return "not_informed"
        if emotion in REFERENCE_EMOTIONS:
            return "reference"
        return "candidate"

    @staticmethod
    def _emotion_label(emotion: EmotionType) -> str:
        if emotion == DEFAULT_EMOTION:
            return "Nao Informado"
        return EMOTION_LABELS[emotion]

    @staticmethod
    def _is_single_month_period(
        start_date: date | None,
        end_date: date | None,
    ) -> bool:
        if start_date is None or end_date is None:
            return False
        return start_date.year == end_date.year and start_date.month == end_date.month
