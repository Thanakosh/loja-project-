# Plano incremental de convergência para AsyncEngine/AsyncSession

## 1) Motivação técnica

A migração de acesso a banco para SQLAlchemy assíncrono (`AsyncEngine` + `AsyncSession`) reduz pontos de bloqueio da aplicação FastAPI em cenários com alto I/O, melhora a eficiência de concorrência por worker e prepara a base para módulos com picos de latência externa (OCR e integrações) sem saturar threads síncronas.

Ganhos esperados:
- melhor throughput em endpoints de leitura/escrita com espera de banco;
- menor contenção de pool em bursts de requisições;
- alinhamento com stack já preparada (`asyncpg` e `aiosqlite` presentes);
- base técnica para evolução gradual sem big-bang.

## 2) Inventário dos endpoints por risco de migração

### Baixo risco (CRUD simples, baixo acoplamento transacional)

- `GET/POST/PUT/DELETE /api/v1/clientes/*`
- `GET/POST/PUT/DELETE /api/v1/fornecedores/*`
- `GET/POST/PUT/DELETE /api/v1/categorias/*`

**Justificativa:** predominância de operações diretas em tabela única, menor dependência de fluxos multi-etapas.

### Médio risco (fluxos com múltiplas entidades e regras de composição)

- `/api/v1/pdv/*`
- `/api/v1/orcamentos/*`
- `/api/v1/vendas/*`
- `/api/v1/contas-receber/*`

**Justificativa:** fluxos com validações em cadeia, persistência coordenada e potencial de regressão funcional se a ordem transacional mudar.

### Alto risco (transações críticas e lógica de consistência forte)

- `/api/v2/estoque/*` e `/api/v1/movimentacao/*`
- `/api/v1/ocr/*`
- `/api/v1/notas-fiscais/*`

**Justificativa:** módulos com maior volume de I/O, side-effects e criticidade de consistência de dados.

## 3) Fases propostas

### Fase 1 — Infraestrutura base (coexistência)

Objetivo:
- manter engine/sessão síncrona atuais;
- adicionar `async_engine`, `AsyncSessionLocal` e dependency `get_async_db`;
- incluir endpoint POC de saúde async para validação contínua.

Entregáveis:
- camada core de banco suportando sync + async;
- cobertura de teste para endpoint async de prova de vida.

### Fase 2 — Migração de baixo risco (1–2 candidatos)

Candidatos sugeridos:
1. `clientes`
2. `categorias`

Objetivo:
- migrar apenas rotas selecionadas para `async def` com `AsyncSession`;
- preservar contratos de request/response;
- validar regressão por suíte de testes do módulo.

Critérios de saída:
- cobertura de testes do módulo migrado sem regressão;
- métricas estáveis de erro e latência por 1 ciclo de release.

### Fase 3 — Módulos de maior I/O

Escopo priorizado:
1. estoque v2
2. OCR

Objetivo:
- reduzir bloqueio em operações de escrita intensiva e pipelines de processamento;
- consolidar padrões de transação async (`async with session.begin()` quando aplicável).

Critérios de saída:
- estabilidade de consistência transacional;
- ausência de aumento de incidentes de concorrência/lock.

## 4) Estratégia de coexistência sync/async

Durante a migração:
- manter `get_db` (sync) e `get_async_db` (async) em paralelo;
- novos endpoints podem nascer em async sem exigir migração imediata dos legados;
- migração por módulo, com rollback independente;
- evitar mistura de sessão sync e async na mesma unidade de trabalho.

## 5) Critérios de rollback por fase

### Fase 1
Rollback se:
- falhas de inicialização da aplicação por URL/driver async;
- falhas recorrentes no endpoint de saúde async.

Ação:
- desabilitar rota POC e retornar ao uso exclusivo de `get_db`.

### Fase 2
Rollback se:
- aumento de erros 5xx no módulo migrado;
- quebra de compatibilidade de resposta;
- degradação de latência acima do baseline acordado.

Ação:
- reverter endpoints do módulo para sessão sync.

### Fase 3
Rollback se:
- inconsistência de estoque/transações detectada;
- jobs OCR com falha de persistência/timeout elevado;
- aumento de incidentes críticos em produção.

Ação:
- rollback por submódulo (estoque e OCR independentes), mantendo infraestrutura async disponível.

## 6) Impacto nos testes

`backend/tests/conftest.py` deve evoluir para suportar também fixtures assíncronas, incluindo:
- engine async de testes com `sqlite+aiosqlite`;
- fixture de `AsyncSession` para testes de endpoints migrados;
- estratégia de isolamento transacional equivalente ao ambiente sync.

Nesta etapa (POC), mantém-se o setup sync existente e adiciona-se teste de endpoint async para garantir não regressão da infraestrutura.
