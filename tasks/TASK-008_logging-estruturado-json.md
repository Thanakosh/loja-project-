---
task_id: TASK-008
title: "Logging estruturado em JSON com trace_id por requisição"
priority: 🟡 média
scope: backend/app/core/ (logging_config.py, main.py, config.py)
branch: feat/structured-logging
commit_message: "feat(logging): implementa logging estruturado em JSON com trace_id"
estimated_effort: 45 minutos
status: concluída
depends_on: []
recomendacao_ref: "#7 — Logging estruturado e observabilidade"
---

# TASK-008: Logging estruturado em JSON com trace_id por requisição

## Contexto
O sistema atual usa `logging.basicConfig(level=logging.INFO)` no `database.py` e `logging.getLogger(__name__)` em vários módulos, mas sem formato estruturado. Em produção, logs de texto puro são difíceis de filtrar, agregar e correlacionar.

**Problemas atuais:**
1. Logs em texto puro — impossível parsear automaticamente (ELK, Datadog, CloudWatch)
2. O `trace_id` já é gerado no middleware (`main.py` linha 44-48), mas **não é incluído nos logs**
3. Sem contexto estruturado: não sabemos qual usuário, endpoint ou método HTTP gerou o log
4. `logging.basicConfig()` no `database.py` configura o root logger de forma rudimentar

## Arquivos afetados
- `backend/app/core/logging_config.py` — **NOVO** — configuração centralizada de logging
- `backend/app/core/config.py` — adicionar configuração `LOG_FORMAT` e `LOG_LEVEL`
- `backend/app/main.py` — integrar logging config e enriquecer middleware com contexto
- `backend/app/core/database.py` — remover `logging.basicConfig()` redundante

## Dependências Python necessárias
```
python-json-logger>=2.0.7
```
Adicionar ao `backend/requirements.txt`.

## Alteração 1: Criar `backend/app/core/logging_config.py`

```python
import logging
import sys
from typing import Optional

from pythonjsonlogger import jsonlogger


class ContextFilter(logging.Filter):
    """Injeta trace_id e request context nos log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "trace_id"):
            record.trace_id = "no-request-context"
        if not hasattr(record, "method"):
            record.method = ""
        if not hasattr(record, "path"):
            record.path = ""
        if not hasattr(record, "user_id"):
            record.user_id = ""
        return True


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Formatter JSON customizado com campos padronizados."""

    def add_fields(self, log_record: dict, record: logging.LogRecord, message_dict: dict) -> None:
        super().add_fields(log_record, record, message_dict)
        log_record["level"] = record.levelname
        log_record["logger"] = record.name
        log_record["timestamp"] = self.formatTime(record)
        # Campos de contexto da requisição
        log_record["trace_id"] = getattr(record, "trace_id", "")
        log_record["method"] = getattr(record, "method", "")
        log_record["path"] = getattr(record, "path", "")
        log_record["user_id"] = getattr(record, "user_id", "")


def setup_logging(
    log_level: str = "INFO",
    log_format: str = "json",
) -> None:
    """
    Configura logging global da aplicação.

    Args:
        log_level: Nível mínimo de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Formato de saída — "json" (produção) ou "text" (desenvolvimento)
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Remove handlers existentes para evitar duplicação
    root_logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)

    if log_format.lower() == "json":
        formatter = CustomJsonFormatter(
            fmt="%(timestamp)s %(level)s %(logger)s %(message)s %(trace_id)s",
            datefmt="%Y-%m-%dT%H:%M:%S%z",
        )
    else:
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | trace_id=%(trace_id)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    handler.setFormatter(formatter)
    handler.addFilter(ContextFilter())
    root_logger.addHandler(handler)

    # Reduzir verbosidade de libs terceiras
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if log_level.upper() == "DEBUG" else logging.WARNING
    )
```

## Alteração 2: Adicionar configs no `config.py`

Adicionar os seguintes campos à classe `Settings`:

```python
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # "json" para produção, "text" para dev
```

## Alteração 3: Integrar no `main.py`

Substituir o middleware de `trace_id` para também alimentar o contexto de logging:

```python
import contextvars
from app.core.logging_config import setup_logging

# Antes de criar o app:
setup_logging(log_level=settings.LOG_LEVEL, log_format=settings.LOG_FORMAT)

logger = logging.getLogger(__name__)

# Context var para trace_id (acessível em qualquer ponto da request)
_trace_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar("trace_id", default="")


@app.middleware("http")
async def add_trace_id_to_request(request: Request, call_next):
    trace_id = request.headers.get("X-Trace-Id") or str(uuid.uuid4())
    request.state.trace_id = trace_id
    _trace_id_ctx.set(trace_id)

    # Log de início da requisição
    logger.info(
        "Request iniciada",
        extra={
            "trace_id": trace_id,
            "method": request.method,
            "path": str(request.url.path),
        },
    )

    response = await call_next(request)
    response.headers["X-Trace-Id"] = trace_id

    # Log de conclusão
    logger.info(
        "Request concluída",
        extra={
            "trace_id": trace_id,
            "method": request.method,
            "path": str(request.url.path),
            "status_code": response.status_code,
        },
    )

    return response
```

## Alteração 4: Remover basicConfig do `database.py`

```python
# REMOVER esta linha:
logging.basicConfig(level=logging.INFO)

# MANTER apenas:
logger = logging.getLogger(__name__)
```

## Alteração 5: Atualizar `.env.example`

Adicionar as novas variáveis:

```env
# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

## Exemplo de output esperado

### Formato JSON (produção):
```json
{
  "timestamp": "2026-02-15T03:00:00-03:00",
  "level": "INFO",
  "logger": "app.main",
  "message": "Request iniciada",
  "trace_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "method": "GET",
  "path": "/api/v2/estoque/"
}
```

### Formato texto (desenvolvimento):
```
2026-02-15 03:00:00 | INFO     | app.main | trace_id=a1b2c3d4... | Request iniciada
```

## Passos
1. Criar branch `feat/structured-logging`
2. Adicionar `python-json-logger>=2.0.7` ao `backend/requirements.txt`
3. Criar `backend/app/core/logging_config.py` com o código acima
4. Adicionar `LOG_LEVEL` e `LOG_FORMAT` ao `config.py`
5. Integrar `setup_logging()` e enriquecer o middleware no `main.py`
6. Remover `logging.basicConfig()` do `database.py`
7. Atualizar `.env.example` com as novas variáveis
8. Rodar testes: `cd backend && pytest tests/ -v`
9. Verificar output de logs no console ao iniciar o servidor
10. Commit seguindo Conventional Commits

## Critérios de aceite
- [ ] Logs da aplicação saem em formato JSON quando `LOG_FORMAT=json`
- [ ] Logs saem em formato texto legível quando `LOG_FORMAT=text`
- [ ] Cada log de requisição inclui `trace_id`, `method` e `path`
- [ ] `logging.basicConfig()` removido do `database.py`
- [ ] Testes existentes passam sem erros
- [ ] `.env.example` atualizado com `LOG_LEVEL` e `LOG_FORMAT`
- [ ] Libs de terceiros (uvicorn, sqlalchemy) com verbosidade reduzida

## Notas
- NÃO alterar a lógica de negócio de nenhum endpoint
- O `trace_id` já existe no middleware — esta task apenas o propaga para o logging
- Em ambiente de dev, usar `LOG_FORMAT=text` para facilitar leitura no terminal
- Consultar `AGENTS.md` para padrões do projeto
