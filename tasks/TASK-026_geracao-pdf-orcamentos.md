---
task_id: TASK-026
title: "Geracao de PDF para orcamentos"
status: concluida
priority: media
agent_chat_executable: "sim"
depends_on: []
---

## Objetivo

Conforme STRATEGY.md (Comunicacao & Vendas), gerar PDF profissional de orcamentos
para envio ao cliente.

### Backend

1. Adicionar dependencia `weasyprint` ou `reportlab` no `requirements.txt`.
2. Criar endpoint `GET /api/v1/orcamentos/{id}/pdf` que retorna PDF.
3. Template com: dados da empresa, dados do cliente, itens do orcamento,
   validade, condicoes de pagamento e total.

### Frontend

1. Botao "Exportar PDF" no modal de detalhes do orcamento.
2. Abrir PDF em nova aba ou iniciar download.

### Criterio de aceite

- PDF gerado contem todos os dados do orcamento.
- Layout profissional com logo da empresa.
- Teste de backend que gera PDF e valida HTTP 200 + content-type.
