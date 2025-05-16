from fastapi import APIRouter, Depends
from fastapi_users import FastAPIUsers
from fastapi_users.authentication import JWTStrategy, AuthenticationBackend
from fastapi_users.db import SQLAlchemyUserDatabase
from sqlalchemy.orm import Session
from ...core.database import get_db, SessionLocal
from ...models.user import User
from ...schemas.user import UserRead, UserCreate, UserUpdate
from ...core.config import settings

# Configuração do banco para FastAPI Users
user_db = SQLAlchemyUserDatabase(User, SessionLocal())

def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(secret=settings.fastapi_users_secret, lifetime_seconds=3600)

auth_backend = AuthenticationBackend(
    name="jwt",
    transport=None,  # FastAPI Users 12+ exige transport explícito, mas para simplificar deixamos None
    get_strategy=get_jwt_strategy,
)

fastapi_users = FastAPIUsers[
    User,
    int
](
    user_db,
    [auth_backend],
)

router = APIRouter(tags=["users"])

router.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth/jwt",
    tags=["auth"],
)
router.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)
router.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["users"],
) 