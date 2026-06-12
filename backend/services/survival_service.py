from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from models.category import Category
from models.survival_setting import SurvivalSetting
from models.transaction import Transaction
from models.user import User
from schemas.budget import BudgetLimitStatus
from schemas.survival import (
    SurvivalModeResponse,
    SurvivalRecommendation,
    SurvivalSettingResponse,
    SurvivalSettingUpdate,
    SurvivalTrigger,
)
from services.budget_service import BudgetService, BudgetServiceError
from utils.month_utils import parse_month_label


DEFAULT_ACTIVATION_PERCENTAGE = 80
FALLBACK_NON_ESSENTIAL_CATEGORY_NAMES = {"lazer", "hobbies", "compras"}


class SurvivalService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_setting(self, current_user: User) -> SurvivalSettingResponse:
        setting = self._get_stored_setting(current_user)
        if setting is None:
            return SurvivalSettingResponse(
                activation_percentage=DEFAULT_ACTIVATION_PERCENTAGE,
                is_default=True,
            )
        return SurvivalSettingResponse(
            activation_percentage=setting.activation_percentage,
            is_default=False,
        )

    def update_setting(
        self,
        current_user: User,
        payload: SurvivalSettingUpdate,
    ) -> SurvivalSettingResponse:
        setting = self._get_stored_setting(current_user)
        if setting is None:
            setting = SurvivalSetting(
                user_id=current_user.id,
                activation_percentage=payload.activation_percentage,
            )
            self.db.add(setting)
        else:
            setting.activation_percentage = payload.activation_percentage

        self.db.commit()
        return SurvivalSettingResponse(
            activation_percentage=setting.activation_percentage,
            is_default=False,
        )

    def evaluate_mode(
        self,
        current_user: User,
        month: str | None = None,
    ) -> SurvivalModeResponse:
        setting = self.get_setting(current_user)
        budget_status = BudgetService(self.db).get_budget_settings(current_user, month)
        trigger_status = self._select_trigger(
            budget_status.global_limit,
            budget_status.category_limits,
            setting.activation_percentage,
        )

        if not budget_status.alerts_enabled:
            return self._inactive_response(
                month=budget_status.month,
                activation_percentage=setting.activation_percentage,
                reason="no_limits",
            )

        if trigger_status is None:
            return self._inactive_response(
                month=budget_status.month,
                activation_percentage=setting.activation_percentage,
                reason="below_threshold",
            )

        recommendation_rows = self._get_non_essential_spending(
            current_user,
            budget_status.month,
        )
        category_limits = {
            item.category_id: item
            for item in budget_status.category_limits
            if item.category_id is not None
        }
        recommendations = self._build_recommendations(
            recommendation_rows,
            category_limits,
        )
        recommended_category_ids = {item.category_id for item in recommendations}

        return SurvivalModeResponse(
            month=budget_status.month,
            activation_percentage=setting.activation_percentage,
            is_active=True,
            activation_reason=(
                "global_limit" if trigger_status.category_id is None else "category_limit"
            ),
            trigger=self._build_trigger(trigger_status),
            recommendations=recommendations,
            highlighted_transaction_ids=self._get_highlighted_transaction_ids(
                current_user,
                budget_status.month,
                recommended_category_ids,
            ),
        )

    def _get_stored_setting(self, current_user: User) -> SurvivalSetting | None:
        return self.db.scalar(
            select(SurvivalSetting).where(SurvivalSetting.user_id == current_user.id)
        )

    @staticmethod
    def _select_trigger(
        global_limit: BudgetLimitStatus | None,
        category_limits: list[BudgetLimitStatus],
        activation_percentage: int,
    ) -> BudgetLimitStatus | None:
        candidates = [
            status
            for status in ([global_limit] if global_limit is not None else []) + category_limits
            if status.spent_amount * Decimal("100")
            >= status.limit_amount * activation_percentage
        ]
        if not candidates:
            return None

        return max(
            candidates,
            key=lambda status: (
                status.spent_amount / status.limit_amount,
                status.spent_amount - status.limit_amount,
                1 if status.category_id is not None else 0,
            ),
        )

    def _get_non_essential_spending(
        self,
        current_user: User,
        month: str,
    ) -> list:
        _, month_start, next_month_start = self._parse_month(month)
        statement = (
            select(
                Category.id.label("category_id"),
                Category.name.label("category_name"),
                func.coalesce(func.sum(Transaction.amount), 0).label("spent_amount"),
            )
            .join(Transaction, Transaction.category_id == Category.id)
            .where(
                Transaction.user_id == current_user.id,
                Transaction.type == "expense",
                Transaction.date >= month_start,
                Transaction.date < next_month_start,
                (Category.user_id == current_user.id) | (Category.user_id.is_(None)),
                (
                    Category.is_essential.is_(False)
                    | (func.lower(Category.name).in_(FALLBACK_NON_ESSENTIAL_CATEGORY_NAMES))
                ),
            )
            .group_by(Category.id, Category.name)
        )
        return list(self.db.execute(statement))

    @staticmethod
    def _build_recommendations(
        spending_rows: list,
        category_limits: dict[int, BudgetLimitStatus],
    ) -> list[SurvivalRecommendation]:
        recommendations: list[tuple[SurvivalRecommendation, Decimal]] = []

        for row in spending_rows:
            limit_status = category_limits.get(row.category_id)
            exceeded_amount = Decimal("0.00")
            limit_amount = None
            usage_percentage = None
            exact_usage = Decimal("0.00")
            if limit_status is not None:
                limit_amount = limit_status.limit_amount
                usage_percentage = limit_status.usage_percentage
                exact_usage = limit_status.spent_amount / limit_status.limit_amount
                exceeded_amount = max(
                    limit_status.spent_amount - limit_status.limit_amount,
                    Decimal("0.00"),
                )

            recommendations.append(
                (
                    SurvivalRecommendation(
                        category_id=row.category_id,
                        category_name=row.category_name,
                        spent_amount=row.spent_amount or Decimal("0.00"),
                        limit_amount=limit_amount,
                        exceeded_amount=exceeded_amount,
                        usage_percentage=usage_percentage,
                        message=(
                            f"Considere reduzir gastos em {row.category_name} "
                            "e evitar novos lancamentos nao essenciais nesta categoria."
                        ),
                    ),
                    exact_usage,
                )
            )

        sorted_recommendations = sorted(
            recommendations,
            key=lambda item: (
                -item[0].exceeded_amount,
                -item[1],
                -item[0].spent_amount,
                item[0].category_name,
            ),
        )
        return [item[0] for item in sorted_recommendations]

    def _get_highlighted_transaction_ids(
        self,
        current_user: User,
        month: str,
        category_ids: set[int],
    ) -> list[int]:
        if not category_ids:
            return []

        _, month_start, next_month_start = self._parse_month(month)
        statement = (
            select(Transaction.id)
            .where(
                Transaction.user_id == current_user.id,
                Transaction.type == "expense",
                Transaction.category_id.in_(category_ids),
                Transaction.date >= month_start,
                Transaction.date < next_month_start,
            )
            .order_by(Transaction.date.desc(), Transaction.id.desc())
        )
        return list(self.db.scalars(statement))

    @staticmethod
    def _build_trigger(status: BudgetLimitStatus) -> SurvivalTrigger:
        return SurvivalTrigger(
            scope="global" if status.category_id is None else "category",
            category_id=status.category_id,
            category_name=status.category_name,
            limit_amount=status.limit_amount,
            spent_amount=status.spent_amount,
            usage_percentage=status.usage_percentage,
        )

    @staticmethod
    def _inactive_response(
        month: str,
        activation_percentage: int,
        reason: str,
    ) -> SurvivalModeResponse:
        return SurvivalModeResponse(
            month=month,
            activation_percentage=activation_percentage,
            is_active=False,
            activation_reason=reason,
            trigger=None,
            recommendations=[],
            highlighted_transaction_ids=[],
        )

    @staticmethod
    def _parse_month(month: str):
        try:
            return parse_month_label(month)
        except ValueError as exc:
            raise BudgetServiceError(str(exc), 400) from exc
