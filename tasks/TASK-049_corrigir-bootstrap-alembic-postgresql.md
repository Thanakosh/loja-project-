---
task_id: TASK-049
title: "Corrigir bootstrap Alembic em PostgreSQL vazio"
status: concluida
priority: arquitetura
agent_chat_executable: "sim"
depends_on: ["TASK-048"]
---

## Objetivo

Corrigir a chain de migracoes do Alembic para que `alembic upgrade head`
consiga montar o schema completo em um banco PostgreSQL vazio, sem depender de
`Base.metadata.create_all()` nem de estado legado preexistente.

### Contexto

Durante a validacao real da stack async em PostgreSQL da `TASK-048`, o runtime
da aplicacao passou com sucesso, mas o bootstrap via Alembic falhou em banco
vazio.

Falha observada:
- migracao: `migrations/versions/20260214_refactor_estoque_transacoes.py`
- erro: tentativa de criar `transacao_estoque` com FK para `produto.id`
  antes de a tabela `produto` existir no banco

Isso indica que a chain historica de migracoes nao reproduz corretamente o
schema atual a partir do estado zero.

### Atualizacao de execucao - 2026-03-23

Bootstrap corrigido e validado em PostgreSQL real (`loja_validacao`).

Correcao aplicada:
- `migrations/env.py` agora normaliza URLs `postgresql://` para
  `postgresql+psycopg://` no caminho sincrono do Alembic e garante
  `alembic_version.version_num` com capacidade suficiente para revision IDs
  longos no PostgreSQL.
- `migrations/versions/20260214_refactor_estoque_transacoes.py` passou a
  bootstrapar de forma idempotente as tabelas-base legadas necessarias antes de
  criar `transacao_estoque` e indices associados.
- `migrations/versions/20260221_refactor_orcamento.py` foi ajustada para
  preservar `orcamento` legado apenas quando existir e criar a nova estrutura
  de forma condicional em banco vazio.
- `migrations/versions/20260308_adiciona_campos_feedback_fiscal.py` passou a
  converter enums para texto de forma compativel com PostgreSQL antes das
  atualizacoes com `REPLACE()`.

Validacoes executadas:
- `alembic -c alembic.ini upgrade head` em schema PostgreSQL vazio -> `passou`
- `python backend/scripts/validate_async_postgresql.py` com `PYTHONPATH=backend`
  e schema criado por migracoes -> `passou`
- `pytest tests/test_caixa.py tests/test_estoque_v2.py tests/test_pdv.py -q`
  -> `48 passed`

Resultado:
- a chain do Alembic agora monta o schema completo a partir do estado zero em
  PostgreSQL
- o schema gerado por migracoes ficou compativel com o runtime async validado
  pela aplicacao real
- o bootstrap alternativo via `Base.metadata.create_all()` deixou de ser
  necessario para validar o ambiente PostgreSQL

### Acoes

1. Revisar a ordem e o conteudo das migracoes desde `5065442b792a`.
2. Identificar quais tabelas-base (`produto`, `user` e correlatas) nao estao
   sendo criadas no bootstrap.
3. Corrigir a chain preservando o historico do Alembic, sem apagar migracoes
   antigas.
4. Validar `alembic upgrade head` em banco PostgreSQL vazio.
5. Validar tambem `alembic downgrade` no escopo seguro necessario.
6. Registrar a estrategia adotada nesta task e no changelog, se aplicavel.

### Criterio de aceite

- `alembic -c alembic.ini upgrade head` passa em um banco PostgreSQL vazio.
- O schema final criado por migracoes fica compativel com o schema usado pelo
  runtime atual da aplicacao.
- Nao ha dependencia de bootstrap alternativo via `Base.metadata.create_all()`.

### Branch sugerida

`fix/alembic-bootstrap-postgresql`
