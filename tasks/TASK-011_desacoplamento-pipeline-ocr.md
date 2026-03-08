---
task_id: TASK-011
title: "Desacoplamento do pipeline OCR com fila assíncrona (ARQ + Redis)"
priority: 🟢 arquitetura
scope: backend/app/core/, backend/app/api/v1/ocr.py, docker-compose.yml
branch: feat/ocr-async-queue
commit_message: "feat(ocr): desacopla pipeline OCR com fila assíncrona persistida"
estimated_effort: 120 minutos
status: concluída
depends_on: []
recomendacao_ref: "#10 — Desacoplamento do pipeline OCR → LLM → cadastro"
completed_at: "2026-03-08"
branch: feat/ocr-async-queue
commit: "feat(ocr): desacopla pipeline OCR com fila assíncrona persistida"
---

# TASK-011: Desacoplamento do pipeline OCR com fila assíncrona

> ✅ **STATUS: CONCLUÍDA** — Infraestrutura ARQ + Redis implementada na branch `feat/ocr-async-queue`.
> O fluxo XML síncrono (/upload-arquivo) continua ativo e independente do Redis.
> O processamento OCR/LLM real será habilitado no worker quando reintroduzido.

## Contexto
O pipeline OCR → LLM → cadastro roda dentro do processo da API usando `BackgroundTasks`. O estado é mantido **em memória** (dict Python), o que causa:

1. **Perda de tarefas em restart** — tarefas em andamento são perdidas
2. **Sem retry** — falha no OCR/LLM não tem recuperação automática
3. **Sem idempotência** — mesma nota pode ser processada múltiplas vezes
4. **Sem TTL** — tarefas antigas acumulam em memória
5. **Sem escalabilidade** — impossível distribuir entre workers

**Solução:** ARQ (Async Redis Queue) — leve, async-native, compatível com stack.

## Deps necessárias
Adicionar ao `requirements.txt`:
```
arq>=0.25.0
redis>=5.0.0
```

## Arquivos afetados
- `backend/app/core/task_queue.py` — **NOVO** — abstração da fila
- `backend/app/core/ocr_worker.py` — **NOVO** — worker ARQ
- `backend/app/api/v1/ocr.py` — adaptar para usar fila
- `backend/app/core/config.py` — configs Redis
- `docker-compose.yml` — serviço Redis
- `.env.example` — novas variáveis

## Alteração 1: Redis no `docker-compose.yml`

Adicionar serviço e volume:
```yaml
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 3
# Adicionar redis_data ao volumes:
```

## Alteração 2: Configs no `config.py`

```python
    # Redis / Task Queue
    REDIS_URL: str = "redis://localhost:6379/0"
    OCR_TASK_TTL_HOURS: int = 24
    OCR_MAX_RETRIES: int = 3
    OCR_RETRY_DELAY_SECONDS: int = 30
```

## Alteração 3: `backend/app/core/task_queue.py`

Implementar:
- `get_redis_pool()` — pool de conexões
- `enqueue_ocr_task(file_path, user_id, filename, idempotency_key)` → task_id
- `get_task_status(task_id)` → {status, result, error, retries}
- `close_redis_pool()` — cleanup
- Idempotência via chave hash do arquivo no Redis
- TTL automático via `redis.expire()`

## Alteração 4: `backend/app/core/ocr_worker.py`

Implementar `WorkerSettings` com:
- `process_ocr_task(ctx, file_path, user_id, filename)` — handler principal
- Atualiza metadata em `ocr:meta:{job_id}` (status, retries, error)
- Cron job diário para limpeza de tarefas expiradas
- Config: `max_tries`, `retry_delay`, `max_jobs=5`, `job_timeout=300`
- Iniciar com: `arq app.core.ocr_worker.WorkerSettings`

## Alteração 5: Adaptar `ocr.py`

Substituir `BackgroundTasks` por `enqueue_ocr_task()`:
```python
# POST /api/v1/ocr/processar → enqueue_ocr_task(...) → retorna task_id
# GET /api/v1/ocr/status/{task_id} → get_task_status(task_id)
```

## Arquitetura resultante
```
FastAPI ──▶ Redis (Queue) ◀── ARQ Worker (OCR/LLM)
  POST /ocr/processar         process_ocr_task()
  GET /ocr/status/{id}        retry + idempotência + TTL
```

## Passos
1. Criar branch `feat/ocr-async-queue`
2. Adicionar deps ao `requirements.txt`
3. Redis no `docker-compose.yml`
4. Configs no `config.py`
5. Criar `task_queue.py` e `ocr_worker.py`
6. Adaptar `ocr.py`
7. Atualizar `.env.example`
8. Testar: `docker compose up -d` + `arq app.core.ocr_worker.WorkerSettings`
9. `cd backend && pytest tests/ -v`
10. Commit seguindo Conventional Commits

## Critérios de aceite
- [ ] Redis no `docker-compose.yml` com healthcheck
- [ ] Tarefas OCR enfileiradas no Redis (não usa BackgroundTasks)
- [ ] Status consultado via Redis
- [ ] Tarefas sobrevivem a restart da API
- [ ] Retry automático (até 3 tentativas)
- [ ] Idempotência por hash do arquivo
- [ ] TTL: auto-expiração após 24h
- [ ] Worker ARQ iniciável separadamente
- [ ] Testes existentes passam (mock Redis)

## Notas
- NÃO remover lógica OCR existente — apenas redirecionar para worker
- Manter BackgroundTasks como fallback se Redis indisponível
- Testes de OCR: usar `fakeredis` para mock
- Implementação pode ser faseada (Fase 1: infra, Fase 2: endpoints, Fase 3: OCR real)
- Consultar `AGENTS.md` para padrões do projeto
