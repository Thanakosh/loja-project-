---
task_id: TASK-021
title: "Implementar testes E2E do frontend com Playwright"
status: concluida
priority: alta
agent_chat_executable: "sim"
depends_on: ["TASK-019"]
---

## Objetivo

O `playwright.config.ts` ja foi adicionado ao projeto, mas ainda nao ha nenhum
teste E2E escrito. Criar suite minima de smoke tests para os fluxos criticos do
frontend.

### Escopo minimo

1. **Login:** email/senha invalidos exibe erro; credenciais validas redireciona
   para Dashboard.
2. **Dashboard:** apos login, cards de vendas e alertas de estoque sao renderizados.
3. **Vendas:** listagem carrega, paginacao funciona (Anterior/Proxima), modal de
   detalhes abre e fecha.
4. **PDV:** abrir tela, adicionar item, finalizar venda (happy path).

### Acoes

1. Instalar dependencias de Playwright (`npx playwright install`).
2. Criar pasta `frontend/e2e/` com testes separados por fluxo.
3. Adicionar script `npm run test:e2e` ao `package.json`.
4. Integrar no CI (`.github/workflows/`) como job opcional.

### Criterio de aceite

- 4+ testes passando localmente.
- `npm run test:e2e` roda sem erro.
