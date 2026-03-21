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
- Modulo `pdv.py` migrado para `AsyncSession` em `refactor/async-pdv`, incluindo leitura, criacao, cancelamento de vendas e verificacao de preco minimo.
- `app/services/pdv_service.py` passou a expor funcoes async para evitar misturar `Session` e `AsyncSession` no mesmo fluxo.
- `app/services/configuracao_loja_service.py` recebeu helper async para suportar os calculos do PDV sem fallback sincrono.
- Validacao executada: `$env:DEBUG='false'; pytest backend/tests/test_pdv.py backend/tests/test_pdv_preco_minimo.py -q` com `32 passed`.
- Modulo `ocr.py` migrado para `AsyncSession` em `refactor/async-pdv`, mantendo a semantica atual do upload XML e dos endpoints desativados.
- Validacao executada: `$env:DEBUG='false'; pytest backend/tests/test_ocr.py backend/tests/test_ocr_fiscal_validation.py -q` com `16 passed`.
- Modulo `produto.py` migrado para `AsyncSession`, incluindo CRUD, filtros por categoria/barcode e paginacao.
- `app/core/pagination.py` recebeu helper `paginate_async()` para suportar listagens migradas sem manter `Query` sincrona no endpoint.
- Validacao executada: `$env:DEBUG='false'; pytest backend/tests/test_produto.py -q` com `39 passed`.
- Modulo `configuracoes.py` migrado para `AsyncSession`, reaproveitando o helper async de configuracao da loja ja usado por `pdv` e `ocr`.
- Validacao executada: `$env:DEBUG='false'; pytest backend/tests/test_configuracoes.py -q` com `3 passed`.
- Modulo `categorias.py` migrado para `AsyncSession`, incluindo CRUD, arvore hierarquica e listagem paginada.
- Validacao executada: `$env:DEBUG='false'; pytest backend/tests/test_categorias.py -q` com `3 passed`.
- Modulo `caixa.py` migrado para `AsyncSession`, incluindo abertura, fechamento, consulta do caixa atual e historico.
- `app/services/caixa_service.py` passou a expor funcoes async para manter o fluxo do router integralmente assincrono.
- Validacao executada: `$env:DEBUG='false'; pytest backend/tests/test_caixa.py -q` com `14 passed`.
- Modulo `clientes.py` migrado para `AsyncSession`, preservando busca por texto/codigo legado e o historico de observacoes/autorizacoes.
- Validacao executada: `$env:DEBUG='false'; pytest backend/tests/test_clientes.py -q` com `3 passed`.
- Modulo `fornecedores.py` migrado para `AsyncSession`, incluindo CRUD, busca textual, soft delete e reativacao.
- Validacao executada: `$env:DEBUG='false'; pytest backend/tests/test_fornecedores.py -q` com `15 passed`.
- Modulo `contas_receber.py` migrado para `AsyncSession`, incluindo resumo agregado, listagem paginada e baixa de conta.
- Validacao executada: `$env:DEBUG='false'; pytest backend/tests/test_contas_receber.py -q` com `4 passed`.
- Modulo `notas_fiscais.py` migrado para `AsyncSession`, incluindo listagem com filtros e carregamento de itens via eager loading.
- Validacao executada: `$env:DEBUG='false'; pytest backend/tests/test_notas_fiscais.py -q` com `3 passed`.
- `app/core/security.py` recebeu helpers async para autenticacao, emissao/rotacao de refresh token e revogacao de tokens, evitando misturar `Session` e `AsyncSession` no modulo de usuarios.
- Modulo `users.py` migrado para `AsyncSession`, incluindo login, refresh, logout, registro e listagem.
- Validacao executada: `$env:DEBUG='false'; pytest backend/tests/test_users.py -q` com `7 passed`.
- Modulo `orcamento.py` migrado para `AsyncSession`, incluindo CRUD, exportacao de PDF e conversao em venda via fluxo async do PDV.
- `app/core/pagination.py` passou a aplicar `unique()` em `paginate_async()` para suportar paginacao de queries com `joinedload` em colecoes.
- Validacao executada: `$env:DEBUG='false'; pytest backend/tests/test_orcamento.py -q` com `19 passed`.
- Modulo `relatorios.py` migrado para `AsyncSession`, incluindo exportacao de PDFs de vendas, estoque baixo e resumo mensal.
- Validacao executada: `$env:DEBUG='false'; pytest backend/tests/test_relatorios_pdf.py -q` com `3 passed`.
- Modulo `fiscal_ai.py` migrado para `AsyncSession`, incluindo sugestao de preco, auditoria de nota, dashboard de risco, classificacao NCM, ranking de fornecedores e feedback.
- Validacao executada: `$env:DEBUG='false'; pytest backend/tests/test_fiscal_ai.py -q` com `16 passed`.
- Modulo `vendas.py` migrado para `AsyncSession`, incluindo listagem paginada, resumo por periodo, detalhamento e listagem por cliente.
- Validacao indireta executada: `$env:DEBUG='false'; pytest backend/tests/test_pdv.py backend/tests/test_orcamento.py backend/tests/test_relatorios_pdf.py backend/tests/test_fiscal_ai.py -q` com `64 passed`.
- Task geral permanece `pendente`, pois os proximos modulos (demais endpoints sync) ainda nao foram migrados.
