from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional

class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    is_active: Optional[bool] = True
    is_superuser: bool = False

class UserCreate(UserBase):
    password: str

class UserUpdate(UserBase):
    password: Optional[str] = None

class User(UserBase):
    id: str

    model_config = ConfigDict(from_attributes=True)

class UserInDBBase(UserBase):
    id: int

    model_config = ConfigDict(from_attributes=True)

class UserInDB(UserInDBBase):
    hashed_password: str
