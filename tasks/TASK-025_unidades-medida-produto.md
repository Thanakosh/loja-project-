---
task_id: TASK-025
title: "Unidades de medida flexíveis para produtos"
status: concluída
tested_by: TestUnidadeMedida (backend/tests/test_produto.py)
priority: media
agent_chat_executable: "sim"
depends_on: []
---

## Objetivo

Conforme RECOMENDACOES_TECNICAS.md (item "Unidades de Medida"), permitir que
produtos sejam vendidos por metro, unidade, kg etc.

### Backend

1. Criar tabela ou Enum `UnidadeMedida` (UN, MT, KG, CX, PC, etc.).
2. Adicionar campo `unidade_medida` no modelo `Produto` (default: UN).
3. Migração Alembic.
4. PDV: permitir quantidade fracionada quando unidade não é UN/CX.

### Frontend

1. Select de unidade de medida no cadastro de produto.
2. PDV: campo de quantidade aceitar decimais para unidades que permitem fração.
3. Exibir unidade na listagem e nos detalhes da venda.

### Critério de aceite

- Produto pode ter unidade diferente de "Unidade".
- PDV aceita quantidade fracionada (ex.: 2.5 metros).
- Testes para validação de quantidade fracionada.
