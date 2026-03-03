---
task_id: TASK-033
title: "Persistir feedback fiscal e rastreabilidade de sugestões"
status: pendente
priority: media
agent_chat_executable: "sim"
depends_on: ["TASK-031", "TASK-032"]
---

## Objetivo

Criar base de aprendizado contínuo com governança, registrando feedback humano
sobre sugestões fiscais e de precificação.

### Ações

1. Criar modelo/tabela `fiscal_feedback` com campos:
   - `origem_sugestao`
   - `versao_motor`
   - `user_id`
   - `created_at`
   - decisão do usuário
2. Gerar migração Alembic para nova tabela sem alterar histórico existente.
3. Implementar endpoint `POST /api/v1/fiscal-ai/feedback` autenticado.
4. Adicionar consulta inicial para métricas de aceitação/rejeição por tipo.
5. Cobrir fluxo com testes automatizados.

### Critério de aceite

- Feedback fica persistido com rastreabilidade completa de origem e versão.
- Dados ficam prontos para uso em ajustes assíncronos por lote.
