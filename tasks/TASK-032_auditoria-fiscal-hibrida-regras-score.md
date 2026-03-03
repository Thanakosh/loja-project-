---
task_id: TASK-032
title: "Iniciar auditoria fiscal híbrida (regras + score)"
status: pendente
priority: media
agent_chat_executable: "sim"
depends_on: ["TASK-030"]
---

## Objetivo

Criar a primeira versão da auditoria fiscal combinando validações
determinísticas com score de risco explicável.

### Ações

1. Implementar `backend/app/fiscal/engine.py` com regras de inconsistência:
   - CST incompatível com regime
   - alíquota fora de faixa esperada
   - outlier de preço por NCM
2. Criar estrutura inicial de `backend/app/ai/audit_service.py` para ranking
   de risco e explicações textuais.
3. Expor endpoint `POST /api/v1/fiscal-ai/validate-note` autenticado.
4. Retornar contrato com `classificacao`, `confianca`, `explicacao` e `fatores`.
5. Cobrir com testes unitários e integração de endpoint.

### Critério de aceite

- Auditoria classifica risco em `baixo`, `medio` ou `alto` com justificativa.
- Regras determinísticas continuam sendo a camada mandatória da decisão.
