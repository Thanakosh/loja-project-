---
task_id: TASK-022
title: "Implementar controle de caixa diário (abertura/fechamento)"
status: concluída
priority: media
agent_chat_executable: "sim"
depends_on: []
---

## Objetivo

Conforme STRATEGY.md Fase 3 e RECOMENDACOES_TECNICAS.md item "Financeiro",
implementar o módulo de controle de caixa diário.

### Backend

1. Criar modelo `CaixaDiario` (id, data_abertura, data_fechamento, valor_abertura,
   valor_fechamento, status, usuario_id).
2. Endpoints:
   - `POST /api/v1/caixa/abrir` — abre caixa com valor inicial.
   - `POST /api/v1/caixa/fechar` — fecha caixa com conferência.
   - `GET /api/v1/caixa/atual` — retorna caixa aberto do dia.
   - `GET /api/v1/caixa/historico` — listagem paginada.
3. Vincular vendas do PDV ao caixa aberto.

### Frontend

1. Nova página `CaixaDiario.tsx` com abertura, fechamento e histórico.
2. Bloquear PDV se caixa não estiver aberto (aviso visual).

### Critério de aceite

- Não é possível registrar venda no PDV sem caixa aberto.
- Conferência de fechamento exibe diferença (se houver).
- Testes de backend para abrir, fechar e listar caixa.
