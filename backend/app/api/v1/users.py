import logging
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from ...core.config import settings
from ...core.database import get_db
from ...core.limiter import limiter
from ...core.security import (
    authenticate_user,
    create_token_pair,
    rotate_refresh_token,
    revoke_user_tokens,
    get_current_user,
    get_password_hash,
)
from ...models.user import User
from ...schemas.user import (
    User as UserSchema,
    UserCreate,
    UserList,
    TokenResponse,
    RefreshTokenRequest,
)

router = APIRouter(tags=["users"])
logger = logging.getLogger(__name__)


def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()


@router.post("/token", response_model=TokenResponse)
@limiter.limit("20/minute")
async def login_for_access_token(
    request: Request,
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    trace_id = getattr(request.state, "trace_id", "")
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        logger.warning("Tentativa de login inválida", extra={"trace_id": trace_id})
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Aqui a mágica acontece: access + refresh
    access_token, refresh_token = create_token_pair(db, user)
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
    db: Session = Depends(get_db)
):
    """
    Renova o par de tokens usando um refresh token válido.

    O refresh token usado é revogado e um novo par é emitido (rotação).
    Se um refresh token já revogado for apresentado, TODOS os tokens
    do usuário são revogados por segurança (detecção de roubo).
    """
    result = rotate_refresh_token(db, body.refresh_token)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token inválido ou expirado",
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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Revoga todos os refresh tokens do usuário (logout global).
    O access token atual continua válido até expirar.
    """
    count = revoke_user_tokens(db, current_user.id)
    return {"message": "Logout realizado com sucesso", "tokens_revogados": count}


@router.post("/register", response_model=UserSchema)
@limiter.limit("20/minute")
def register_user(
    request: Request,
    response: Response,
    user: UserCreate,
    db: Session = Depends(get_db),
):
    trace_id = getattr(request.state, "trace_id", "")
    db_user = get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(
            status_code=400,
            detail="Email já cadastrado"
        )
    # Verificar username duplicado
    if user.username:
        existing_username = db.query(User).filter(User.username == user.username).first()
        if existing_username:
            raise HTTPException(
                status_code=400,
                detail="Nome de usuário já cadastrado"
            )
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        full_name=user.full_name,
        is_superuser=user.is_superuser if user.is_superuser else False
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    logger.info("Usuário criado", extra={"user_id": db_user.id, "trace_id": trace_id})
    return db_user


@router.get("/me", response_model=UserSchema)
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def read_users_me(
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_user)
):
    return current_user


@router.get("/", response_model=UserList)
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def list_users(
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Lista todos os usuários do sistema. Requer autenticação."""
    users = db.query(User).order_by(User.id).all()
    return UserList(users=users, total=len(users))
