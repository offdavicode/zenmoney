from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from models.category import Category
from models.recurrence import Recurrence
from models.transaction import Transaction
from models.user import User
from schemas.recurrence import RecurrenceCreate, RecurrenceRunDueResponse, RecurrenceUpdate
from utils.date_utils import now_in_brasilia
from utils.emotion_rules import normalize_emotion
from utils.recurrence_dates import first_scheduled_on_or_after, next_scheduled_date


class RecurrenceServiceError(Exception):
    def __init__(self, message: str, status_code: int) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class RecurrenceService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_recurrence(self, current_user: User, payload: RecurrenceCreate) -> Recurrence:
        category = self._resolve_category(current_user, payload.category_id, payload.type)
        day_of_month = payload.day_of_month or payload.start_date.day
        next_run_date = first_scheduled_on_or_after(payload.start_date, day_of_month)
        self._ensure_occurrence_within_end_date(next_run_date, payload.end_date)

        recurrence = Recurrence(
            user_id=current_user.id,
            category_id=category.id if category is not None else None,
            type=payload.type,
            amount=payload.amount,
            description=self._normalize_description(payload.description),
            emotion=self._resolve_emotion(payload.type, payload.emotion),
            frequency=payload.frequency,
            day_of_month=day_of_month,
            start_date=payload.start_date,
            end_date=payload.end_date,
            next_run_date=next_run_date,
            is_active=True,
        )
        self.db.add(recurrence)
        self.db.commit()
        self.db.refresh(recurrence)
        return recurrence

    def list_recurrences(self, current_user: User) -> list[Recurrence]:
        statement = (
            select(Recurrence)
            .where(Recurrence.user_id == current_user.id)
            .order_by(Recurrence.is_active.desc(), Recurrence.next_run_date, Recurrence.id)
        )
        return list(self.db.scalars(statement))

    def get_recurrence(self, current_user: User, recurrence_id: int) -> Recurrence:
        return self._get_owned_recurrence(current_user, recurrence_id)

    def update_recurrence(
        self,
        current_user: User,
        recurrence_id: int,
        payload: RecurrenceUpdate,
    ) -> Recurrence:
        recurrence = self._get_owned_recurrence(current_user, recurrence_id)
        update_data = payload.model_dump(exclude_unset=True)

        next_type = update_data.get("type", recurrence.type)
        next_category_id = update_data.get("category_id", recurrence.category_id)
        category = self._resolve_category(current_user, next_category_id, next_type)

        next_start_date = update_data.get("start_date", recurrence.start_date)
        next_end_date = update_data.get("end_date", recurrence.end_date)
        next_day_of_month = update_data.get("day_of_month", recurrence.day_of_month)
        next_frequency = update_data.get("frequency", recurrence.frequency)
        if next_day_of_month is None:
            next_day_of_month = next_start_date.day

        if next_end_date is not None and next_end_date < next_start_date:
            raise RecurrenceServiceError("A data de fim deve ser posterior ou igual à data de início.", 400)

        schedule_changed = (
            next_start_date != recurrence.start_date
            or next_end_date != recurrence.end_date
            or next_day_of_month != recurrence.day_of_month
            or next_frequency != recurrence.frequency
        )
        if schedule_changed:
            first_occurrence = first_scheduled_on_or_after(next_start_date, next_day_of_month)
            self._ensure_occurrence_within_end_date(first_occurrence, next_end_date)

            reference_date = max(next_start_date, now_in_brasilia().date())
            next_run_date = first_scheduled_on_or_after(reference_date, next_day_of_month)
            recurrence.next_run_date = next_run_date
            if next_end_date is not None and next_run_date > next_end_date:
                recurrence.is_active = False

        recurrence.category_id = category.id if category is not None else None
        recurrence.type = next_type
        recurrence.start_date = next_start_date
        recurrence.end_date = next_end_date
        recurrence.day_of_month = next_day_of_month

        recurrence.frequency = next_frequency
        if "amount" in update_data:
            recurrence.amount = update_data["amount"]
        if "description" in update_data:
            recurrence.description = self._normalize_description(update_data["description"])

        next_emotion = update_data.get("emotion", recurrence.emotion)
        recurrence.emotion = self._resolve_emotion(next_type, next_emotion)

        from sqlalchemy import update as sa_update, delete as sa_delete
        today = now_in_brasilia().date()

        if schedule_changed:
            # Only strictly future generated transactions are disposable.
            # Today's transaction is already part of the user's current records.
            self.db.execute(
                sa_delete(Transaction)
                .where(Transaction.recurrence_id == recurrence.id, Transaction.date > today)
            )
        else:
            # If only attributes changed (amount, description, etc.), propagate to future transactions
            update_values = {}
            if "category_id" in update_data:
                update_values["category_id"] = category.id if category else None
            if "type" in update_data:
                update_values["type"] = next_type
            if "amount" in update_data:
                update_values["amount"] = update_data["amount"]
            if "description" in update_data:
                update_values["description"] = recurrence.description
            if "emotion" in update_data:
                update_values["emotion"] = recurrence.emotion

            if update_values:
                self.db.execute(
                    sa_update(Transaction)
                    .where(Transaction.recurrence_id == recurrence.id, Transaction.date > today)
                    .values(**update_values)
                )

        self.db.commit()
        self.db.refresh(recurrence)
        return recurrence

    def pause_recurrence(self, current_user: User, recurrence_id: int) -> Recurrence:
        recurrence = self._get_owned_recurrence(current_user, recurrence_id)
        recurrence.is_active = False

        from sqlalchemy import delete as sa_delete
        today = now_in_brasilia().date()
        self.db.execute(
            sa_delete(Transaction)
            .where(Transaction.recurrence_id == recurrence.id, Transaction.date > today)
        )

        self.db.commit()
        self.db.refresh(recurrence)
        return recurrence

    def resume_recurrence(self, current_user: User, recurrence_id: int) -> Recurrence:
        recurrence = self._get_owned_recurrence(current_user, recurrence_id)
        if recurrence.is_active:
            return recurrence

        reference_date = max(recurrence.start_date, now_in_brasilia().date())
        next_run_date = first_scheduled_on_or_after(reference_date, recurrence.day_of_month)
        if recurrence.end_date is not None and next_run_date > recurrence.end_date:
            raise RecurrenceServiceError(
                "A recorrência não pode ser retomada porque não há ocorrências futuras antes da sua data de término.",
                400,
            )

        recurrence.next_run_date = next_run_date
        recurrence.is_active = True
        self.db.commit()
        self.db.refresh(recurrence)
        return recurrence

    def delete_recurrence(self, current_user: User, recurrence_id: int) -> None:
        recurrence = self._get_owned_recurrence(current_user, recurrence_id)
        
        from sqlalchemy import delete as sa_delete
        today = now_in_brasilia().date()
        self.db.execute(
            sa_delete(Transaction)
            .where(Transaction.recurrence_id == recurrence.id, Transaction.date > today)
        )
        
        self.db.delete(recurrence)
        self.db.commit()

    def run_due(
        self,
        current_user: User,
        through_date: date | None = None,
    ) -> RecurrenceRunDueResponse:
        effective_date = through_date or now_in_brasilia().date()
        statement = (
            select(Recurrence)
            .where(
                Recurrence.user_id == current_user.id,
                Recurrence.is_active.is_(True),
                Recurrence.next_run_date <= effective_date,
            )
            .order_by(Recurrence.next_run_date, Recurrence.id)
        )
        recurrences = list(self.db.scalars(statement))
        generated_transactions: list[Transaction] = []

        for recurrence in recurrences:
            while recurrence.next_run_date <= effective_date:
                occurrence_date = recurrence.next_run_date
                if recurrence.end_date is not None and occurrence_date > recurrence.end_date:
                    recurrence.is_active = False
                    break

                existing_transaction = self.db.scalar(
                    select(Transaction).where(
                        Transaction.recurrence_id == recurrence.id,
                        Transaction.date == occurrence_date,
                    )
                )
                if existing_transaction is None:
                    transaction = Transaction(
                        user_id=current_user.id,
                        category_id=recurrence.category_id,
                        recurrence_id=recurrence.id,
                        is_recurring=True,
                        type=recurrence.type,
                        amount=recurrence.amount,
                        date=occurrence_date,
                        description=recurrence.description,
                        emotion=recurrence.emotion,
                    )
                    self.db.add(transaction)
                    generated_transactions.append(transaction)

                recurrence.next_run_date = next_scheduled_date(
                    occurrence_date,
                    recurrence.day_of_month,
                )
                if (
                    recurrence.end_date is not None
                    and recurrence.next_run_date > recurrence.end_date
                ):
                    recurrence.is_active = False
                    break

        self.db.commit()
        for transaction in generated_transactions:
            self.db.refresh(transaction)

        return RecurrenceRunDueResponse(
            through_date=effective_date,
            generated_count=len(generated_transactions),
            generated_transactions=generated_transactions,
        )

    def _get_owned_recurrence(self, current_user: User, recurrence_id: int) -> Recurrence:
        recurrence = self.db.scalar(
            select(Recurrence).where(
                Recurrence.id == recurrence_id,
                Recurrence.user_id == current_user.id,
            )
        )
        if recurrence is None:
            raise RecurrenceServiceError("Recorrência não encontrada.", 404)
        return recurrence

    def _resolve_category(
        self,
        current_user: User,
        category_id: int | None,
        transaction_type: str,
    ) -> Category | None:
        if category_id is None:
            return None

        category = self.db.scalar(
            select(Category).where(
                Category.id == category_id,
                Category.type == transaction_type,
                (Category.user_id == current_user.id) | (Category.user_id.is_(None)),
            )
        )
        if category is None:
            raise RecurrenceServiceError(
                "Categoria não encontrada ou incompatível com o tipo de recorrência.",
                404,
            )
        return category

    @staticmethod
    def _ensure_occurrence_within_end_date(
        next_run_date: date,
        end_date: date | None,
    ) -> None:
        if end_date is not None and next_run_date > end_date:
            raise RecurrenceServiceError(
                "O agendamento não possui nenhuma ocorrência na data de término ou antes dela.",
                400,
            )

    @staticmethod
    def _normalize_description(description: str | None) -> str | None:
        if description is None:
            return None
        normalized = description.strip()
        return normalized or None

    @staticmethod
    def _resolve_emotion(transaction_type: str, emotion: str | None) -> str:
        return normalize_emotion(emotion)
