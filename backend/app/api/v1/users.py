import logging

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.config import settings
from ...core.database import get_async_db
from ...core.limiter import limiter
from ...core.security import (
    authenticate_user_async,
    create_token_pair_async,
    get_current_user_async,
    get_password_hash,
    revoke_user_tokens_async,
    rotate_refresh_token_async,
)
from ...models.user import User
from ...schemas.user import (
    RefreshTokenRequest,
    TokenResponse,
    User as UserSchema,
    UserCreate,
    UserList,
)

router = APIRouter(tags=["users"])
logger = logging.getLogger(__name__)


async def get_user_by_email(db: AsyncSession, email: str):
    return (await db.execute(select(User).where(User.email == email))).scalar_one_or_none()


@router.post("/token", response_model=TokenResponse)
@limiter.limit("20/minute")
async def login_for_access_token(
    request: Request,
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_async_db),
):
    trace_id = getattr(request.state, "trace_id", "")
    user = await authenticate_user_async(db, form_data.username, form_data.password)
    if not user:
        logger.warning("Tentativa de login invÃ¡lida", extra={"trace_id": trace_id})
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token, refresh_token = await create_token_pair_async(db, user)
    logger.info("Login bem-sucedido", extra={"user_id": user.id, "trace_id": trace_id})

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/refresh", response_model=TokenResponse)
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def refresh_access_token(
    request: Request,
    response: Response,
    body: RefreshTokenRequest,
    db: AsyncSession = Depends(get_async_db),
):
    """
    Renova o par de tokens usando um refresh token vÃ¡lido.

    O refresh token usado Ã© revogado e um novo par Ã© emitido (rotaÃ§Ã£o).
    Se um refresh token jÃ¡ revogado for apresentado, TODOS os tokens
    do usuÃ¡rio sÃ£o revogados por seguranÃ§a (detecÃ§Ã£o de roubo).
    """
    result = await rotate_refresh_token_async(db, body.refresh_token)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token invÃ¡lido ou expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user, access_token, new_refresh = result

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/logout")
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def logout(
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Revoga todos os refresh tokens do usuÃ¡rio (logout global).
    O access token atual continua vÃ¡lido atÃ© expirar.
    """
    count = await revoke_user_tokens_async(db, current_user.id)
    return {"message": "Logout realizado com sucesso", "tokens_revogados": count}


@router.post("/register", response_model=UserSchema)
@limiter.limit("20/minute")
async def register_user(
    request: Request,
    response: Response,
    user: UserCreate,
    db: AsyncSession = Depends(get_async_db),
):
    trace_id = getattr(request.state, "trace_id", "")
    db_user = await get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email jÃ¡ cadastrado")
    if user.username:
        existing_username = (
            await db.execute(select(User).where(User.username == user.username))
        ).scalar_one_or_none()
        if existing_username:
            raise HTTPException(status_code=400, detail="Nome de usuÃ¡rio jÃ¡ cadastrado")

    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        full_name=user.full_name,
        is_superuser=user.is_superuser if user.is_superuser else False,
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    logger.info("UsuÃ¡rio criado", extra={"user_id": db_user.id, "trace_id": trace_id})
    return db_user


@router.get("/me", response_model=UserSchema)
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def read_users_me(
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_user_async),
):
    return current_user


@router.get("/", response_model=UserList)
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def list_users(
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_async_db),
):
    """Lista todos os usuÃ¡rios do sistema. Requer autenticaÃ§Ã£o."""
    users = (await db.execute(select(User).order_by(User.id))).scalars().all()
    return UserList(users=users, total=len(users))
