---
task_id: TASK-033
title: "Persistir feedback fiscal e rastreabilidade de sugestoes"
status: concluida
priority: media
agent_chat_executable: "sim"
depends_on: ["TASK-031", "TASK-032"]
---

## Objetivo

Criar base de aprendizado continuo com governanca, registrando feedback humano
sobre sugestoes fiscais e de precificacao.

### Acoes

1. Criar modelo/tabela `fiscal_feedback` com campos:
   - `origem_sugestao`
   - `versao_motor`
   - `user_id`
   - `created_at`
   - decisao do usuario
2. Gerar migracao Alembic para nova tabela sem alterar historico existente.
3. Implementar endpoint `POST /api/v1/fiscal-ai/feedback` autenticado.
4. Adicionar consulta inicial para metricas de aceitacao/rejeicao por tipo.
5. Cobrir fluxo com testes automatizados.

### Criterio de aceite

- Feedback fica persistido com rastreabilidade completa de origem e versao.
- Dados ficam prontos para uso em ajustes assincronos por lote.
