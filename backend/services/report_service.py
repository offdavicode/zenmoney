from sqlalchemy.orm import Session


class ReportService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_summary(self, user_id: int | None = None):
        raise NotImplementedError("Summary report has not been implemented yet.")

    def get_by_emotion(self, user_id: int | None = None):
        raise NotImplementedError("Emotion report has not been implemented yet.")

    def get_by_category(self, user_id: int | None = None):
        raise NotImplementedError("Category report has not been implemented yet.")

    def get_spending_triggers(self, user_id: int | None = None):
        raise NotImplementedError("Spending trigger report has not been implemented yet.")

