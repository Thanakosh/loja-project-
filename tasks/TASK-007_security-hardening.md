---
task_id: TASK-007
title: "Hardening de segurança: CORS por ambiente e validação de startup"
priority: 🔴 alta
scope: backend/app/core/ (config.py, security.py, main.py)
branch: fix/security-hardening
commit_message: "fix(security): CORS restrito por ambiente e validação de segredos no startup"
estimated_effort: 15 minutos
status: concluída
---

# TASK-007: Hardening de segurança — CORS por ambiente e validação de startup

## Contexto
Existem pontos de segurança que precisam ser endurecidos antes de ir para produção:

1. **CORS** permite `["*"]` se configurado assim no `.env`, sem warning
2. **JWT_SECRET** pode ser qualquer valor curto ou previsível — sem validação de força
3. **Nenhuma validação** no startup para detectar configurações inseguras
4. **Mensagens de erro** de autenticação estão em inglês (inconsistência com o restante da API)

## Arquivos afetados
- `backend/app/core/config.py` — validações de segurança
- `backend/app/main.py` — warning de CORS no startup

## Alteração 1: Validações no `config.py`

Adicionar validadores para detectar configurações inseguras:

```python
import secrets
import logging
from typing import Optional, List, Union

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str
    SQLALCHEMY_ECHO: bool = False

    # Security
    JWT_SECRET: str
    fastapi_users_secret: str = secrets.token_urlsafe(32)
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Optional configurations
    WHATSAPP_TOKEN: Optional[str] = None
    OPENAI_KEY: Optional[str] = None
    OLLAMA_URL: str = "http://localhost:11434"
    OPEN_INTERPRETER_URL: str = "http://localhost:4000/v1/chat/completions"

    # API Settings
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "Loja API"
    DEBUG: bool = False

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        if not v:
            raise ValueError("DATABASE_URL is required")
        return v

    @field_validator("JWT_SECRET")
    @classmethod
    def validate_jwt_secret(cls, v: str) -> str:
        """Valida que o JWT_SECRET é suficientemente seguro."""
        if not v or len(v) < 16:
            raise ValueError(
                "JWT_SECRET deve ter pelo menos 16 caracteres. "
                "Gere um com: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
            )
        insecure_values = [
            "secret", "password", "123456", "change-me",
            "sua_chave_secreta", "jwt_secret", "mysecret",
        ]
        if v.lower() in insecure_values:
            raise ValueError(
                f"JWT_SECRET com valor '{v}' é inseguro. "
                "Use um valor aleatório forte."
            )
        return v

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()

# Warnings de configuração no startup
if "*" in settings.CORS_ORIGINS:
    logger.warning(
        "⚠️  CORS_ORIGINS contém wildcard '*'. "
        "Isso é aceitável em desenvolvimento, mas NUNCA em produção. "
        "Configure uma lista restrita de origens para ambientes de produção."
    )

if settings.DEBUG:
    logger.warning(
        "⚠️  DEBUG=True está ativo. Desative em produção."
    )
```

## Alteração 2: Warning no `main.py`

Adicionar log no startup da aplicação:

```python
import logging

logger = logging.getLogger(__name__)

# Após app = FastAPI(...)
@app.on_event("startup")
async def startup_warnings():
    if "*" in settings.CORS_ORIGINS:
        logger.warning(
            "CORS wildcard ativo — não usar em produção"
        )
    logger.info(f"Loja API v2.0 iniciada | DEBUG={settings.DEBUG}")
```

## Alteração 3: Padronizar mensagens de autenticação (opcional)

No `backend/app/core/security.py`, padronizar mensagens para português:

```python
# ANTES
detail="Could not validate credentials"
detail="Inactive user"

# DEPOIS  
detail="Não foi possível validar as credenciais"
detail="Usuário inativo"
```

E no `backend/app/api/v1/users.py`:
```python
# ANTES
detail="Incorrect email or password"
detail="Email already registered"

# DEPOIS
detail="Email ou senha incorretos"
detail="Email já cadastrado"
```

## Passos
1. Criar branch `fix/security-hardening`
2. Atualizar `backend/app/core/config.py` com validação de JWT_SECRET e warnings
3. Adicionar startup event no `backend/app/main.py`
4. (Opcional) Padronizar mensagens de erro para português
5. Rodar testes: `cd backend && pytest tests/ -v`
6. Commit seguindo Conventional Commits

## Critérios de aceite
- [x] Servidor **recusa iniciar** se `JWT_SECRET` tiver menos de 16 caracteres
- [x] Servidor **recusa iniciar** se `JWT_SECRET` for um valor trivial ("secret", "password", etc.)
- [x] Warning no log quando CORS tem wildcard `*`
- [x] Warning no log quando `DEBUG=True`
- [x] Testes passam sem erros (ajustar `.env` de teste se necessário)

## ⚠️ Cuidado com os testes
Os testes atuais usam `conftest.py` que pode definir o `JWT_SECRET` via variável de ambiente.
Verificar que o valor usado nos testes tem >= 16 caracteres, senão o validador vai rejeitar.
Se necessário, ajustar o `conftest.py`:
```python
os.environ["JWT_SECRET"] = "test-secret-key-with-minimum-length-ok"
```

## Notas
- NÃO bloquear o startup por causa do CORS wildcard — apenas warnar (dev pode precisar)
- SIM bloquear por causa do JWT_SECRET fraco — isso é crítico
- Consultar `AGENTS.md` para padrões de segurança do projeto
