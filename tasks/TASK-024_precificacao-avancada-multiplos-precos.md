---
task_id: TASK-024
title: "Precificação avançada: custo, varejo e atacado"
status: pendente
priority: media
agent_chat_executable: "sim"
depends_on: []
---

## Objetivo

Conforme RECOMENDACOES_TECNICAS.md (item "Precificação Avançada") e STRATEGY.md
Fase 2, permitir múltiplos preços por produto.

### Backend

1. Adicionar campos ao modelo `Produto`: `preco_custo`, `preco_varejo`,
   `preco_atacado`, `qtd_minima_atacado`.
2. Migração Alembic para novos campos.
3. Atualizar schemas de criação/edição de produto.
4. PDV: aplicar preço atacado quando quantidade >= `qtd_minima_atacado`.

### Frontend

1. Formulário de Produto exibir os 3 campos de preço.
2. PDV: exibir indicador visual quando preço atacado é aplicado.

### Critério de aceite

- Produto tem 3 preços editáveis.
- PDV aplica automaticamente o preço correto.
- Testes para lógica de seleção de preço no PDV.
