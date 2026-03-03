from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional

class UserBase(BaseModel):
    email: EmailStr
    username: Optional[str] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = True
    is_superuser: bool = False

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
    """Resposta de autenticação com access e refresh tokens."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # segundos até expiração do access token


class RefreshTokenRequest(BaseModel):
    """Request para renovar tokens."""
    refresh_token: str
