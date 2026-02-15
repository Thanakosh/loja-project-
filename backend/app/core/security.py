from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
import hashlib
import secrets
import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from .config import settings
from .database import get_db
from ..models.user import User
from ..models.refresh_token import RefreshToken

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/users/token")
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="/api/v1/users/token", auto_error=False)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def len_b_str(s: str) -> int:
    return len(s)


def authenticate_user(db: Session, email: str, password: str):
    """Autentica usuário por email e senha."""
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "jti": str(uuid.uuid4())})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def _hash_token(token: str) -> str:
    """Hash do refresh token para armazenamento seguro."""
    return hashlib.sha256(token.encode()).hexdigest()


def create_token_pair(
    db: Session,
    user: User,
) -> Tuple[str, str]:
    """
    Cria um par access_token + refresh_token.

    Returns:
        Tuple[str, str]: (access_token, refresh_token_raw)
    """
    # Access token (JWT, curto)
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    # Refresh token (opaco, longo)
    refresh_token_raw = secrets.token_urlsafe(64)
    refresh_token_hash = _hash_token(refresh_token_raw)

    db_refresh = RefreshToken(
        token_hash=refresh_token_hash,
        user_id=user.id,
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add(db_refresh)
    db.commit()

    return access_token, refresh_token_raw


def rotate_refresh_token(
    db: Session,
    raw_token: str,
) -> Optional[Tuple[User, str, str]]:
    """
    Valida e rotaciona um refresh token.

    - Revoga o token antigo
    - Cria novo par (access + refresh)
    - Detecta reuso de token já revogado (possível roubo)

    Returns:
        Tuple[User, access_token, new_refresh_token] ou None se inválido
    """
    token_hash = _hash_token(raw_token)

    db_token = db.query(RefreshToken).filter(
        RefreshToken.token_hash == token_hash
    ).first()

    if not db_token:
        return None

    # Token já revogado → possível roubo! Revogar TODA a família
    if db_token.revoked:
        _revoke_all_user_tokens(db, db_token.user_id)
        return None

    # Token expirado
    expires_at = db_token.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if expires_at < datetime.now(timezone.utc):
        db_token.revoked = True
        db_token.revoked_at = datetime.now(timezone.utc)
        db.commit()
        return None

    # Revogar o token atual
    db_token.revoked = True
    db_token.revoked_at = datetime.now(timezone.utc)

    user = db.query(User).filter(User.id == db_token.user_id).first()
    if not user or not user.is_active:
        db.commit()
        return None

    # Criar novo par
    access_token, new_refresh = create_token_pair(db, user)

    # Registrar qual token substituiu este
    db_token.replaced_by = _hash_token(new_refresh)
    db.commit()

    return user, access_token, new_refresh


def revoke_user_tokens(db: Session, user_id: int) -> int:
    """Revoga todos os refresh tokens ativos de um usuário (logout global)."""
    return _revoke_all_user_tokens(db, user_id)


def _revoke_all_user_tokens(db: Session, user_id: int) -> int:
    """Revoga todos os tokens não-revogados de um usuário."""
    count = (
        db.query(RefreshToken)
        .filter(RefreshToken.user_id == user_id, RefreshToken.revoked.is_(False))
        .update(
            {"revoked": True, "revoked_at": datetime.now(timezone.utc)},
            synchronize_session="fetch",
        )
    )
    db.commit()
    return count


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não foi possível validar as credenciais",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Usuário inativo")
    return current_user


async def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_scheme_optional),
    db: Session = Depends(get_db)
) -> Optional[User]:
    if token is None:
        return None

    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        email: Optional[str] = payload.get("sub")
        if not email:
            return None
    except JWTError:
        return None

    return db.query(User).filter(User.email == email).first()
