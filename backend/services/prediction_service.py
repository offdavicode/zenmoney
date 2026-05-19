from sqlalchemy.orm import Session


class PredictionService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def predict_month_end_balance(self, user_id: int):
        raise NotImplementedError("Balance prediction has not been implemented yet.")

