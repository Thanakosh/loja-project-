---
task_id: TASK-012
title: "Rate limiting granular para OCR e LLM com slowapi"
priority: media
scope: backend/app/api/v1/ocr.py, backend/app/api/v1/llm.py, backend/app/core/limiter.py
branch: feat/rate-limiting-granular
commit_message: "feat(security): rate limiting granular por endpoint OCR e LLM"
estimated_effort: 30 minutos
status: concluida
depends_on: []
recomendacao_ref: "#6 Rate limiting em OCR e LLM"
---

# TASK-012: Rate limiting granular para OCR e LLM

## Contexto
O projeto ja possui `slowapi` instalado e um limiter global configurado (`backend/app/core/limiter.py`), mas os endpoints de OCR e LLM - que sao os mais caros computacionalmente - **nao possuem limites especificos** diferenciados. Um unico usuario pode abusar desses endpoints sem restricao.

**Problemas atuais:**
1. O limiter existe mas nao esta aplicado com granularidade nos endpoints caros
2. OCR e LLM consomem recursos significativos (CPU, GPU, API calls externas)
3. Sem diferenciacao entre limites por IP e por usuario autenticado
4. Sem feedback claro ao usuario sobre limites e retry-after

**Arquivo existente `limiter.py`:**
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
```

## Arquivos afetados
- `backend/app/core/limiter.py` - adicionar key_func por usuario
- `backend/app/api/v1/ocr.py` - decorar endpoints com rate limit
- `backend/app/api/v1/llm.py` - decorar endpoints com rate limit
- `backend/app/core/config.py` - configuracoes de limites

## Alteracao 1: Expandir `limiter.py`

```python
from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address


def get_user_or_ip(request: Request) -> str:
    """
    Identifica o rate limit key: user_id se autenticado, IP se nao.
    Permite limites diferentes para usuarios autenticados vs anonimos.
    """
    # Tenta extrair user do request state (setado pelo middleware de auth)
    user = getattr(request.state, "current_user", None)
    if user and hasattr(user, "id"):
        return f"user:{user.id}"
    return get_remote_address(request)


limiter = Limiter(key_func=get_user_or_ip)
```

## Alteracao 2: Configs no `config.py`

```python
    # Rate Limiting
    RATE_LIMIT_OCR: str = "10/hour"       # 10 uploads por hora
    RATE_LIMIT_LLM: str = "30/hour"       # 30 chamadas LLM por hora
    RATE_LIMIT_DEFAULT: str = "100/minute" # endpoints comuns
```

## Alteracao 3: Decorar endpoints OCR em `ocr.py`

```python
from app.core.limiter import limiter
from app.core.config import settings

@router.post("/processar")
@limiter.limit(settings.RATE_LIMIT_OCR)
async def processar_nota_fiscal(request: Request, ...):
    ...

@router.post("/analisar")
@limiter.limit(settings.RATE_LIMIT_OCR)
async def analisar_imagem(request: Request, ...):
    ...
```

**IMPORTANTE:** O `request: Request` deve ser o **primeiro parametro** do endpoint para `slowapi` funcionar corretamente.

## Alteracao 4: Decorar endpoints LLM em `llm.py`

```python
from app.core.limiter import limiter
from app.core.config import settings

@router.post("/analisar")
@limiter.limit(settings.RATE_LIMIT_LLM)
async def analisar_com_llm(request: Request, ...):
    ...

@router.post("/chat")
@limiter.limit(settings.RATE_LIMIT_LLM)
async def chat_llm(request: Request, ...):
    ...
```

## Alteracao 5: Atualizar `.env.example`

```env
# Rate Limiting
RATE_LIMIT_OCR=10/hour
RATE_LIMIT_LLM=30/hour
RATE_LIMIT_DEFAULT=100/minute
```

## Alteracao 6: Verificar handler 429 no `main.py`

O handler de `RateLimitExceeded` ja existe (linhas 116-124):
```python
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    ...
```
Apenas verificar que ele retorna `Retry-After` no header.

## Limites recomendados

| Endpoint | Limite | Justificativa |
|----------|--------|---------------|
| `POST /api/v1/ocr/processar` | 10/hour | OCR e pesado (CPU + storage) |
| `POST /api/v1/ocr/analisar` | 10/hour | Similar ao processar |
| `POST /api/v1/llm/analisar` | 30/hour | API call externa (Ollama) |
| `POST /api/v1/llm/chat` | 30/hour | API call externa (Ollama) |
| Demais endpoints | 100/minute | Default razoavel |

## Passos
1. Criar branch `feat/rate-limiting-granular`
2. Expandir `backend/app/core/limiter.py` com `get_user_or_ip`
3. Adicionar configs de rate limit ao `config.py`
4. Decorar endpoints OCR com `@limiter.limit(settings.RATE_LIMIT_OCR)`
5. Decorar endpoints LLM com `@limiter.limit(settings.RATE_LIMIT_LLM)`
6. Verificar handler 429 no `main.py`
7. Atualizar `.env.example`
8. Rodar testes: `cd backend && pytest tests/ -v`
9. Commit seguindo Conventional Commits

## Criterios de aceite
- [ ] Endpoints OCR limitados a 10/hora por usuario/IP
- [ ] Endpoints LLM limitados a 30/hora por usuario/IP
- [ ] Resposta 429 com formato padronizado (`code`, `message`, `trace_id`)
- [ ] Limites configuraveis via variaveis de ambiente
- [ ] Key function diferencia usuario autenticado de IP anonimo
- [ ] Testes existentes passam sem erros
- [ ] `.env.example` atualizado

## Notas
- `Request` DEVE ser o primeiro parametro do endpoint para `slowapi` funcionar
- O handler 429 ja existe no `main.py` - apenas verificar
- Testes de rate limit ja existem em `test_ratelimit.py` - expandir se necessario
- NAO aplicar rate limit em endpoints de leitura (GET) por enquanto
- Consultar `AGENTS.md` para padroes do projeto
