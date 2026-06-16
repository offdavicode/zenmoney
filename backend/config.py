import os
from dataclasses import dataclass


def _get_comma_separated_values(name: str, default: str) -> tuple[str, ...]:
    raw_value = os.getenv(name, default)
    return tuple(
        value.strip().rstrip("/")
        for value in raw_value.split(",")
        if value.strip()
    )


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "ZenMoney API")
    app_version: str = os.getenv("APP_VERSION", "2.0.0")
    api_prefix: str = os.getenv("API_PREFIX", "/api")
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./zenmoney_v2.db")
    secret_key: str = os.getenv("SECRET_KEY", "change-me-in-development")
    algorithm: str = os.getenv("ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    max_login_attempts: int = int(os.getenv("MAX_LOGIN_ATTEMPTS", "5"))
    account_lock_minutes: int = int(os.getenv("ACCOUNT_LOCK_MINUTES", "15"))
    frontend_origins: tuple[str, ...] = _get_comma_separated_values(
        "FRONTEND_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000",
    )


settings = Settings()
