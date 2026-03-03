---
task_id: TASK-029
title: "Evoluir parser XML com campos fiscais por item"
status: pendente
priority: alta
agent_chat_executable: "sim"
depends_on: []
---

## Objetivo

Expandir o parser de NFe XML atual para coletar campos fiscais por item
necessários para auditoria e precificação (CFOP, CST, ICMS, frete rateado).

### Ações

1. Mapear lacunas do parser atual em `backend/app/core/nfe_parser.py`.
2. Adicionar extração por item para:
   - `cfop`
   - `cst` / `csosn`
   - base/alíquota/valor de ICMS
   - rateio de frete por item
3. Garantir compatibilidade com payload já consumido pelos endpoints atuais.
4. Criar testes cobrindo:
   - XML válido com tributação completa
   - XML sem alguns blocos fiscais opcionais
   - fallback seguro sem quebrar importação

### Critério de aceite

- Parser retorna os novos campos fiscais por item sem regressão do fluxo atual.
- Suíte de testes de importação XML permanece verde.
