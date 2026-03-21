---
task_id: TASK-032
title: "Iniciar auditoria fiscal hibrida (regras + score)"
status: concluida
priority: media
agent_chat_executable: "sim"
depends_on: ["TASK-030"]
---

## Objetivo

Criar a primeira versao da auditoria fiscal combinando validacoes
deterministicas com score de risco explicavel.

### Acoes

1. Implementar `backend/app/fiscal/engine.py` com regras de inconsistencia:
   - CST incompativel com regime
   - aliquota fora de faixa esperada
   - outlier de preco por NCM
2. Criar estrutura inicial de `backend/app/ai/audit_service.py` para ranking
   de risco e explicacoes textuais.
3. Expor endpoint `POST /api/v1/fiscal-ai/validate-note` autenticado.
4. Retornar contrato com `classificacao`, `confianca`, `explicacao` e `fatores`.
5. Cobrir com testes unitarios e integracao de endpoint.

### Criterio de aceite

- Auditoria classifica risco em `baixo`, `medio` ou `alto` com justificativa.
- Regras deterministicas continuam sendo a camada mandatoria da decisao.
