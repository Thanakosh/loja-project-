import logging

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
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
from ...core.user_permissions import require_superuser
from ...models.user import User
from ...schemas.user import (
    RefreshTokenRequest,
    TokenResponse,
    User as UserSchema,
    UserCreate,
    UserList,
    UserUpdate,
)

router = APIRouter(tags=["users"])
logger = logging.getLogger(__name__)


async def get_user_by_email(db: AsyncSession, email: str):
    return (await db.execute(select(User).where(User.email == email))).scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: int) -> User:
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario nao encontrado")
    return user


async def ensure_unique_user_fields(
    db: AsyncSession,
    *,
    email: str,
    username: str | None,
    exclude_user_id: int | None = None,
) -> None:
    email_query = select(User).where(User.email == email)
    if exclude_user_id is not None:
        email_query = email_query.where(User.id != exclude_user_id)

    existing_email = (await db.execute(email_query)).scalar_one_or_none()
    if existing_email:
        raise HTTPException(status_code=400, detail="Email ja cadastrado")

    if username:
        username_query = select(User).where(User.username == username)
        if exclude_user_id is not None:
            username_query = username_query.where(User.id != exclude_user_id)

        existing_username = (await db.execute(username_query)).scalar_one_or_none()
        if existing_username:
            raise HTTPException(status_code=400, detail="Nome de usuario ja cadastrado")


async def count_superusers(db: AsyncSession, *, active_only: bool = False) -> int:
    query = select(func.count()).select_from(User).where(User.is_superuser.is_(True))
    if active_only:
        query = query.where(User.is_active.is_(True))

    return int((await db.scalar(query)) or 0)


async def ensure_admin_guardrails(
    db: AsyncSession,
    *,
    current_admin: User,
    target_user: User,
    next_is_superuser: bool,
    next_is_active: bool,
) -> None:
    if current_admin.id == target_user.id:
        if not next_is_active:
            raise HTTPException(status_code=400, detail="Voce nao pode desativar o proprio usuario")
        if target_user.is_superuser and not next_is_superuser:
            raise HTTPException(
                status_code=400,
                detail="Voce nao pode remover o proprio perfil de administrador",
            )

    if target_user.is_superuser and not next_is_superuser:
        if await count_superusers(db) <= 1:
            raise HTTPException(
                status_code=400,
                detail="Nao e permitido remover o ultimo administrador do sistema",
            )
        if target_user.is_active and await count_superusers(db, active_only=True) <= 1:
            raise HTTPException(
                status_code=400,
                detail="Nao e permitido remover o ultimo administrador ativo do sistema",
            )

    if target_user.is_superuser and target_user.is_active and not next_is_active:
        if await count_superusers(db, active_only=True) <= 1:
            raise HTTPException(
                status_code=400,
                detail="Nao e permitido desativar o ultimo administrador ativo do sistema",
            )


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
        logger.warning("Tentativa de login invalida", extra={"trace_id": trace_id})
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
    result = await rotate_refresh_token_async(db, body.refresh_token)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token invalido ou expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user, access_token, new_refresh = result
    _ = user

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
    count = await revoke_user_tokens_async(db, current_user.id)
    return {"message": "Logout realizado com sucesso", "tokens_revogados": count}


@router.post("/register", response_model=UserSchema)
@limiter.limit("20/minute")
async def register_user(
    request: Request,
    response: Response,
    user: UserCreate,
    db: AsyncSession = Depends(get_async_db),
    current_admin: User = Depends(require_superuser),
):
    trace_id = getattr(request.state, "trace_id", "")
    _ = current_admin
    await ensure_unique_user_fields(db, email=user.email, username=user.username)

    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=get_password_hash(user.password),
        full_name=user.full_name,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
        allowed_tabs=[] if user.is_superuser else user.allowed_tabs,
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    logger.info("Usuario criado", extra={"user_id": db_user.id, "trace_id": trace_id})
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
    current_user: User = Depends(require_superuser),
    db: AsyncSession = Depends(get_async_db),
):
    _ = current_user
    users = (await db.execute(select(User).order_by(User.id))).scalars().all()
    return UserList(users=users, total=len(users))


@router.put("/{user_id}", response_model=UserSchema)
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def update_user(
    request: Request,
    response: Response,
    user_id: int,
    payload: UserUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_admin: User = Depends(require_superuser),
):
    trace_id = getattr(request.state, "trace_id", "")
    target_user = await get_user_by_id(db, user_id)

    await ensure_unique_user_fields(
        db,
        email=payload.email,
        username=payload.username,
        exclude_user_id=target_user.id,
    )
    await ensure_admin_guardrails(
        db,
        current_admin=current_admin,
        target_user=target_user,
        next_is_superuser=payload.is_superuser,
        next_is_active=payload.is_active,
    )

    target_user.username = payload.username
    target_user.email = payload.email
    target_user.full_name = payload.full_name
    target_user.is_active = payload.is_active
    target_user.is_superuser = payload.is_superuser
    target_user.allowed_tabs = [] if payload.is_superuser else payload.allowed_tabs

    if payload.password:
        target_user.hashed_password = get_password_hash(payload.password)

    await db.commit()

    if not target_user.is_active:
        await revoke_user_tokens_async(db, target_user.id)

    await db.refresh(target_user)
    logger.info(
        "Usuario atualizado",
        extra={"user_id": target_user.id, "admin_id": current_admin.id, "trace_id": trace_id},
    )
    return target_user


@router.delete("/{user_id}")
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def delete_user(
    request: Request,
    response: Response,
    user_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_admin: User = Depends(require_superuser),
):
    trace_id = getattr(request.state, "trace_id", "")
    target_user = await get_user_by_id(db, user_id)

    await ensure_admin_guardrails(
        db,
        current_admin=current_admin,
        target_user=target_user,
        next_is_superuser=False,
        next_is_active=False,
    )
    await revoke_user_tokens_async(db, target_user.id)

    try:
        await db.delete(target_user)
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        logger.warning(
            "Falha ao excluir usuario com historico vinculado",
            extra={"user_id": target_user.id, "admin_id": current_admin.id, "trace_id": trace_id},
        )
        raise HTTPException(
            status_code=400,
            detail="Usuario possui historico vinculado e nao pode ser excluido permanentemente. Desative-o em vez disso.",
        ) from exc

    logger.info(
        "Usuario excluido",
        extra={"user_id": user_id, "admin_id": current_admin.id, "trace_id": trace_id},
    )
    return {"message": "Usuario excluido com sucesso"}
