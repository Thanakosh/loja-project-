---
task_id: TASK-027
title: "Integração WhatsApp para envio de orçamentos e notificações"
status: pendente
priority: baixa
agent_chat_executable: "nao"
reason: "Requer configuração de API WhatsApp Business e credenciais externas"
depends_on: ["TASK-026"]
---

## Objetivo

Conforme STRATEGY.md Fase 4 e RECOMENDACOES_TECNICAS.md, implementar envio de
orçamentos em PDF via WhatsApp e notificações de estoque baixo.

### Backend

1. Criar serviço `WhatsAppService` com integração à API do WhatsApp Business
   (ou Evolution API / Z-API).
2. Endpoint `POST /api/v1/orcamentos/{id}/enviar-whatsapp` — envia PDF ao
   telefone do cliente.
3. Notificação automática de estoque baixo (agendamento diário ou via webhook).

### Frontend

1. Botão "Enviar por WhatsApp" no modal do orçamento (exige telefone do cliente).
2. Configuração de WhatsApp nas settings do sistema.

### Critério de aceite

- Orçamento em PDF é enviado ao telefone do cliente.
- Notificação de estoque baixo é enviada ao administrador.
- Testes de integração com mock do serviço WhatsApp.
