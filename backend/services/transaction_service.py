from sqlalchemy.orm import Session

from schemas.transaction import TransactionCreate, TransactionUpdate


class TransactionService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_transaction(self, payload: TransactionCreate):
        raise NotImplementedError("Transaction creation has not been implemented yet.")

    def list_transactions(self):
        raise NotImplementedError("Transaction listing has not been implemented yet.")

    def get_transaction(self, transaction_id: int):
        raise NotImplementedError("Transaction retrieval has not been implemented yet.")

    def update_transaction(self, transaction_id: int, payload: TransactionUpdate):
        raise NotImplementedError("Transaction update has not been implemented yet.")

    def delete_transaction(self, transaction_id: int):
        raise NotImplementedError("Transaction deletion has not been implemented yet.")

