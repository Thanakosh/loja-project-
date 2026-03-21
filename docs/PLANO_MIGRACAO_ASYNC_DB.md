# Plano incremental de convergencia para AsyncEngine/AsyncSession

## 1) Motivacao tecnica

A migracao de acesso a banco para SQLAlchemy assincrono (`AsyncEngine` + `AsyncSession`) reduz pontos de bloqueio da aplicacao FastAPI em cenarios com alto I/O, melhora a eficiencia de concorrencia por worker e prepara a base para modulos com picos de latencia externa (OCR e integracoes) sem saturar threads sincronas.

Ganhos esperados:
- melhor throughput em endpoints de leitura/escrita com espera de banco;
- menor contencao de pool em bursts de requisicoes;
- alinhamento com stack ja preparada (`asyncpg` e `aiosqlite` presentes);
- base tecnica para evolucao gradual sem big-bang.

## 2) Inventario dos endpoints por risco de migracao

### Baixo risco (CRUD simples, baixo acoplamento transacional)

- `GET/POST/PUT/DELETE /api/v1/clientes/*`
- `GET/POST/PUT/DELETE /api/v1/fornecedores/*`
- `GET/POST/PUT/DELETE /api/v1/categorias/*`

**Justificativa:** predominancia de operacoes diretas em tabela unica, menor dependencia de fluxos multi-etapas.

### Medio risco (fluxos com multiplas entidades e regras de composicao)

- `/api/v1/pdv/*`
- `/api/v1/orcamentos/*`
- `/api/v1/vendas/*`
- `/api/v1/contas-receber/*`

**Justificativa:** fluxos com validacoes em cadeia, persistencia coordenada e potencial de regressao funcional se a ordem transacional mudar.

### Alto risco (transacoes criticas e logica de consistencia forte)

- `/api/v2/estoque/*` e `/api/v1/movimentacao/*`
- `/api/v1/ocr/*`
- `/api/v1/notas-fiscais/*`

**Justificativa:** modulos com maior volume de I/O, side-effects e criticidade de consistencia de dados.

## 3) Fases propostas

### Fase 1 - Infraestrutura base (coexistencia)

Objetivo:
- manter engine/sessao sincrona atuais;
- adicionar `async_engine`, `AsyncSessionLocal` e dependency `get_async_db`;
- incluir endpoint POC de saude async para validacao continua.

Entregaveis:
- camada core de banco suportando sync + async;
- cobertura de teste para endpoint async de prova de vida.

### Fase 2 - Migracao de baixo risco (1-2 candidatos)

Candidatos sugeridos:
1. `clientes`
2. `categorias`

Objetivo:
- migrar apenas rotas selecionadas para `async def` com `AsyncSession`;
- preservar contratos de request/response;
- validar regressao por suite de testes do modulo.

Criterios de saida:
- cobertura de testes do modulo migrado sem regressao;
- metricas estaveis de erro e latencia por 1 ciclo de release.

### Fase 3 - Modulos de maior I/O

Escopo priorizado:
1. estoque v2
2. OCR

Objetivo:
- reduzir bloqueio em operacoes de escrita intensiva e pipelines de processamento;
- consolidar padroes de transacao async (`async with session.begin()` quando aplicavel).

Criterios de saida:
- estabilidade de consistencia transacional;
- ausencia de aumento de incidentes de concorrencia/lock.

## 4) Estrategia de coexistencia sync/async

Durante a migracao:
- manter `get_db` (sync) e `get_async_db` (async) em paralelo;
- novos endpoints podem nascer em async sem exigir migracao imediata dos legados;
- migracao por modulo, com rollback independente;
- evitar mistura de sessao sync e async na mesma unidade de trabalho.

## 5) Criterios de rollback por fase

### Fase 1
Rollback se:
- falhas de inicializacao da aplicacao por URL/driver async;
- falhas recorrentes no endpoint de saude async.

Acao:
- desabilitar rota POC e retornar ao uso exclusivo de `get_db`.

### Fase 2
Rollback se:
- aumento de erros 5xx no modulo migrado;
- quebra de compatibilidade de resposta;
- degradacao de latencia acima do baseline acordado.

Acao:
- reverter endpoints do modulo para sessao sync.

### Fase 3
Rollback se:
- inconsistencia de estoque/transacoes detectada;
- jobs OCR com falha de persistencia/timeout elevado;
- aumento de incidentes criticos em producao.

Acao:
- rollback por submodulo (estoque e OCR independentes), mantendo infraestrutura async disponivel.

## 6) Impacto nos testes

`backend/tests/conftest.py` deve evoluir para suportar tambem fixtures assincronas, incluindo:
- engine async de testes com `sqlite+aiosqlite`;
- fixture de `AsyncSession` para testes de endpoints migrados;
- estrategia de isolamento transacional equivalente ao ambiente sync.

Nesta etapa (POC), mantem-se o setup sync existente e adiciona-se teste de endpoint async para garantir nao regressao da infraestrutura.
