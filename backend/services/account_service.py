from sqlalchemy.orm import Session

from models.user import User
from schemas.user import AccountDeleteRequest, AccountDeleteResponse
from utils.security import verify_password


class AccountServiceError(Exception):
    def __init__(self, message: str, status_code: int) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class AccountService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def delete_account(
        self,
        current_user: User,
        payload: AccountDeleteRequest,
    ) -> AccountDeleteResponse:
        if not verify_password(payload.current_password, current_user.password_hash):
            raise AccountServiceError("Current password is incorrect.", 401)

        self.db.delete(current_user)
        self.db.commit()
        return AccountDeleteResponse(
            message="Account and all associated data were permanently deleted."
        )
