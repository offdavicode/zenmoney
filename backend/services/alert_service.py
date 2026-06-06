from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from models.budget_alert import BudgetAlert
from models.user import User
from schemas.budget import BudgetAlertCheckResponse, BudgetAlertResponse, BudgetLimitStatus
from services.budget_service import BudgetService


THRESHOLD_STEP = 10
MAX_THRESHOLD = 100


class AlertService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def check_budget_alert(
        self,
        current_user: User,
        month: str | None = None,
    ) -> BudgetAlertCheckResponse:
        budget_status = BudgetService(self.db).get_budget_settings(current_user, month)
        candidates: list[BudgetAlertResponse] = []

        if budget_status.global_limit is not None:
            alert = self._process_limit_status(
                current_user=current_user,
                month=budget_status.month,
                status=budget_status.global_limit,
            )
            if alert is not None:
                candidates.append(alert)

        for category_limit in budget_status.category_limits:
            alert = self._process_limit_status(
                current_user=current_user,
                month=budget_status.month,
                status=category_limit,
            )
            if alert is not None:
                candidates.append(alert)

        if not candidates:
            return BudgetAlertCheckResponse(month=budget_status.month, alert=None)

        highest_alert = sorted(
            candidates,
            key=lambda item: (
                item.threshold_percent,
                item.usage_percentage,
                1 if item.scope == "global" else 0,
            ),
            reverse=True,
        )[0]
        self.db.commit()
        return BudgetAlertCheckResponse(month=budget_status.month, alert=highest_alert)

    def evaluate_survival_mode(self, user_id: int):
        raise NotImplementedError("Survival mode has not been implemented yet.")

    def _process_limit_status(
        self,
        current_user: User,
        month: str,
        status: BudgetLimitStatus,
    ) -> BudgetAlertResponse | None:
        highest_threshold = self._highest_crossed_threshold(status.usage_percentage)
        if highest_threshold is None:
            return None

        scope_key = self._scope_key(status.category_id)
        existing_thresholds = self._get_existing_thresholds(
            current_user=current_user,
            scope_key=scope_key,
            month=month,
            highest_threshold=highest_threshold,
        )
        new_thresholds = [
            threshold
            for threshold in range(THRESHOLD_STEP, highest_threshold + THRESHOLD_STEP, THRESHOLD_STEP)
            if threshold not in existing_thresholds
        ]

        if not new_thresholds:
            return None

        for threshold in new_thresholds:
            self.db.add(
                BudgetAlert(
                    user_id=current_user.id,
                    category_id=status.category_id,
                    scope_key=scope_key,
                    month=month,
                    threshold_percent=threshold,
                    limit_amount=status.limit_amount,
                    spent_amount=status.spent_amount,
                    usage_percentage=Decimal(str(status.usage_percentage)),
                )
            )

        return self._build_alert_response(
            month=month,
            status=status,
            threshold_percent=max(new_thresholds),
        )

    def _get_existing_thresholds(
        self,
        current_user: User,
        scope_key: str,
        month: str,
        highest_threshold: int,
    ) -> set[int]:
        statement = select(BudgetAlert.threshold_percent).where(
            BudgetAlert.user_id == current_user.id,
            BudgetAlert.scope_key == scope_key,
            BudgetAlert.month == month,
            BudgetAlert.threshold_percent <= highest_threshold,
        )
        return set(self.db.scalars(statement))

    def _build_alert_response(
        self,
        month: str,
        status: BudgetLimitStatus,
        threshold_percent: int,
    ) -> BudgetAlertResponse:
        scope = "global" if status.category_id is None else "category"
        return BudgetAlertResponse(
            month=month,
            scope=scope,
            category_id=status.category_id,
            category_name=status.category_name,
            threshold_percent=threshold_percent,
            limit_amount=status.limit_amount,
            spent_amount=status.spent_amount,
            usage_percentage=status.usage_percentage,
            message=self._build_message(status, threshold_percent),
        )

    @staticmethod
    def _highest_crossed_threshold(usage_percentage: float) -> int | None:
        if usage_percentage < THRESHOLD_STEP:
            return None
        threshold = int(usage_percentage // THRESHOLD_STEP) * THRESHOLD_STEP
        return min(threshold, MAX_THRESHOLD)

    @staticmethod
    def _scope_key(category_id: int | None) -> str:
        if category_id is None:
            return "global"
        return f"category:{category_id}"

    @staticmethod
    def _build_message(status: BudgetLimitStatus, threshold_percent: int) -> str:
        if status.category_id is None:
            return f"Voce atingiu {threshold_percent}% do limite mensal geral."
        return f"Voce atingiu {threshold_percent}% do limite de {status.category_name}."
