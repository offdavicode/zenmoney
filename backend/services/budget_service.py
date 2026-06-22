from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from models.budget_alert import BudgetAlert
from models.budget_limit import BudgetLimit
from models.category import Category
from models.transaction import Transaction
from models.user import User
from schemas.budget import BudgetLimitStatus, BudgetSettingsResponse, BudgetSettingsUpdate
from utils.month_utils import parse_month_label


GLOBAL_BUDGET_NAME = "Limite mensal geral"
INCONSISTENT_LIMITS_MESSAGE = (
    "A soma dos limites por categoria não pode exceder o limite global."
)


class BudgetServiceError(Exception):
    def __init__(self, message: str, status_code: int) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class BudgetService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_budget_settings(
        self,
        current_user: User,
        month: str | None = None,
    ) -> BudgetSettingsResponse:
        month_label, month_start, next_month_start = self._parse_month(month)
        limits = self._list_limits(current_user)
        spent_by_category = self._get_spent_by_category(current_user, month_start, next_month_start)
        total_spent = sum(spent_by_category.values(), Decimal("0.00"))

        global_limit = None
        category_limits: list[BudgetLimitStatus] = []

        for limit in limits:
            if limit.category_id is None:
                global_limit = self._build_limit_status(
                    category_id=None,
                    category_name=GLOBAL_BUDGET_NAME,
                    limit_amount=limit.amount,
                    spent_amount=total_spent,
                )
                continue

            category_name = limit.category.name if limit.category is not None else "Categoria removida"
            category_limits.append(
                self._build_limit_status(
                    category_id=limit.category_id,
                    category_name=category_name,
                    limit_amount=limit.amount,
                    spent_amount=spent_by_category.get(limit.category_id, Decimal("0.00")),
                )
            )

        category_limits.sort(key=lambda item: item.category_name)

        return BudgetSettingsResponse(
            month=month_label,
            global_limit=global_limit,
            category_limits=category_limits,
            alerts_enabled=global_limit is not None or bool(category_limits),
        )

    def update_budget_settings(
        self,
        current_user: User,
        payload: BudgetSettingsUpdate,
        month: str | None = None,
    ) -> BudgetSettingsResponse:
        seen_category_ids: set[int] = set()
        for item in payload.category_limits:
            if item.category_id in seen_category_ids:
                raise BudgetServiceError("Limite de categoria duplicado na requisição.", 400)
            seen_category_ids.add(item.category_id)
            self._resolve_budget_category(current_user, item.category_id)

        proposed_limits = self._build_proposed_limits(current_user, payload)
        self._validate_limit_relationship(proposed_limits)

        if "global_limit" in payload.model_fields_set:
            self._set_limit(
                current_user=current_user,
                category_id=None,
                amount=payload.global_limit,
            )

        if "category_limits" in payload.model_fields_set:
            existing_limits = self._list_limits(current_user)
            for limit in existing_limits:
                if limit.category_id is not None and limit.category_id not in seen_category_ids:
                    self.db.delete(limit)
                    self._delete_alert_history(current_user, limit.category_id)

        for item in payload.category_limits:
            self._set_limit(
                current_user=current_user,
                category_id=item.category_id,
                amount=item.amount,
            )

        self.db.commit()
        return self.get_budget_settings(current_user, month)

    def _build_proposed_limits(
        self,
        current_user: User,
        payload: BudgetSettingsUpdate,
    ) -> dict[int | None, Decimal]:
        proposed_limits = {
            limit.category_id: limit.amount
            for limit in self._list_limits(current_user)
        }

        if "global_limit" in payload.model_fields_set:
            self._apply_proposed_limit(
                proposed_limits,
                category_id=None,
                amount=payload.global_limit,
            )

        for item in payload.category_limits:
            self._apply_proposed_limit(
                proposed_limits,
                category_id=item.category_id,
                amount=item.amount,
            )

        return proposed_limits

    @staticmethod
    def _apply_proposed_limit(
        proposed_limits: dict[int | None, Decimal],
        category_id: int | None,
        amount: Decimal | None,
    ) -> None:
        if amount is None:
            proposed_limits.pop(category_id, None)
            return
        proposed_limits[category_id] = amount

    @staticmethod
    def _validate_limit_relationship(
        proposed_limits: dict[int | None, Decimal],
    ) -> None:
        global_limit = proposed_limits.get(None)
        if global_limit is None:
            return

        category_total = sum(
            (
                amount
                for category_id, amount in proposed_limits.items()
                if category_id is not None
            ),
            Decimal("0.00"),
        )
        if category_total > global_limit:
            raise BudgetServiceError(INCONSISTENT_LIMITS_MESSAGE, 400)

    def _set_limit(
        self,
        current_user: User,
        category_id: int | None,
        amount: Decimal | None,
    ) -> None:
        existing_limit = self._get_limit(current_user, category_id)

        if amount is None:
            if existing_limit is not None:
                self.db.delete(existing_limit)
            self._delete_alert_history(current_user, category_id)
            return

        if existing_limit is None:
            self.db.add(
                BudgetLimit(
                    user_id=current_user.id,
                    category_id=category_id,
                    amount=amount,
                )
            )
            self._delete_alert_history(current_user, category_id)
            return

        if existing_limit.amount != amount:
            self._delete_alert_history(current_user, category_id)
        existing_limit.amount = amount

    def _get_limit(self, current_user: User, category_id: int | None) -> BudgetLimit | None:
        statement = select(BudgetLimit).where(BudgetLimit.user_id == current_user.id)
        if category_id is None:
            statement = statement.where(BudgetLimit.category_id.is_(None))
        else:
            statement = statement.where(BudgetLimit.category_id == category_id)
        return self.db.scalar(statement)

    def _list_limits(self, current_user: User) -> list[BudgetLimit]:
        statement = (
            select(BudgetLimit)
            .where(BudgetLimit.user_id == current_user.id)
            .order_by(BudgetLimit.category_id.is_not(None), BudgetLimit.category_id)
        )
        return list(self.db.scalars(statement))

    def _resolve_budget_category(self, current_user: User, category_id: int) -> Category:
        statement = select(Category).where(
            Category.id == category_id,
            Category.type == "expense",
            (Category.user_id == current_user.id) | (Category.user_id.is_(None)),
        )
        category = self.db.scalar(statement)
        if category is None:
            raise BudgetServiceError("Categoria não encontrada ou não disponível para orçamento de despesas.", 404)
        return category

    def _get_spent_by_category(
        self,
        current_user: User,
        month_start,
        next_month_start,
    ) -> dict[int | None, Decimal]:
        statement = (
            select(
                Transaction.category_id,
                func.coalesce(func.sum(Transaction.amount), 0).label("spent_amount"),
            )
            .where(
                Transaction.user_id == current_user.id,
                Transaction.type == "expense",
                Transaction.date >= month_start,
                Transaction.date < next_month_start,
            )
            .group_by(Transaction.category_id)
        )

        return {
            row.category_id: row.spent_amount or Decimal("0.00")
            for row in self.db.execute(statement)
        }

    def _build_limit_status(
        self,
        category_id: int | None,
        category_name: str,
        limit_amount: Decimal,
        spent_amount: Decimal,
    ) -> BudgetLimitStatus:
        remaining_amount = limit_amount - spent_amount
        return BudgetLimitStatus(
            category_id=category_id,
            category_name=category_name,
            limit_amount=limit_amount,
            spent_amount=spent_amount,
            remaining_amount=remaining_amount,
            usage_percentage=self._calculate_percentage(spent_amount, limit_amount),
            is_exceeded=spent_amount > limit_amount,
        )

    def _delete_alert_history(self, current_user: User, category_id: int | None) -> None:
        scope_key = self._scope_key(category_id)
        statement = select(BudgetAlert).where(
            BudgetAlert.user_id == current_user.id,
            BudgetAlert.scope_key == scope_key,
        )
        for alert in self.db.scalars(statement):
            self.db.delete(alert)

    @staticmethod
    def _calculate_percentage(spent_amount: Decimal, limit_amount: Decimal) -> float:
        if limit_amount <= 0:
            return 0.0
        return round(float((spent_amount / limit_amount) * Decimal("100")), 2)

    @staticmethod
    def _scope_key(category_id: int | None) -> str:
        if category_id is None:
            return "global"
        return f"category:{category_id}"

    @staticmethod
    def _parse_month(month: str | None):
        try:
            return parse_month_label(month)
        except ValueError as exc:
            raise BudgetServiceError(str(exc), 400) from exc
