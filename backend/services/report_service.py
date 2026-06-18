from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from models.category import Category
from models.transaction import Transaction
from models.user import User
from schemas.report import (
    CategoryReportItem,
    EmotionReportItem,
    ReportPeriod,
    SpendingTriggerReportItem,
    SummaryReport,
    VisualReportItem,
    VisualReportResponse,
    VisualReportSection,
)
from utils.emotion_rules import DEFAULT_EMOTION, EMOTION_LABELS, VALID_EMOTIONS, normalize_emotion
from utils.month_utils import parse_month_label


UNCATEGORIZED_CATEGORY_NAME = "Sem categoria"
OTHER_ITEMS_LABEL = "Outros"
CENTS = Decimal("0.01")
MINIMUM_INSIGHT_TRANSACTIONS = 5
MINIMUM_CHART_PERCENTAGE = 1.0
MAX_CHART_ITEMS = 10


class ReportServiceError(Exception):
    def __init__(self, message: str, status_code: int) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


@dataclass(frozen=True)
class ReportFilters:
    start_date: date | None
    end_date: date | None
    category_id: int | None


class ReportService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_summary(
        self,
        current_user: User,
        month: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> SummaryReport:
        filters = self._resolve_filters(current_user, month, start_date, end_date)
        conditions = self._transaction_conditions(current_user, filters)
        totals_statement = (
            select(
                Transaction.type,
                func.count(Transaction.id).label("transaction_count"),
                func.coalesce(func.sum(Transaction.amount), 0).label("total_amount"),
            )
            .where(*conditions)
            .group_by(Transaction.type)
        )

        transaction_count = 0
        income_count = 0
        expense_count = 0
        total_income = Decimal("0.00")
        total_expense = Decimal("0.00")

        for row in self.db.execute(totals_statement):
            transaction_count += row.transaction_count
            if row.type == "income":
                income_count = row.transaction_count
                total_income = row.total_amount or Decimal("0.00")
            elif row.type == "expense":
                expense_count = row.transaction_count
                total_expense = row.total_amount or Decimal("0.00")

        essential_expense = Decimal("0.00")
        non_essential_expense = Decimal("0.00")
        uncategorized_expense = Decimal("0.00")

        expense_breakdown_statement = (
            select(
                Transaction.category_id,
                Category.is_essential,
                func.coalesce(func.sum(Transaction.amount), 0).label("total_amount"),
            )
            .outerjoin(Category, Transaction.category_id == Category.id)
            .where(*conditions, Transaction.type == "expense")
            .group_by(Transaction.category_id, Category.is_essential)
        )

        for row in self.db.execute(expense_breakdown_statement):
            amount = row.total_amount or Decimal("0.00")
            if row.category_id is None:
                uncategorized_expense += amount

            if row.is_essential is True:
                essential_expense += amount
            else:
                non_essential_expense += amount

        average_expense = Decimal("0.00")
        if expense_count > 0:
            average_expense = (total_expense / expense_count).quantize(CENTS)

        return SummaryReport(
            transaction_count=transaction_count,
            income_count=income_count,
            expense_count=expense_count,
            total_income=total_income,
            total_expense=total_expense,
            balance=total_income - total_expense,
            average_expense=average_expense,
            essential_expense=essential_expense,
            essential_expense_percentage=self._calculate_percentage(
                essential_expense,
                total_expense,
            ),
            non_essential_expense=non_essential_expense,
            non_essential_expense_percentage=self._calculate_percentage(
                non_essential_expense,
                total_expense,
            ),
            uncategorized_expense=uncategorized_expense,
        )

    def get_by_emotion(
        self,
        current_user: User,
        month: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        category_id: int | None = None,
    ) -> list[EmotionReportItem]:
        filters = self._resolve_filters(current_user, month, start_date, end_date, category_id)
        statement = (
            select(
                Transaction.emotion,
                func.count(Transaction.id).label("transaction_count"),
                func.coalesce(func.sum(Transaction.amount), 0).label("total_amount"),
            )
            .where(
                *self._transaction_conditions(current_user, filters),
                Transaction.type == "expense",
            )
            .group_by(Transaction.emotion)
        )

        totals_by_emotion: dict[str, dict[str, Decimal | int]] = {
            emotion: {
                "transaction_count": 0,
                "total_amount": Decimal("0.00"),
            }
            for emotion in VALID_EMOTIONS
        }

        for row in self.db.execute(statement):
            try:
                emotion = normalize_emotion(row.emotion)
            except ValueError:
                emotion = DEFAULT_EMOTION

            totals_by_emotion[emotion]["transaction_count"] += row.transaction_count
            totals_by_emotion[emotion]["total_amount"] += row.total_amount or Decimal("0.00")

        grand_total = sum(
            data["total_amount"]
            for data in totals_by_emotion.values()
            if isinstance(data["total_amount"], Decimal)
        )
        insight_period_is_valid = self._is_single_month_period(filters)

        report_items: list[EmotionReportItem] = []
        for emotion in VALID_EMOTIONS:
            data = totals_by_emotion[emotion]
            total_amount = data["total_amount"]
            transaction_count = data["transaction_count"]

            if not isinstance(total_amount, Decimal) or not isinstance(transaction_count, int):
                continue

            average_amount = Decimal("0.00")
            if transaction_count > 0:
                average_amount = (total_amount / transaction_count).quantize(CENTS)

            report_items.append(
                EmotionReportItem(
                    emotion=emotion,
                    label=EMOTION_LABELS[emotion],
                    transaction_count=transaction_count,
                    total_amount=total_amount,
                    average_amount=average_amount,
                    percentage=self._calculate_percentage(total_amount, grand_total),
                    insight_eligible=(
                        emotion != DEFAULT_EMOTION
                        and insight_period_is_valid
                        and transaction_count >= MINIMUM_INSIGHT_TRANSACTIONS
                    ),
                )
            )

        return report_items

    def get_by_category(
        self,
        current_user: User,
        month: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        category_id: int | None = None,
    ) -> list[CategoryReportItem]:
        filters = self._resolve_filters(current_user, month, start_date, end_date, category_id)
        category_items = self._build_category_report_base(current_user, category_id)

        statement = (
            select(
                Transaction.category_id,
                func.count(Transaction.id).label("transaction_count"),
                func.coalesce(func.sum(Transaction.amount), 0).label("total_amount"),
            )
            .where(
                *self._transaction_conditions(current_user, filters),
                Transaction.type == "expense",
            )
            .group_by(Transaction.category_id)
        )

        for row in self.db.execute(statement):
            safe_category_id = row.category_id if row.category_id in category_items else None
            if safe_category_id not in category_items:
                continue

            item = category_items[safe_category_id]
            category_items[safe_category_id] = item.model_copy(
                update={
                    "transaction_count": item.transaction_count + row.transaction_count,
                    "total_amount": item.total_amount + (row.total_amount or Decimal("0.00")),
                }
            )

        grand_total = sum(item.total_amount for item in category_items.values())
        report_items = [
            item.model_copy(
                update={"percentage": self._calculate_percentage(item.total_amount, grand_total)}
            )
            for item in category_items.values()
        ]

        return sorted(
            report_items,
            key=lambda item: (
                item.total_amount == 0,
                -item.total_amount,
                item.category_name,
            ),
        )

    def get_visual_report(
        self,
        current_user: User,
        month: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        category_id: int | None = None,
    ) -> VisualReportResponse:
        filters = self._resolve_filters(current_user, month, start_date, end_date, category_id)
        category_items = self.get_by_category(
            current_user, month, start_date, end_date, category_id
        )
        emotion_items = self.get_by_emotion(
            current_user, month, start_date, end_date, category_id
        )
        total_expense = sum((item.total_amount for item in category_items), Decimal("0.00"))

        visual_categories = [
            VisualReportItem(
                key=str(item.category_id) if item.category_id is not None else "uncategorized",
                label=item.category_name,
                transaction_count=item.transaction_count,
                total_amount=item.total_amount,
                percentage=item.percentage,
            )
            for item in category_items
            if item.transaction_count > 0
        ]
        visual_emotions = [
            VisualReportItem(
                key=item.emotion,
                label=item.label,
                transaction_count=item.transaction_count,
                total_amount=item.total_amount,
                percentage=item.percentage,
                insight_eligible=item.insight_eligible,
            )
            for item in emotion_items
            if item.transaction_count > 0
        ]

        return VisualReportResponse(
            period=ReportPeriod(
                start_date=filters.start_date,
                end_date=filters.end_date,
                category_id=filters.category_id,
            ),
            total_expense=total_expense,
            category_distribution=self._build_visual_section(visual_categories),
            emotion_distribution=self._build_visual_section(visual_emotions),
        )

    def get_spending_triggers(
        self,
        current_user: User,
        month: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        category_id: int | None = None,
    ) -> list[SpendingTriggerReportItem]:
        filters = self._resolve_filters(current_user, month, start_date, end_date, category_id)
        categories_by_id = {
            category.id: category
            for category in self._list_accessible_expense_categories(current_user)
        }

        statement = (
            select(
                Transaction.emotion,
                Transaction.category_id,
                func.count(Transaction.id).label("transaction_count"),
                func.coalesce(func.sum(Transaction.amount), 0).label("total_amount"),
            )
            .where(
                *self._transaction_conditions(current_user, filters),
                Transaction.type == "expense",
            )
            .group_by(Transaction.emotion, Transaction.category_id)
        )

        raw_items: dict[tuple[str, int | None], dict[str, Decimal | int | str | None]] = {}
        for row in self.db.execute(statement):
            try:
                emotion = normalize_emotion(row.emotion)
            except ValueError:
                emotion = DEFAULT_EMOTION

            category = categories_by_id.get(row.category_id) if row.category_id is not None else None
            category_name = category.name if category is not None else UNCATEGORIZED_CATEGORY_NAME
            safe_category_id = category.id if category is not None else None
            key = (emotion, safe_category_id)

            if key not in raw_items:
                raw_items[key] = {
                    "emotion": emotion,
                    "category_id": safe_category_id,
                    "category_name": category_name,
                    "transaction_count": 0,
                    "total_amount": Decimal("0.00"),
                }

            raw_items[key]["transaction_count"] += row.transaction_count
            raw_items[key]["total_amount"] += row.total_amount or Decimal("0.00")

        grand_total = sum(
            data["total_amount"]
            for data in raw_items.values()
            if isinstance(data["total_amount"], Decimal)
        )

        report_items: list[SpendingTriggerReportItem] = []
        for data in raw_items.values():
            emotion = data["emotion"]
            category_id_value = data["category_id"]
            category_name = data["category_name"]
            transaction_count = data["transaction_count"]
            total_amount = data["total_amount"]

            if (
                not isinstance(emotion, str)
                or not isinstance(category_id_value, int | type(None))
                or not isinstance(category_name, str)
                or not isinstance(transaction_count, int)
                or not isinstance(total_amount, Decimal)
            ):
                continue

            average_amount = Decimal("0.00")
            if transaction_count > 0:
                average_amount = (total_amount / transaction_count).quantize(CENTS)

            normalized_emotion = normalize_emotion(emotion)
            report_items.append(
                SpendingTriggerReportItem(
                    emotion=normalized_emotion,
                    emotion_label=EMOTION_LABELS[normalized_emotion],
                    category_id=category_id_value,
                    category_name=category_name,
                    transaction_count=transaction_count,
                    total_amount=total_amount,
                    average_amount=average_amount,
                    percentage=self._calculate_percentage(total_amount, grand_total),
                )
            )

        return sorted(
            report_items,
            key=lambda item: (-item.total_amount, -item.transaction_count, item.category_name, item.emotion),
        )

    def _resolve_filters(
        self,
        current_user: User,
        month: str | None,
        start_date: date | None,
        end_date: date | None,
        category_id: int | None = None,
    ) -> ReportFilters:
        if month is not None and (start_date is not None or end_date is not None):
            raise ReportServiceError(
                "Use o mês ou a data de início/fim, mas não ambos.",
                400,
            )
        if start_date is not None and end_date is not None and start_date > end_date:
            raise ReportServiceError("A data de início deve ser anterior ou igual à data de fim.", 400)

        resolved_start = start_date
        resolved_end = end_date

        if month is not None:
            try:
                _, resolved_start, next_month_start = parse_month_label(month)
            except ValueError as exc:
                raise ReportServiceError(str(exc), 400) from exc
            resolved_end = next_month_start - timedelta(days=1)

        if category_id is not None:
            self._resolve_expense_category(current_user, category_id)

        return ReportFilters(
            start_date=resolved_start,
            end_date=resolved_end,
            category_id=category_id,
        )

    @staticmethod
    def _transaction_conditions(current_user: User, filters: ReportFilters) -> list:
        conditions = [Transaction.user_id == current_user.id]
        if filters.start_date is not None:
            conditions.append(Transaction.date >= filters.start_date)
        if filters.end_date is not None:
            conditions.append(Transaction.date <= filters.end_date)
        if filters.category_id is not None:
            conditions.append(Transaction.category_id == filters.category_id)
        return conditions

    def _resolve_expense_category(self, current_user: User, category_id: int) -> Category:
        statement = select(Category).where(
            Category.id == category_id,
            Category.type == "expense",
            (Category.user_id == current_user.id) | (Category.user_id.is_(None)),
        )
        category = self.db.scalar(statement)
        if category is None:
            raise ReportServiceError("Categoria de despesa não encontrada.", 404)
        return category

    def _build_category_report_base(
        self,
        current_user: User,
        category_id: int | None = None,
    ) -> dict[int | None, CategoryReportItem]:
        category_items: dict[int | None, CategoryReportItem] = {}
        if category_id is None:
            category_items[None] = CategoryReportItem(
                category_id=None,
                category_name=UNCATEGORIZED_CATEGORY_NAME,
                is_default=False,
                is_essential=False,
                transaction_count=0,
                total_amount=Decimal("0.00"),
                percentage=0.0,
            )

        for category in self._list_accessible_expense_categories(current_user):
            if category_id is not None and category.id != category_id:
                continue
            category_items[category.id] = CategoryReportItem(
                category_id=category.id,
                category_name=category.name,
                is_default=category.is_default,
                is_essential=category.is_essential,
                transaction_count=0,
                total_amount=Decimal("0.00"),
                percentage=0.0,
            )

        return category_items

    def _list_accessible_expense_categories(self, current_user: User) -> list[Category]:
        statement = (
            select(Category)
            .where(
                Category.type == "expense",
                (Category.user_id == current_user.id) | (Category.user_id.is_(None)),
            )
            .order_by(Category.is_default.desc(), Category.name.asc())
        )
        return list(self.db.scalars(statement))

    def _build_visual_section(self, items: list[VisualReportItem]) -> VisualReportSection:
        sorted_items = sorted(items, key=lambda item: (-item.total_amount, item.label))
        relevant_items = [
            item for item in sorted_items if item.percentage >= MINIMUM_CHART_PERCENTAGE
        ]
        tiny_items = [
            item for item in sorted_items if item.percentage < MINIMUM_CHART_PERCENTAGE
        ]

        bar_items = relevant_items[:MAX_CHART_ITEMS]
        bar_item_keys = {item.key for item in bar_items}
        textual_items = [
            item for item in sorted_items if item.key not in bar_item_keys
        ]

        pie_items = relevant_items
        aggregated_items = tiny_items
        if len(relevant_items) > MAX_CHART_ITEMS:
            pie_items = relevant_items[: MAX_CHART_ITEMS - 1]
            aggregated_items = tiny_items + relevant_items[MAX_CHART_ITEMS - 1 :]
        elif tiny_items and len(relevant_items) == MAX_CHART_ITEMS:
            pie_items = relevant_items[: MAX_CHART_ITEMS - 1]
            aggregated_items = tiny_items + relevant_items[MAX_CHART_ITEMS - 1 :]

        if aggregated_items:
            total_amount = sum((item.total_amount for item in sorted_items), Decimal("0.00"))
            aggregated_amount = sum(
                (item.total_amount for item in aggregated_items),
                Decimal("0.00"),
            )
            pie_items.append(
                VisualReportItem(
                    key="others",
                    label=OTHER_ITEMS_LABEL,
                    transaction_count=sum(item.transaction_count for item in aggregated_items),
                    total_amount=aggregated_amount,
                    percentage=self._calculate_percentage(
                        aggregated_amount,
                        total_amount,
                    ),
                    is_aggregated=True,
                    insight_eligible=False,
                )
            )

        return VisualReportSection(
            pie_items=pie_items,
            bar_items=bar_items,
            textual_items=sorted(textual_items, key=lambda item: (-item.total_amount, item.label)),
        )

    @staticmethod
    def _is_single_month_period(filters: ReportFilters) -> bool:
        if filters.start_date is None or filters.end_date is None:
            return False
        return (
            filters.start_date.year == filters.end_date.year
            and filters.start_date.month == filters.end_date.month
        )

    @staticmethod
    def _calculate_percentage(total_amount: Decimal, grand_total: Decimal) -> float:
        if grand_total <= 0:
            return 0.0
        return round(float((total_amount / grand_total) * Decimal("100")), 2)
