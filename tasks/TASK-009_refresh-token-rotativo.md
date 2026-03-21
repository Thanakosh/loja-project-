---
task_id: TASK-009
title: "Refresh token rotativo com revogacao e blacklist"
priority: arquitetura
scope: backend/app/core/security.py, backend/app/api/v1/users.py, backend/app/models/
branch: feat/refresh-token
commit_message: "feat(auth): implementa refresh token rotativo com revogacao"
estimated_effort: 90 minutos
status: concluida
depends_on: []
recomendacao_ref: "#11 Evolucao de autenticacao com refresh token"
---

# TASK-009: Refresh token rotativo com revogacao e blacklist

## Contexto
Atualmente o sistema usa apenas **access token** (JWT) com expiracao de 30 minutos (`ACCESS_TOKEN_EXPIRE_MINUTES`). Quando o token expira, o usuario precisa fazer login novamente. Isso cria uma experiencia ruim para sessoes longas.

**Problemas atuais:**
1. Sem refresh token - o usuario precisa re-autenticar a cada 30 min
2. Sem mecanismo de revogacao - nao e possivel invalidar tokens apos logout ou comprometimento
3. O endpoint `POST /api/v1/users/token` retorna apenas `{ access_token, token_type }`

**Solucao:**
- Access token curto (15 min) + Refresh token longo (7 dias)
- Refresh token rotativo: cada uso gera um novo par (access + refresh)
- Blacklist em banco para revogacao (logout / comprometimento)

## Arquivos afetados
- `backend/app/models/refresh_token.py` - **NOVO** - modelo de refresh token
- `backend/app/core/security.py` - funcoes de criacao/validacao de refresh token
- `backend/app/core/config.py` - novas configuracoes de token
- `backend/app/api/v1/users.py` - endpoints `/refresh` e `/logout`
- `backend/app/schemas/user.py` - schema de resposta com refresh token
- `migrations/` - nova migracao para tabela `refresh_token`

## Alteracao 1: Criar modelo `backend/app/models/refresh_token.py`

```python
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Index
from sqlalchemy.orm import relationship

from ..core.database import Base


class RefreshToken(Base):
    __tablename__ = "refresh_token"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    token_hash = Column(String, unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked = Column(Boolean, default=False, nullable=False)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    # Qual token gerou este (para deteccao de reuso)
    replaced_by = Column(String, nullable=True)

    user = relationship("User", backref="refresh_tokens")

    __table_args__ = (
        Index("ix_refresh_token_user_active", "user_id", "revoked"),
    )

    def __repr__(self):
        return f"<RefreshToken(id={self.id}, user_id={self.user_id}, revoked={self.revoked})>"
```

## Alteracao 2: Adicionar configs no `config.py`

Adicionar a classe `Settings`:

```python
    # Token Configuration
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15  #  REDUZIR de 30 para 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
```

## Alteracao 3: Atualizar `security.py`

Adicionar funcoes de criacao e validacao de refresh token:

```python
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

from sqlalchemy.orm import Session

from ..models.refresh_token import RefreshToken


def _hash_token(token: str) -> str:
    """Hash do refresh token para armazenamento seguro."""
    return hashlib.sha256(token.encode()).hexdigest()


def create_token_pair(
    db: Session,
    user: "User",
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
) -> Optional[Tuple["User", str, str]]:
    """
    Valida e rotaciona um refresh token.

    - Revoga o token antigo
    - Cria novo par (access + refresh)
    - Detecta reuso de token ja revogado (possivel roubo)

    Returns:
        Tuple[User, access_token, new_refresh_token] ou None se invalido
    """
    token_hash = _hash_token(raw_token)

    db_token = db.query(RefreshToken).filter(
        RefreshToken.token_hash == token_hash
    ).first()

    if not db_token:
        return None

    # Token ja revogado  possivel roubo! Revogar TODA a familia
    if db_token.revoked:
        _revoke_all_user_tokens(db, db_token.user_id)
        return None

    # Token expirado
    if db_token.expires_at < datetime.now(timezone.utc):
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
    """Revoga todos os refresh tokens ativos de um usuario (logout global)."""
    return _revoke_all_user_tokens(db, user_id)


def _revoke_all_user_tokens(db: Session, user_id: int) -> int:
    """Revoga todos os tokens nao-revogados de um usuario."""
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
```

## Alteracao 4: Atualizar esquemas em `schemas/user.py`

Adicionar schema de resposta com tokens:

```python
class TokenResponse(BaseModel):
    """Resposta de autenticacao com access e refresh tokens."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # segundos ate expiracao do access token


class RefreshTokenRequest(BaseModel):
    """Request para renovar tokens."""
    refresh_token: str
```

## Alteracao 5: Atualizar endpoints em `users.py`

```python
from ...core.security import (
    create_token_pair,
    rotate_refresh_token,
    revoke_user_tokens,
    get_current_user,
    get_password_hash,
    verify_password,
)
from ...schemas.user import TokenResponse, RefreshTokenRequest


@router.post("/token", response_model=TokenResponse)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token, refresh_token = create_token_pair(db, user)
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_access_token(
    body: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """
    Renova o par de tokens usando um refresh token valido.

    O refresh token usado e revogado e um novo par e emitido (rotacao).
    Se um refresh token ja revogado for apresentado, TODOS os tokens
    do usuario sao revogados por seguranca (deteccao de roubo).
    """
    result = rotate_refresh_token(db, body.refresh_token)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token invalido ou expirado",
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
async def logout(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Revoga todos os refresh tokens do usuario (logout global).
    O access token atual continua valido ate expirar (15 min max).
    """
    count = revoke_user_tokens(db, current_user.id)
    return {"message": "Logout realizado com sucesso", "tokens_revogados": count}
```

## Alteracao 6: Registrar model e gerar migracao

No `backend/app/models/__init__.py`, adicionar:
```python
from .refresh_token import RefreshToken
```

Gerar migracao:
```bash
cd backend
alembic revision --autogenerate -m "add_refresh_token_table"
alembic upgrade head
```

## Alteracao 7: Atualizar `.env.example`

```env
# Token Configuration
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
```

## Fluxo de autenticacao (apos implementacao)

```
1. Login:      POST /api/v1/users/token   { access_token, refresh_token, expires_in }
2. Usar API:   Authorization: Bearer <access_token>
3. Renovar:    POST /api/v1/users/refresh { refresh_token }  { novo_access, novo_refresh }
4. Logout:     POST /api/v1/users/logout   revoga todos os refresh tokens
```

## Seguranca implementada

| Risco | Mitigacao |
|-------|-----------|
| Roubo de refresh token | Rotacao: cada uso gera novo token |
| Reuso de token revogado | Deteccao de roubo: revoga TODA a familia |
| Token exposto em DB | Armazenado como hash SHA-256 (nao reversivel) |
| Sessao comprometida | `/logout` revoga todos os tokens ativos |
| Access token longo | Reduzido de 30 para 15 minutos |

## Passos
1. Criar branch `feat/refresh-token`
2. Criar `backend/app/models/refresh_token.py`
3. Registrar modelo em `backend/app/models/__init__.py`
4. Adicionar `REFRESH_TOKEN_EXPIRE_DAYS` ao `config.py`
5. Alterar `ACCESS_TOKEN_EXPIRE_MINUTES` de 30 para 15
6. Adicionar funcoes de refresh token ao `security.py`
7. Adicionar schemas `TokenResponse` e `RefreshTokenRequest` ao `schemas/user.py`
8. Atualizar endpoints em `users.py` (`/token`, `/refresh`, `/logout`)
9. Gerar migracao Alembic: `alembic revision --autogenerate -m "add_refresh_token_table"`
10. Atualizar `.env.example`
11. Rodar testes: `cd backend && pytest tests/ -v`
12. Commit seguindo Conventional Commits

## Criterios de aceite
- [ ] `POST /api/v1/users/token` retorna `{ access_token, refresh_token, token_type, expires_in }`
- [ ] `POST /api/v1/users/refresh` aceita refresh token e retorna novo par
- [ ] Refresh token antigo e revogado apos uso (rotacao)
- [ ] Reuso de token revogado revoga TODOS os tokens do usuario
- [ ] `POST /api/v1/users/logout` revoga todos os refresh tokens ativos
- [ ] Refresh tokens armazenados como hash SHA-256 (nunca em texto puro)
- [ ] Migracao Alembic criada e aplicavel
- [ ] Testes existentes adaptados para novo formato de resposta do `/token`
- [ ] Testes existentes passam sem erros

##  Cuidado com os testes existentes
Os testes atuais esperam que `POST /api/v1/users/token` retorne `{ access_token, token_type }`.
Com esta mudanca, a resposta incluira `refresh_token` e `expires_in` adicionais.
Verificar e ajustar:
- `conftest.py` - fixture `auth_headers` (linha 82-88)
- `test_users.py` - testes de login

Os testes devem continuar extraindo `access_token` normalmente, ja que o campo ainda existe.

## Notas
- NAO implementar JWT para o refresh token - usar token opaco (secrets.token_urlsafe)
- NAO armazenar o refresh token em texto puro - sempre hash
- O access token JWT NAO e revogavel (stateless) - ele expira naturalmente em 15 min
- A limpeza de tokens expirados pode ser feita em task futura (cron job)
- Consultar `AGENTS.md` para padroes do projeto
