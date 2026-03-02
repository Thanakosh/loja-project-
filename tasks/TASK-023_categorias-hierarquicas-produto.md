---
task_id: TASK-023
title: "Categorias hierárquicas de produtos"
status: pendente
priority: media
agent_chat_executable: "sim"
depends_on: []
---

## Objetivo

Conforme RECOMENDACOES_TECNICAS.md (item "Categorias Hierárquicas") e STRATEGY.md
Fase 2, implementar árvore de categorias para produtos.

### Backend

1. Criar modelo `Categoria` (id, nome, parent_id FK self-referencing, ativo).
2. Endpoints CRUD: `GET/POST/PUT/DELETE /api/v1/categorias/`.
3. Endpoint `GET /api/v1/categorias/arvore` — retorna árvore hierárquica.
4. Adicionar FK `categoria_id` na tabela `Produto`.
5. Migração Alembic.

### Frontend

1. Componente de seleção em árvore no cadastro de Produtos.
2. Filtro por categoria na listagem de Produtos.

### Critério de aceite

- Categorias suportam pelo menos 3 níveis (ex.: Elétrico > Fios > 2.5mm).
- Filtro por categoria funciona na listagem.
- Testes de backend para CRUD e árvore.
