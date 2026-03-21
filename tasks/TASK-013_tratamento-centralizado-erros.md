---
task_id: TASK-013
title: "Implementar tratamento centralizado de erros na API"
priority: media
scope: backend/app/main.py, backend/app/core/, backend/tests/
branch: fix/error-handlers-globais
commit_message: "fix(api): padroniza tratamento global de erros com trace_id"
estimated_effort: 45 minutos
status: concluida
depends_on: []
recomendacao_ref: "#4 Tratamento centralizado de erros"
---

# TASK-013: Tratamento centralizado de erros

## Contexto
Atualmente os erros sao tratados de forma distribuida entre endpoints e middlewares.
Precisamos de um formato unico de resposta de erro para reduzir inconsistencia,
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

## Criterios de aceite
- [x] Exception handlers globais registrados no FastAPI
- [x] Erros de validacao retornam formato padronizado
- [x] Erros de negocio (ex.: estoque insuficiente) retornam `code` especifico
- [x] `trace_id` presente em todas as respostas de erro
- [x] Testes automatizados cobrindo cenarios principais
