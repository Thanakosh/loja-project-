from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from ..core.user_permissions import normalize_allowed_tabs


class UserBase(BaseModel):
    email: EmailStr
    username: Optional[str] = None
    full_name: Optional[str] = None
    is_active: bool = True
    is_superuser: bool = False
    allowed_tabs: list[str] = Field(default_factory=list)

    @field_validator("username", "full_name", mode="before")
    @classmethod
    def strip_optional_text(cls, value: Optional[str]) -> Optional[str]:
        if value is None or not isinstance(value, str):
            return value

        cleaned = value.strip()
        return cleaned or None

    @field_validator("allowed_tabs", mode="before")
    @classmethod
    def validate_allowed_tabs(cls, value: object) -> list[str]:
        return normalize_allowed_tabs(value)


class UserCreate(UserBase):
    password: str


class UserUpdate(UserBase):
    password: Optional[str] = None


class User(UserBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class UserList(BaseModel):
    users: list["User"]
    total: int


class UserInDBBase(UserBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class UserInDB(UserInDBBase):
    hashed_password: str


class TokenResponse(BaseModel):
    """Resposta de autenticacao com access e refresh tokens."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshTokenRequest(BaseModel):
    """Request para renovar tokens."""

    refresh_token: str
