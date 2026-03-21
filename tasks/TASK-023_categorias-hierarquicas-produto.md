---
task_id: TASK-023
title: "Categorias hierarquicas de produtos"
status: concluido
priority: media
agent_chat_executable: "sim"
depends_on: []
---

## Objetivo

Conforme RECOMENDACOES_TECNICAS.md (item "Categorias Hierarquicas") e STRATEGY.md
Fase 2, implementar arvore de categorias para produtos.

### Backend

1. Criar modelo `Categoria` (id, nome, parent_id FK self-referencing, ativo).
2. Endpoints CRUD: `GET/POST/PUT/DELETE /api/v1/categorias/`.
3. Endpoint `GET /api/v1/categorias/arvore` - retorna arvore hierarquica.
4. Adicionar FK `categoria_id` na tabela `Produto`.
5. Migracao Alembic.

### Frontend

1. Componente de selecao em arvore no cadastro de Produtos.
2. Filtro por categoria na listagem de Produtos.

### Criterio de aceite

- Categorias suportam pelo menos 3 niveis (ex.: Eletrico > Fios > 2.5mm).
- Filtro por categoria funciona na listagem.
- Testes de backend para CRUD e arvore.
