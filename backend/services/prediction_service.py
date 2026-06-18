from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from models.transaction import Transaction
from models.user import User
from schemas.prediction import BalancePredictionResponse
from utils.date_utils import now_in_brasilia


CENTS = Decimal("0.01")


class PredictionService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def predict_month_end_balance(
        self,
        current_user: User,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> BalancePredictionResponse:
        today = now_in_brasilia().date()

        if start_date is None:
            start_date = today.replace(day=1)
        if end_date is None:
            next_month_start = self._next_month_start(start_date)
            end_date = next_month_start - timedelta(days=1)

        if start_date > today:
            elapsed_days = 0
            days_remaining = max((end_date - start_date).days + 1, 0)
            current_income = Decimal("0.00")
            current_expense = Decimal("0.00")
        else:
            elapsed_end = min(end_date, today)
            elapsed_days = max((elapsed_end - start_date).days + 1, 0)

            if end_date > today:
                days_remaining = max((end_date - today).days, 0)
            else:
                days_remaining = 0

            current_income, current_expense = self._get_totals_for_range(
                current_user,
                start_date,
                elapsed_end,
            )

        current_daily_average = self._calculate_current_daily_average(
            current_expense,
            elapsed_days,
        )
        expected_variable_expense = self._money(
            current_daily_average * days_remaining
        )
        current_month_balance = self._money(current_income - current_expense)
        predicted_end_balance = self._money(current_month_balance - expected_variable_expense)

        return BalancePredictionResponse(
            month=f"{start_date.year:04d}-{start_date.month:02d}",
            calculated_on=today,
            days_remaining=days_remaining,
            current_income=self._money(current_income),
            current_expense=self._money(current_expense),
            current_month_balance=current_month_balance,
            expected_future_recurring_income=self._money(Decimal("0.00")),
            expected_future_recurring_expense=self._money(Decimal("0.00")),
            historical_daily_variable_expense_average=self._money(
                current_daily_average
            ),
            expected_remaining_variable_expense=expected_variable_expense,
            predicted_end_balance=predicted_end_balance,
            history_months_used=[],
            confidence_level=self._confidence_level(elapsed_days, current_expense),
        )

    def _get_totals_for_range(
        self,
        current_user: User,
        start_date: date,
        end_date: date,
    ) -> tuple[Decimal, Decimal]:
        statement = (
            select(
                Transaction.type,
                func.coalesce(func.sum(Transaction.amount), 0).label("total"),
            )
            .where(
                Transaction.user_id == current_user.id,
                Transaction.date >= start_date,
                Transaction.date <= end_date,
            )
            .group_by(Transaction.type)
        )
        totals = {row.type: row.total for row in self.db.execute(statement)}
        return (
            totals.get("income", Decimal("0.00")),
            totals.get("expense", Decimal("0.00")),
        )

    @staticmethod
    def _calculate_current_daily_average(current_expense: Decimal, elapsed_days: int) -> Decimal:
        if elapsed_days <= 0 or current_expense <= 0:
            return Decimal("0.00")
        return current_expense / elapsed_days

    @staticmethod
    def _confidence_level(elapsed_days: int, current_expense: Decimal) -> str:
        if current_expense <= 0:
            return "insufficient"
        if elapsed_days < 7:
            return "low"
        if elapsed_days < 15:
            return "medium"
        return "high"

    @staticmethod
    def _next_month_start(month_start: date) -> date:
        if month_start.month == 12:
            return date(month_start.year + 1, 1, 1)
        return date(month_start.year, month_start.month + 1, 1)

    @staticmethod
    def _money(value: Decimal) -> Decimal:
        return value.quantize(CENTS)
