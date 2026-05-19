from sqlalchemy.orm import Session


class AlertService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_budget_status(self, user_id: int):
        raise NotImplementedError("Budget monitoring has not been implemented yet.")

    def evaluate_survival_mode(self, user_id: int):
        raise NotImplementedError("Survival mode has not been implemented yet.")

