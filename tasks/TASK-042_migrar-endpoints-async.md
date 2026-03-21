---
task_id: TASK-042
title: "Migrar endpoints para async de forma incremental"
status: pendente
priority: baixa
agent_chat_executable: "sim"
depends_on: ["TASK-037"]
---

## Objetivo

Migrar endpoints do backend de sessões síncronas (`Session`) para assíncronas
(`AsyncSession`) de forma incremental, começando pelos módulos de maior I/O,
sem quebrar funcionalidade existente.

### Contexto

O `database.py` já possui infraestrutura async pronta (`get_async_engine`,
`get_async_db`, `AsyncSession`), mas apenas o endpoint `health_async` a
utiliza. A `STRATEGY.md` define a convergência async como objetivo de longo
prazo. Todos os 21 routers usam `Session = Depends(get_db)` (síncronos).

### Pré-requisitos

- TASK-037 concluída (baseline de cobertura de testes para detectar regressões).
- Dependência `asyncpg` instalada para PostgreSQL async.
- Dependência `aiosqlite` instalada para testes com SQLite async.

### Ações

#### Fase 1 — Preparação

1. **Adicionar dependências async ao requirements.txt:**
   ```
   asyncpg>=0.29.0
   aiosqlite>=0.20.0
   ```
2. **Criar fixture async no conftest.py de testes:**
   ```python
   @pytest_asyncio.fixture
   async def async_db():
       async with _AsyncSessionLocal() as session:
           yield session
   ```
3. **Verificar que `get_async_db()` funciona** com endpoint de health existente.

#### Fase 2 — Migrar módulo por módulo (ordem sugerida)

| Ordem | Módulo | Motivo da prioridade |
|-------|--------|---------------------|
| 1 | `estoque_v2.py` | Maior I/O (queries agregadas) |
| 2 | `pdv.py` | Operações transacionais pesadas |
| 3 | `ocr.py` | I/O de arquivo + processamento |
| 4 | `produtos.py` | Alta frequência de acesso |
| 5+ | Demais endpoints | Ordem livre |

Para cada módulo:
1. Mudar `def endpoint(...)` para `async def endpoint(...)`.
2. Mudar `db: Session = Depends(get_db)` para `db: AsyncSession = Depends(get_async_db)`.
3. Substituir `db.query(Model)` por `await db.execute(select(Model))`.
4. Substituir `db.commit()` por `await db.commit()`.
5. Substituir `db.add()` por `db.add()` (sem await, mas `flush`/`commit` com await).
6. Atualizar testes correspondentes para usar fixture async.
7. Rodar testes do módulo e verificar que passam.

#### Fase 3 — Limpeza

1. Quando todos os endpoints estiverem migrados, remover `get_db()` sync.
2. Atualizar `database.py` para manter apenas engine async.
3. Atualizar `STRATEGY.md` marcando convergência async como concluída.

### Regras para o agente

- **Migrar UM módulo por PR** — PRs pequenos e focados.
- **Manter cobertura de testes** — não reduzir cobertura do módulo migrado.
- **Não misturar sync/async** no mesmo endpoint.
- Testar tanto com SQLite (testes) quanto com PostgreSQL (dev/staging).

### Critério de aceite (por módulo)

- Endpoint usa `AsyncSession` e `async/await` corretamente.
- Testes do módulo passam com fixture async.
- Nenhum uso síncrono remanescente no módulo migrado.
- Build e CI verdes.

### Branch sugerida

`refactor/async-<nome-modulo>` (ex: `refactor/async-estoque-v2`)

## Atualizacao de progresso

- Modulo `estoque_v2.py` migrado para `AsyncSession` em `refactor/async-estoque-v2`.
- Dependencias de autenticacao async adicionadas em `app/core/security.py` para evitar misturar sync/async no endpoint.
- `backend/tests/conftest.py` recebeu adapter async sobre a mesma sessao de teste, permitindo validar o modulo incrementalmente sem reestruturar toda a suite.
- Validacao executada: `pytest backend/tests/test_estoque_v2.py -q` com `8 passed`.
- Task geral permanece `pendente`, pois os proximos modulos (`pdv.py`, `ocr.py`, `produto.py` e demais) ainda nao foram migrados.
