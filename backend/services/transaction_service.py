from sqlalchemy import select
from sqlalchemy.orm import Session

from models.category import Category
from models.transaction import Transaction
from models.user import User
from schemas.transaction import TransactionCreate, TransactionUpdate


class TransactionServiceError(Exception):
    def __init__(self, message: str, status_code: int) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class TransactionService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_transaction(self, current_user: User, payload: TransactionCreate) -> Transaction:
        category = self._resolve_category(
            current_user=current_user,
            category_id=payload.category_id,
            transaction_type=payload.type,
        )

        transaction = Transaction(
            user_id=current_user.id,
            category_id=category.id if category is not None else None,
            type=payload.type,
            amount=payload.amount,
            date=payload.date,
            description=self._normalize_description(payload.description),
            emotion=self._normalize_emotion(payload.emotion),
        )
        self.db.add(transaction)
        self.db.commit()
        self.db.refresh(transaction)
        return transaction

    def list_transactions(self, current_user: User) -> list[Transaction]:
        statement = (
            select(Transaction)
            .where(Transaction.user_id == current_user.id)
            .order_by(Transaction.date.desc(), Transaction.id.desc())
        )
        return list(self.db.scalars(statement))

    def get_transaction(self, current_user: User, transaction_id: int) -> Transaction:
        transaction = self._get_owned_transaction(current_user, transaction_id)
        return transaction

    def update_transaction(
        self,
        current_user: User,
        transaction_id: int,
        payload: TransactionUpdate,
    ) -> Transaction:
        transaction = self._get_owned_transaction(current_user, transaction_id)
        update_data = payload.model_dump(exclude_unset=True)

        next_type = update_data.get("type", transaction.type)
        next_category_id = transaction.category_id

        if "category_id" in update_data:
            if update_data["category_id"] is None:
                next_category_id = None
            else:
                next_category_id = update_data["category_id"]

        category = self._resolve_category(
            current_user=current_user,
            category_id=next_category_id,
            transaction_type=next_type,
        )

        if "type" in update_data:
            transaction.type = update_data["type"]
        if "amount" in update_data:
            transaction.amount = update_data["amount"]
        if "date" in update_data:
            transaction.date = update_data["date"]
        if "description" in update_data:
            transaction.description = self._normalize_description(update_data["description"])
        if "emotion" in update_data:
            transaction.emotion = self._normalize_emotion(update_data["emotion"])
        if "category_id" in update_data:
            transaction.category_id = category.id if category is not None else None

        self.db.commit()
        self.db.refresh(transaction)
        return transaction

    def delete_transaction(self, current_user: User, transaction_id: int) -> None:
        transaction = self._get_owned_transaction(current_user, transaction_id)
        self.db.delete(transaction)
        self.db.commit()

    def _get_owned_transaction(self, current_user: User, transaction_id: int) -> Transaction:
        statement = select(Transaction).where(
            Transaction.id == transaction_id,
            Transaction.user_id == current_user.id,
        )
        transaction = self.db.scalar(statement)
        if transaction is None:
            raise TransactionServiceError("Transaction not found.", 404)
        return transaction

    def _resolve_category(
        self,
        current_user: User,
        category_id: int | None,
        transaction_type: str,
    ) -> Category | None:
        if category_id is None:
            return None

        statement = select(Category).where(
            Category.id == category_id,
            Category.type == transaction_type,
            (Category.user_id == current_user.id) | (Category.user_id.is_(None)),
        )
        category = self.db.scalar(statement)
        if category is None:
            raise TransactionServiceError(
                "Category not found or incompatible with the transaction type.",
                404,
            )
        return category

    @staticmethod
    def _normalize_description(description: str | None) -> str | None:
        if description is None:
            return None

        normalized = description.strip()
        return normalized or None

    @staticmethod
    def _normalize_emotion(emotion: str | None) -> str:
        if emotion is None:
            return "not_specified"

        normalized = emotion.strip()
        return normalized or "not_specified"
