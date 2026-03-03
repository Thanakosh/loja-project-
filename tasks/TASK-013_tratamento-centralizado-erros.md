---
task_id: TASK-013
title: "Implementar tratamento centralizado de erros na API"
priority: 🟡 média
scope: backend/app/main.py, backend/app/core/, backend/tests/
branch: fix/error-handlers-globais
commit_message: "fix(api): padroniza tratamento global de erros com trace_id"
estimated_effort: 45 minutos
status: concluída
depends_on: []
recomendacao_ref: "#4 — Tratamento centralizado de erros"
---

# TASK-013: Tratamento centralizado de erros

## Contexto
Atualmente os erros são tratados de forma distribuída entre endpoints e middlewares.
Precisamos de um formato único de resposta de erro para reduzir inconsistência,
evitar vazamento de detalhes internos e facilitar troubleshooting.

## Objetivo
Padronizar resposta de erro no formato:
```json
{
  "code": "string",
  "message": "string",
  "details": {},
  "trace_id": "uuid"
}
```

## Critérios de aceite
- [x] Exception handlers globais registrados no FastAPI
- [x] Erros de validação retornam formato padronizado
- [x] Erros de negócio (ex.: estoque insuficiente) retornam `code` específico
- [x] `trace_id` presente em todas as respostas de erro
- [x] Testes automatizados cobrindo cenários principais
