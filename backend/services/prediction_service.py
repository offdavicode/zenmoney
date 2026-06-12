from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from models.recurrence import Recurrence
from models.transaction import Transaction
from models.user import User
from schemas.prediction import BalancePredictionResponse, PredictionHistoryMonth
from utils.date_utils import now_in_brasilia
from utils.recurrence_dates import next_scheduled_date


CENTS = Decimal("0.01")
MAX_HISTORY_MONTHS = 3
CONFIDENCE_BY_MONTH_COUNT = {
    0: "insufficient",
    1: "low",
    2: "medium",
    3: "high",
}


class PredictionService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def predict_month_end_balance(self, current_user: User) -> BalancePredictionResponse:
        today = now_in_brasilia().date()
        month_start = today.replace(day=1)
        next_month_start = self._next_month_start(month_start)
        days_remaining = max((next_month_start - today).days - 1, 0)

        current_income, current_expense = self._get_current_totals(
            current_user,
            month_start,
            next_month_start,
        )
        future_income, future_expense = self._get_future_recurring_totals(
            current_user,
            month_start,
            next_month_start,
        )
        history_months = self._get_history_months(current_user, month_start)
        exact_historical_daily_average = self._calculate_historical_daily_average(
            history_months
        )
        expected_variable_expense = self._money(
            exact_historical_daily_average * days_remaining
        )
        current_month_balance = self._money(current_income - current_expense)
        predicted_end_balance = self._money(
            current_month_balance
            + future_income
            - future_expense
            - expected_variable_expense
        )

        return BalancePredictionResponse(
            month=f"{today.year:04d}-{today.month:02d}",
            calculated_on=today,
            days_remaining=days_remaining,
            current_income=self._money(current_income),
            current_expense=self._money(current_expense),
            current_month_balance=current_month_balance,
            expected_future_recurring_income=self._money(future_income),
            expected_future_recurring_expense=self._money(future_expense),
            historical_daily_variable_expense_average=self._money(
                exact_historical_daily_average
            ),
            expected_remaining_variable_expense=expected_variable_expense,
            predicted_end_balance=predicted_end_balance,
            history_months_used=history_months,
            confidence_level=CONFIDENCE_BY_MONTH_COUNT[len(history_months)],
        )

    def _get_current_totals(
        self,
        current_user: User,
        month_start: date,
        next_month_start: date,
    ) -> tuple[Decimal, Decimal]:
        statement = (
            select(
                Transaction.type,
                func.coalesce(func.sum(Transaction.amount), 0).label("total"),
            )
            .where(
                Transaction.user_id == current_user.id,
                Transaction.date >= month_start,
                Transaction.date < next_month_start,
            )
            .group_by(Transaction.type)
        )
        totals = {row.type: row.total for row in self.db.execute(statement)}
        return (
            totals.get("income", Decimal("0.00")),
            totals.get("expense", Decimal("0.00")),
        )

    def _get_future_recurring_totals(
        self,
        current_user: User,
        month_start: date,
        next_month_start: date,
    ) -> tuple[Decimal, Decimal]:
        recurrences = self.db.scalars(
            select(Recurrence).where(
                Recurrence.user_id == current_user.id,
                Recurrence.is_active.is_(True),
                Recurrence.next_run_date < next_month_start,
                (Recurrence.end_date.is_(None)) | (Recurrence.end_date >= month_start),
            )
        )
        income = Decimal("0.00")
        expense = Decimal("0.00")

        for recurrence in recurrences:
            occurrence_date = recurrence.next_run_date
            while occurrence_date < month_start:
                occurrence_date = next_scheduled_date(
                    occurrence_date,
                    recurrence.day_of_month,
                )
            while occurrence_date < next_month_start:
                if recurrence.end_date is not None and occurrence_date > recurrence.end_date:
                    break
                if occurrence_date >= month_start:
                    if recurrence.type == "income":
                        income += recurrence.amount
                    elif recurrence.type == "expense":
                        expense += recurrence.amount
                occurrence_date = next_scheduled_date(
                    occurrence_date,
                    recurrence.day_of_month,
                )

        return income, expense

    def _get_history_months(
        self,
        current_user: User,
        current_month_start: date,
    ) -> list[PredictionHistoryMonth]:
        history: list[PredictionHistoryMonth] = []
        month_end = current_month_start

        for _ in range(MAX_HISTORY_MONTHS):
            month_start = self._previous_month_start(month_end)
            variable_total, transaction_count = self.db.execute(
                select(
                    func.coalesce(func.sum(Transaction.amount), 0),
                    func.count(Transaction.id),
                ).where(
                    Transaction.user_id == current_user.id,
                    Transaction.type == "expense",
                    Transaction.is_recurring.is_(False),
                    Transaction.date >= month_start,
                    Transaction.date < month_end,
                )
            ).one()

            if transaction_count > 0:
                history.append(
                    PredictionHistoryMonth(
                        month=f"{month_start.year:04d}-{month_start.month:02d}",
                        variable_expense=self._money(variable_total),
                        days_in_month=(month_end - month_start).days,
                    )
                )
            month_end = month_start

        return history

    @classmethod
    def _calculate_historical_daily_average(
        cls,
        history_months: list[PredictionHistoryMonth],
    ) -> Decimal:
        if not history_months:
            return Decimal("0.00")

        total_expense = sum(
            (month.variable_expense for month in history_months),
            Decimal("0.00"),
        )
        total_days = sum(month.days_in_month for month in history_months)
        return total_expense / total_days

    @staticmethod
    def _next_month_start(month_start: date) -> date:
        if month_start.month == 12:
            return date(month_start.year + 1, 1, 1)
        return date(month_start.year, month_start.month + 1, 1)

    @staticmethod
    def _previous_month_start(month_start: date) -> date:
        if month_start.month == 1:
            return date(month_start.year - 1, 12, 1)
        return date(month_start.year, month_start.month - 1, 1)

    @staticmethod
    def _money(value: Decimal) -> Decimal:
        return value.quantize(CENTS)
