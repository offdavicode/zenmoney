import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator


LOWERCASE_PATTERN = re.compile(r"[a-z]")
UPPERCASE_PATTERN = re.compile(r"[A-Z]")
DIGIT_PATTERN = re.compile(r"\d")
SPECIAL_CHARACTER_PATTERN = re.compile(r"[^A-Za-z0-9_]")
PASSWORD_STRENGTH_MESSAGE = (
    "Password must contain at least one uppercase letter, one lowercase letter, "
    "one number, and one special character."
)


def validate_password_strength(value: str) -> str:
    has_lowercase = bool(LOWERCASE_PATTERN.search(value))
    has_uppercase = bool(UPPERCASE_PATTERN.search(value))
    has_digit = bool(DIGIT_PATTERN.search(value))
    has_special_character = bool(SPECIAL_CHARACTER_PATTERN.search(value))

    if not all((has_lowercase, has_uppercase, has_digit, has_special_character)):
        raise ValueError(PASSWORD_STRENGTH_MESSAGE)

    if len(value.encode("utf-8")) > 72:
        raise ValueError("Password must have at most 72 bytes when encoded in UTF-8.")

    return value


class UserCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, value: str) -> str:
        return validate_password_strength(value)


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class UserProfileUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=100)
    email: EmailStr | None = None

    @model_validator(mode="after")
    def validate_at_least_one_field(self):
        if self.name is None and self.email is None:
            raise ValueError("At least one field must be provided to update the profile.")
        return self


class UserPasswordUpdate(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def validate_new_password_strength(cls, value: str) -> str:
        return validate_password_strength(value)


class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr

    model_config = ConfigDict(from_attributes=True)


class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int
    user: UserResponse


class LogoutResponse(BaseModel):
    message: str


class PasswordChangeResponse(BaseModel):
    message: str


class AccountDeleteRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)


class AccountDeleteResponse(BaseModel):
    message: str
