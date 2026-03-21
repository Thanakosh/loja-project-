---
task_id: TASK-007
title: "Hardening de seguranca: CORS por ambiente e validacao de startup"
priority: alta
scope: backend/app/core/ (config.py, security.py, main.py)
branch: fix/security-hardening
commit_message: "fix(security): CORS restrito por ambiente e validacao de segredos no startup"
estimated_effort: 15 minutos
status: concluida
---

# TASK-007: Hardening de seguranca - CORS por ambiente e validacao de startup

## Contexto
Existem pontos de seguranca que precisam ser endurecidos antes de ir para producao:

1. **CORS** permite `["*"]` se configurado assim no `.env`, sem warning
2. **JWT_SECRET** pode ser qualquer valor curto ou previsivel - sem validacao de forca
3. **Nenhuma validacao** no startup para detectar configuracoes inseguras
4. **Mensagens de erro** de autenticacao estao em ingles (inconsistencia com o restante da API)

## Arquivos afetados
- `backend/app/core/config.py` - validacoes de seguranca
- `backend/app/main.py` - warning de CORS no startup

## Alteracao 1: Validacoes no `config.py`

Adicionar validadores para detectar configuracoes inseguras:

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
        """Valida que o JWT_SECRET e suficientemente seguro."""
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
                f"JWT_SECRET com valor '{v}' e inseguro. "
                "Use um valor aleatorio forte."
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

# Warnings de configuracao no startup
if "*" in settings.CORS_ORIGINS:
    logger.warning(
        "  CORS_ORIGINS contem wildcard '*'. "
        "Isso e aceitavel em desenvolvimento, mas NUNCA em producao. "
        "Configure uma lista restrita de origens para ambientes de producao."
    )

if settings.DEBUG:
    logger.warning(
        "  DEBUG=True esta ativo. Desative em producao."
    )
```

## Alteracao 2: Warning no `main.py`

Adicionar log no startup da aplicacao:

```python
import logging

logger = logging.getLogger(__name__)

# Apos app = FastAPI(...)
@app.on_event("startup")
async def startup_warnings():
    if "*" in settings.CORS_ORIGINS:
        logger.warning(
            "CORS wildcard ativo - nao usar em producao"
        )
    logger.info(f"Loja API v2.0 iniciada | DEBUG={settings.DEBUG}")
```

## Alteracao 3: Padronizar mensagens de autenticacao (opcional)

No `backend/app/core/security.py`, padronizar mensagens para portugues:

```python
# ANTES
detail="Could not validate credentials"
detail="Inactive user"

# DEPOIS
detail="Nao foi possivel validar as credenciais"
detail="Usuario inativo"
```

E no `backend/app/api/v1/users.py`:
```python
# ANTES
detail="Incorrect email or password"
detail="Email already registered"

# DEPOIS
detail="Email ou senha incorretos"
detail="Email ja cadastrado"
```

## Passos
1. Criar branch `fix/security-hardening`
2. Atualizar `backend/app/core/config.py` com validacao de JWT_SECRET e warnings
3. Adicionar startup event no `backend/app/main.py`
4. (Opcional) Padronizar mensagens de erro para portugues
5. Rodar testes: `cd backend && pytest tests/ -v`
6. Commit seguindo Conventional Commits

## Criterios de aceite
- [x] Servidor **recusa iniciar** se `JWT_SECRET` tiver menos de 16 caracteres
- [x] Servidor **recusa iniciar** se `JWT_SECRET` for um valor trivial ("secret", "password", etc.)
- [x] Warning no log quando CORS tem wildcard `*`
- [x] Warning no log quando `DEBUG=True`
- [x] Testes passam sem erros (ajustar `.env` de teste se necessario)

##  Cuidado com os testes
Os testes atuais usam `conftest.py` que pode definir o `JWT_SECRET` via variavel de ambiente.
Verificar que o valor usado nos testes tem >= 16 caracteres, senao o validador vai rejeitar.
Se necessario, ajustar o `conftest.py`:
```python
os.environ["JWT_SECRET"] = "test-secret-key-with-minimum-length-ok"
```

## Notas
- NAO bloquear o startup por causa do CORS wildcard - apenas warnar (dev pode precisar)
- SIM bloquear por causa do JWT_SECRET fraco - isso e critico
- Consultar `AGENTS.md` para padroes de seguranca do projeto
