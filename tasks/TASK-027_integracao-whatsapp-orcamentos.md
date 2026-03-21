---
task_id: TASK-027
title: "Integracao WhatsApp para envio de orcamentos e notificacoes"
status: pendente
priority: baixa
agent_chat_executable: "nao"
reason: "Requer configuracao de API WhatsApp Business e credenciais externas"
depends_on: ["TASK-026"]
---

## Objetivo

Conforme STRATEGY.md Fase 4 e RECOMENDACOES_TECNICAS.md, implementar envio de
orcamentos em PDF via WhatsApp e notificacoes de estoque baixo.

### Backend

1. Criar servico `WhatsAppService` com integracao a API do WhatsApp Business
   (ou Evolution API / Z-API).
2. Endpoint `POST /api/v1/orcamentos/{id}/enviar-whatsapp` - envia PDF ao
   telefone do cliente.
3. Notificacao automatica de estoque baixo (agendamento diario ou via webhook).

### Frontend

1. Botao "Enviar por WhatsApp" no modal do orcamento (exige telefone do cliente).
2. Configuracao de WhatsApp nas settings do sistema.

### Criterio de aceite

- Orcamento em PDF e enviado ao telefone do cliente.
- Notificacao de estoque baixo e enviada ao administrador.
- Testes de integracao com mock do servico WhatsApp.
