from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from config import settings
from models.revoked_token import RevokedToken
from models.user import User
from schemas.user import (
    AccessTokenResponse,
    LogoutResponse,
    PasswordChangeResponse,
    UserCreate,
    UserLogin,
    UserPasswordUpdate,
    UserProfileUpdate,
)
from utils.security import create_access_token, decode_access_token, hash_password, verify_password


class AuthServiceError(Exception):
    def __init__(self, message: str, status_code: int) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def register_user(self, payload: UserCreate) -> User:
        normalized_email = payload.email.strip().lower()

        existing_user = self.db.scalar(
            select(User).where(User.email == normalized_email)
        )
        if existing_user is not None:
            raise AuthServiceError("A user with this e-mail already exists.", 409)

        user = User(
            name=payload.name.strip(),
            email=normalized_email,
            password_hash=hash_password(payload.password),
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def login_user(self, payload: UserLogin) -> AccessTokenResponse:
        normalized_email = payload.email.strip().lower()
        user = self.db.scalar(select(User).where(User.email == normalized_email))

        if user is None:
            raise AuthServiceError("Invalid e-mail or password.", 401)

        now = datetime.now(timezone.utc)
        if user.locked_until is not None:
            locked_until = self._ensure_utc(user.locked_until)
            if locked_until > now:
                raise AuthServiceError("Access temporarily blocked. Try again later.", 423)
            user.locked_until = None
            user.failed_login_attempts = 0
            self.db.commit()

        if not verify_password(payload.password, user.password_hash):
            self._register_failed_login_attempt(user)
            raise AuthServiceError("Invalid e-mail or password.", 401)

        user.failed_login_attempts = 0
        user.locked_until = None
        self.db.commit()
        self.db.refresh(user)

        access_token = create_access_token(subject=str(user.id))
        token_payload = decode_access_token(access_token)

        return AccessTokenResponse(
            access_token=access_token,
            expires_in=settings.access_token_expire_minutes * 60,
            user=user,
        )

    def logout_user(self, token: str) -> LogoutResponse:
        try:
            payload = decode_access_token(token)
        except ValueError as exc:
            raise AuthServiceError(str(exc), 401) from exc

        token_jti = payload.get("jti")
        subject = payload.get("sub")
        expires_at = payload.get("exp")

        if token_jti is None or subject is None or expires_at is None:
            raise AuthServiceError("Invalid authentication token.", 401)

        existing_revocation = self.db.scalar(
            select(RevokedToken).where(RevokedToken.token_jti == token_jti)
        )
        if existing_revocation is None:
            revoked_token = RevokedToken(
                token_jti=token_jti,
                user_id=int(subject),
                expires_at=datetime.fromtimestamp(expires_at, tz=timezone.utc).replace(tzinfo=None),
            )
            self.db.add(revoked_token)
            self.db.commit()

        return LogoutResponse(message="Logout completed successfully.")

    def update_profile(self, current_user: User, payload: UserProfileUpdate) -> User:
        has_changes = False

        if payload.name is not None:
            normalized_name = payload.name.strip()
            if normalized_name != current_user.name:
                current_user.name = normalized_name
                has_changes = True

        if payload.email is not None:
            normalized_email = payload.email.strip().lower()
            if normalized_email != current_user.email:
                existing_user = self.db.scalar(
                    select(User).where(
                        User.email == normalized_email,
                        User.id != current_user.id,
                    )
                )
                if existing_user is not None:
                    raise AuthServiceError("A user with this e-mail already exists.", 409)

                current_user.email = normalized_email
                has_changes = True

        if not has_changes:
            return current_user

        self.db.commit()
        self.db.refresh(current_user)
        return current_user

    def change_password(
        self,
        current_user: User,
        payload: UserPasswordUpdate,
    ) -> PasswordChangeResponse:
        if not verify_password(payload.current_password, current_user.password_hash):
            raise AuthServiceError("Current password is incorrect.", 401)

        if payload.current_password == payload.new_password:
            raise AuthServiceError(
                "The new password must be different from the current password.",
                400,
            )

        current_user.password_hash = hash_password(payload.new_password)
        self.db.commit()
        self.db.refresh(current_user)

        return PasswordChangeResponse(message="Password updated successfully.")

    def _register_failed_login_attempt(self, user: User) -> None:
        user.failed_login_attempts += 1

        if user.failed_login_attempts >= settings.max_login_attempts:
            lock_until = datetime.now(timezone.utc) + timedelta(
                minutes=settings.account_lock_minutes
            )
            user.locked_until = lock_until.replace(tzinfo=None)
            user.failed_login_attempts = 0

        self.db.commit()

    @staticmethod
    def _ensure_utc(value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
