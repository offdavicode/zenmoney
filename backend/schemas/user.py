import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator


SPECIAL_CHARACTER_PATTERN = re.compile(r"[^A-Za-z0-9]")


class UserCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=7, max_length=128)

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, value: str) -> str:
        has_alphanumeric = any(char.isalnum() for char in value)
        has_special_character = bool(SPECIAL_CHARACTER_PATTERN.search(value))

        if not has_alphanumeric or not has_special_character:
            raise ValueError(
                "Password must contain at least one alphanumeric character and one special character."
            )

        if len(value.encode("utf-8")) > 72:
            raise ValueError("Password must have at most 72 bytes when encoded in UTF-8.")

        return value


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
    new_password: str = Field(min_length=7, max_length=128)

    @field_validator("new_password")
    @classmethod
    def validate_new_password_strength(cls, value: str) -> str:
        has_alphanumeric = any(char.isalnum() for char in value)
        has_special_character = bool(SPECIAL_CHARACTER_PATTERN.search(value))

        if not has_alphanumeric or not has_special_character:
            raise ValueError(
                "Password must contain at least one alphanumeric character and one special character."
            )

        if len(value.encode("utf-8")) > 72:
            raise ValueError("Password must have at most 72 bytes when encoded in UTF-8.")

        return value


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
