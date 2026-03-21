---
task_id: TASK-042
title: "Migrar endpoints para async de forma incremental"
status: pendente
priority: baixa
agent_chat_executable: "sim"
depends_on: ["TASK-037"]
---

## Objetivo

Migrar endpoints do backend de sessoes sincronas (`Session`) para assincronas
(`AsyncSession`) de forma incremental, comecando pelos modulos de maior I/O,
sem quebrar funcionalidade existente.

### Contexto

O `database.py` ja possui infraestrutura async pronta (`get_async_engine`,
`get_async_db`, `AsyncSession`), mas apenas o endpoint `health_async` a
utiliza. A `STRATEGY.md` define a convergencia async como objetivo de longo
prazo. Todos os 21 routers usam `Session = Depends(get_db)` (sincronos).

### Pre-requisitos

- TASK-037 concluida (baseline de cobertura de testes para detectar regressoes).
- Dependencia `asyncpg` instalada para PostgreSQL async.
- Dependencia `aiosqlite` instalada para testes com SQLite async.

### Acoes

#### Fase 1 - Preparacao

1. **Adicionar dependencias async ao requirements.txt:**
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

#### Fase 2 - Migrar modulo por modulo (ordem sugerida)

| Ordem | Modulo | Motivo da prioridade |
|-------|--------|---------------------|
| 1 | `estoque_v2.py` | Maior I/O (queries agregadas) |
| 2 | `pdv.py` | Operacoes transacionais pesadas |
| 3 | `ocr.py` | I/O de arquivo + processamento |
| 4 | `produtos.py` | Alta frequencia de acesso |
| 5+ | Demais endpoints | Ordem livre |

Para cada modulo:
1. Mudar `def endpoint(...)` para `async def endpoint(...)`.
2. Mudar `db: Session = Depends(get_db)` para `db: AsyncSession = Depends(get_async_db)`.
3. Substituir `db.query(Model)` por `await db.execute(select(Model))`.
4. Substituir `db.commit()` por `await db.commit()`.
5. Substituir `db.add()` por `db.add()` (sem await, mas `flush`/`commit` com await).
6. Atualizar testes correspondentes para usar fixture async.
7. Rodar testes do modulo e verificar que passam.

#### Fase 3 - Limpeza

1. Quando todos os endpoints estiverem migrados, remover `get_db()` sync.
2. Atualizar `database.py` para manter apenas engine async.
3. Atualizar `STRATEGY.md` marcando convergencia async como concluida.

### Regras para o agente

- **Migrar UM modulo por PR** - PRs pequenos e focados.
- **Manter cobertura de testes** - nao reduzir cobertura do modulo migrado.
- **Nao misturar sync/async** no mesmo endpoint.
- Testar tanto com SQLite (testes) quanto com PostgreSQL (dev/staging).

### Criterio de aceite (por modulo)

- Endpoint usa `AsyncSession` e `async/await` corretamente.
- Testes do modulo passam com fixture async.
- Nenhum uso sincrono remanescente no modulo migrado.
- Build e CI verdes.

### Branch sugerida

`refactor/async-<nome-modulo>` (ex: `refactor/async-estoque-v2`)

## Atualizacao de progresso

- Modulo `estoque_v2.py` migrado para `AsyncSession` em `refactor/async-estoque-v2`.
- Dependencias de autenticacao async adicionadas em `app/core/security.py` para evitar misturar sync/async no endpoint.
- `backend/tests/conftest.py` recebeu adapter async sobre a mesma sessao de teste, permitindo validar o modulo incrementalmente sem reestruturar toda a suite.
- Validacao executada: `pytest backend/tests/test_estoque_v2.py -q` com `8 passed`.
- Task geral permanece `pendente`, pois os proximos modulos (`pdv.py`, `ocr.py`, `produto.py` e demais) ainda nao foram migrados.
