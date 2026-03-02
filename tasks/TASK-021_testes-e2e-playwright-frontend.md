---
task_id: TASK-021
title: "Implementar testes E2E do frontend com Playwright"
status: concluida
priority: alta
agent_chat_executable: "sim"
depends_on: ["TASK-019"]
---

## Objetivo

O `playwright.config.ts` já foi adicionado ao projeto, mas ainda não há nenhum
teste E2E escrito. Criar suíte mínima de smoke tests para os fluxos críticos do
frontend.

### Escopo mínimo

1. **Login:** email/senha inválidos exibe erro; credenciais válidas redireciona
   para Dashboard.
2. **Dashboard:** após login, cards de vendas e alertas de estoque são renderizados.
3. **Vendas:** listagem carrega, paginação funciona (Anterior/Próxima), modal de
   detalhes abre e fecha.
4. **PDV:** abrir tela, adicionar item, finalizar venda (happy path).

### Ações

1. Instalar dependências de Playwright (`npx playwright install`).
2. Criar pasta `frontend/e2e/` com testes separados por fluxo.
3. Adicionar script `npm run test:e2e` ao `package.json`.
4. Integrar no CI (`.github/workflows/`) como job opcional.

### Critério de aceite

- 4+ testes passando localmente.
- `npm run test:e2e` roda sem erro.
