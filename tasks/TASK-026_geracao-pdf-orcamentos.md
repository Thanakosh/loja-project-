---
task_id: TASK-026
title: "Geração de PDF para orçamentos"
status: concluída
priority: media
agent_chat_executable: "sim"
depends_on: []
---

## Objetivo

Conforme STRATEGY.md (Comunicação & Vendas), gerar PDF profissional de orçamentos
para envio ao cliente.

### Backend

1. Adicionar dependência `weasyprint` ou `reportlab` no `requirements.txt`.
2. Criar endpoint `GET /api/v1/orcamentos/{id}/pdf` que retorna PDF.
3. Template com: dados da empresa, dados do cliente, itens do orçamento,
   validade, condições de pagamento e total.

### Frontend

1. Botão "Exportar PDF" no modal de detalhes do orçamento.
2. Abrir PDF em nova aba ou iniciar download.

### Critério de aceite

- PDF gerado contém todos os dados do orçamento.
- Layout profissional com logo da empresa.
- Teste de backend que gera PDF e valida HTTP 200 + content-type.
