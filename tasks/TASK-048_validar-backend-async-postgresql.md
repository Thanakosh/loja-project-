---
task_id: TASK-048
title: "Validar backend async em PostgreSQL"
status: concluida
priority: baixa
agent_chat_executable: "sim"
depends_on: ["TASK-042"]
---

## Objetivo

Executar uma validacao complementar do backend assincrono usando PostgreSQL,
confirmando que a migracao concluida em `TASK-042` tambem se comporta como
esperado fora do fluxo local baseado em SQLite.

### Contexto

A `TASK-042` concluiu a migracao da camada HTTP e da infraestrutura principal
para `AsyncSession`, com cobertura funcional ampla em testes locais. A
validacao em PostgreSQL nao e bloqueadora para o encerramento da migracao, mas
segue recomendada antes de merge mais rigoroso ou release.

### Atualizacao de execucao - 2026-03-22

Validacao complementar executada com PostgreSQL real em `localhost:5432`,
usando a base descartavel `loja_validacao` e o runner dedicado
`backend/scripts/validate_async_postgresql.py`.

Fluxo validado em PostgreSQL:
- `GET /api/v2/health-async`
- `POST /api/v1/users/register`
- `POST /api/v1/users/token`
- `GET /api/v1/users/me`
- `GET/PUT /api/v1/configuracoes/loja`
- `POST /api/v1/produtos/`
- `GET /api/v2/estoque/produto/{id}`
- `POST /api/v2/estoque/transacao`
- `POST /api/v1/caixa/abrir`
- `POST /api/v1/pdv/venda`

Resultado observado:
- stack async com `DATABASE_URL=postgresql://...` passou ponta a ponta
- estoque final validado em `10.0` apos criar produto com estoque inicial `5`,
  registrar entrada `+7` e concluir venda `-2`
- runner tambem passou no Windows com override `VALIDATION_RESET_SCHEMA=1`,
  recriando o schema a partir dos modelos para validar o runtime real

Correcao aplicada durante a validacao:
- `backend/app/models/transacao_estoque.py` passou a gerar `datetime` UTC
  ingenuo, alinhado ao schema atual
- `backend/app/services/caixa_service.py` passou a gravar datas de abertura e
  fechamento com UTC ingenuo
- isso removeu a regressao real do `asyncpg` em PostgreSQL:
  `can't subtract offset-naive and offset-aware datetimes`

Divergencia documentada:
- `alembic -c alembic.ini upgrade head` ainda falha em banco vazio na migracao
  `migrations/versions/20260214_refactor_estoque_transacoes.py`
- o erro ocorre porque a migracao tenta criar `transacao_estoque` antes de
  existir a relacao `produto`
- isso caracteriza um problema separado na chain de bootstrap das migracoes e
  foi formalizado na `TASK-049`
- seguimento encerrado em `2026-03-23`: a `TASK-049` corrigiu o bootstrap do
  Alembic em PostgreSQL vazio e validou o runtime sobre o schema migrado

Validacoes complementares desta sessao:
- `pytest tests/test_caixa.py tests/test_estoque_v2.py tests/test_pdv.py -q`
  -> `48 passed`
- runner PostgreSQL real com `DATABASE_URL=postgresql://...` -> `passou`

### Acoes

1. Preparar ambiente de teste com PostgreSQL e driver async (`asyncpg`).
2. Configurar `DATABASE_URL` para um banco PostgreSQL descartavel de validacao.
3. Rodar uma bateria minima focada nos fluxos assincronos criticos:
   - `backend/tests/test_users.py`
   - `backend/tests/test_pdv.py`
   - `backend/tests/test_pdv_preco_minimo.py`
   - `backend/tests/test_caixa.py`
   - `backend/tests/test_configuracoes.py`
4. Registrar diferencas de comportamento entre SQLite e PostgreSQL, se houver.
5. Atualizar esta task com o resultado da validacao.

### Criterio de aceite

- Ambiente PostgreSQL de validacao sobe sem ajustes manuais nao documentados.
- Bateria minima async executa sem regressao critica.
- Eventuais divergencias de dialeto/transacao ficam documentadas.

### Branch sugerida

`docs/validar-backend-async-postgresql`
