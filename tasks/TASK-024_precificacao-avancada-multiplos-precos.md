---
task_id: TASK-024
title: "Precificacao avancada: custo, varejo e atacado"
status: concluida
priority: media
agent_chat_executable: "sim"
depends_on: []
---

## Objetivo

Conforme RECOMENDACOES_TECNICAS.md (item "Precificacao Avancada") e STRATEGY.md
Fase 2, permitir multiplos precos por produto.

### Backend

1. Adicionar campos ao modelo `Produto`: `preco_custo`, `preco_varejo`,
   `preco_atacado`, `qtd_minima_atacado`.
2. Migracao Alembic para novos campos.
3. Atualizar schemas de criacao/edicao de produto.
4. PDV: aplicar preco atacado quando quantidade >= `qtd_minima_atacado`.

### Frontend

1. Formulario de Produto exibir os 3 campos de preco.
2. PDV: exibir indicador visual quando preco atacado e aplicado.

### Criterio de aceite

- Produto tem 3 precos editaveis.
- PDV aplica automaticamente o preco correto.
- Testes para logica de selecao de preco no PDV.
