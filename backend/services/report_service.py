from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from models.category import Category
from models.transaction import Transaction
from models.user import User
from schemas.report import (
    CategoryReportItem,
    EmotionReportItem,
    SpendingTriggerReportItem,
    SummaryReport,
)
from utils.emotion_rules import DEFAULT_EMOTION, EMOTION_LABELS, VALID_EMOTIONS, normalize_emotion


UNCATEGORIZED_CATEGORY_NAME = "Sem categoria"
CENTS = Decimal("0.01")


class ReportService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_summary(self, current_user: User) -> SummaryReport:
        totals_statement = (
            select(
                Transaction.type,
                func.count(Transaction.id).label("transaction_count"),
                func.coalesce(func.sum(Transaction.amount), 0).label("total_amount"),
            )
            .where(Transaction.user_id == current_user.id)
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
            .where(
                Transaction.user_id == current_user.id,
                Transaction.type == "expense",
            )
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

    def get_by_emotion(self, current_user: User) -> list[EmotionReportItem]:
        statement = (
            select(
                Transaction.emotion,
                func.count(Transaction.id).label("transaction_count"),
                func.coalesce(func.sum(Transaction.amount), 0).label("total_amount"),
            )
            .where(
                Transaction.user_id == current_user.id,
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

        report_items: list[EmotionReportItem] = []
        for emotion in VALID_EMOTIONS:
            data = totals_by_emotion[emotion]
            total_amount = data["total_amount"]
            transaction_count = data["transaction_count"]

            if not isinstance(total_amount, Decimal) or not isinstance(transaction_count, int):
                continue

            percentage = 0.0
            if grand_total > 0:
                percentage = round(float((total_amount / grand_total) * Decimal("100")), 2)

            report_items.append(
                EmotionReportItem(
                    emotion=emotion,
                    label=EMOTION_LABELS[emotion],
                    transaction_count=transaction_count,
                    total_amount=total_amount,
                    percentage=percentage,
                )
            )

        return report_items

    def get_by_category(self, current_user: User) -> list[CategoryReportItem]:
        category_items = self._build_category_report_base(current_user)

        statement = (
            select(
                Transaction.category_id,
                func.count(Transaction.id).label("transaction_count"),
                func.coalesce(func.sum(Transaction.amount), 0).label("total_amount"),
            )
            .where(
                Transaction.user_id == current_user.id,
                Transaction.type == "expense",
            )
            .group_by(Transaction.category_id)
        )

        for row in self.db.execute(statement):
            category_id = row.category_id
            if category_id not in category_items:
                category_id = None

            item = category_items[category_id]
            category_items[category_id] = item.model_copy(
                update={
                    "transaction_count": item.transaction_count + row.transaction_count,
                    "total_amount": item.total_amount + (row.total_amount or Decimal("0.00")),
                }
            )

        grand_total = sum(item.total_amount for item in category_items.values())

        report_items: list[CategoryReportItem] = []
        for item in category_items.values():
            report_items.append(
                item.model_copy(
                    update={
                        "percentage": self._calculate_percentage(item.total_amount, grand_total)
                    }
                )
            )

        return sorted(
            report_items,
            key=lambda item: (
                item.total_amount == 0,
                -item.total_amount,
                item.category_name,
            ),
        )

    def get_spending_triggers(self, current_user: User) -> list[SpendingTriggerReportItem]:
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
                Transaction.user_id == current_user.id,
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

            category_id = row.category_id
            category = categories_by_id.get(category_id) if category_id is not None else None
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
            category_id = data["category_id"]
            category_name = data["category_name"]
            transaction_count = data["transaction_count"]
            total_amount = data["total_amount"]

            if (
                not isinstance(emotion, str)
                or not isinstance(category_id, int | type(None))
                or not isinstance(category_name, str)
                or not isinstance(transaction_count, int)
                or not isinstance(total_amount, Decimal)
            ):
                continue

            average_amount = Decimal("0.00")
            if transaction_count > 0:
                average_amount = (total_amount / transaction_count).quantize(CENTS)

            report_items.append(
                SpendingTriggerReportItem(
                    emotion=normalize_emotion(emotion),
                    emotion_label=EMOTION_LABELS[normalize_emotion(emotion)],
                    category_id=category_id,
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

    def _build_category_report_base(self, current_user: User) -> dict[int | None, CategoryReportItem]:
        category_items: dict[int | None, CategoryReportItem] = {
            None: CategoryReportItem(
                category_id=None,
                category_name=UNCATEGORIZED_CATEGORY_NAME,
                is_default=False,
                is_essential=False,
                transaction_count=0,
                total_amount=Decimal("0.00"),
                percentage=0.0,
            )
        }

        for category in self._list_accessible_expense_categories(current_user):
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

    @staticmethod
    def _calculate_percentage(total_amount: Decimal, grand_total: Decimal) -> float:
        if grand_total <= 0:
            return 0.0
        return round(float((total_amount / grand_total) * Decimal("100")), 2)
