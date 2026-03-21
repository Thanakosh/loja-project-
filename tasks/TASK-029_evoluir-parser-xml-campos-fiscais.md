---
task_id: TASK-029
title: "Evoluir parser XML com campos fiscais por item"
status: concluida
priority: alta
agent_chat_executable: "sim"
depends_on: []
---

## Objetivo

Expandir o parser de NFe XML atual para coletar campos fiscais por item
necessarios para auditoria e precificacao (CFOP, CST, ICMS, frete rateado).

### Acoes

1. Mapear lacunas do parser atual em `backend/app/core/nfe_parser.py`.
2. Adicionar extracao por item para:
   - `cfop`
   - `cst` / `csosn`
   - base/aliquota/valor de ICMS
   - rateio de frete por item
3. Garantir compatibilidade com payload ja consumido pelos endpoints atuais.
4. Criar testes cobrindo:
   - XML valido com tributacao completa
   - XML sem alguns blocos fiscais opcionais
   - fallback seguro sem quebrar importacao

### Criterio de aceite

- Parser retorna os novos campos fiscais por item sem regressao do fluxo atual.
- Suite de testes de importacao XML permanece verde.
