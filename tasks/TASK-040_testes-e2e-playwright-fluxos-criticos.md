---
task_id: TASK-040
title: "Testes E2E Playwright para fluxos críticos do frontend"
status: pendente
priority: media
agent_chat_executable: "sim"
depends_on: ["TASK-034"]
---

## Objetivo

Implementar testes end-to-end com Playwright cobrindo os fluxos de negócio
mais críticos do frontend, garantindo que regressões sejam detectadas
automaticamente.

### Contexto

O projeto possui Playwright configurado (`playwright.config.ts`, diretórios
`e2e/`, `tests/`, `playwright-report/`) mas sem testes substanciais. O
frontend tem 15 páginas e nenhum teste automatizado validando fluxos de
usuário completos.

### Pré-requisitos

- Backend rodando em `http://localhost:8000` com banco de testes.
- Frontend rodando em `http://localhost:5173` (Vite dev server).
- Usuário de teste criado (credentials definidas em fixture).

### Ações

1. **Configurar fixtures de teste:**
   - Criar `frontend/e2e/fixtures/auth.ts` com login automático
   - Criar `frontend/e2e/fixtures/test-data.ts` com dados de teste
     (produto, cliente, fornecedor de exemplo)

2. **Implementar testes por fluxo:**

   **Fluxo 1 — Login e Autenticação (`e2e/auth.spec.ts`):**
   - Login válido → redireciona para dashboard
   - Login inválido → exibe mensagem de erro
   - Token expirado → refresh silencioso funciona
   - Logout → redireciona para login

   **Fluxo 2 — PDV Completo (`e2e/pdv.spec.ts`):**
   - Abrir caixa → adicionar produto → finalizar venda
   - Venda a prazo → gera contas a receber
   - Venda com desconto → respeita política de desconto
   - Cancelar venda → estorna estoque

   **Fluxo 3 — Cadastro de Produto (`e2e/produtos.spec.ts`):**
   - Criar produto → aparece na listagem
   - Editar produto → valores atualizados
   - Desativar produto → some da listagem padrão

   **Fluxo 4 — Orçamento → Venda (`e2e/orcamentos.spec.ts`):**
   - Criar orçamento com itens → converter em venda
   - Cancelar orçamento → itens não são vendidos

   **Fluxo 5 — Importação de Nota (`e2e/importar-nota.spec.ts`):**
   - Upload de XML válido → produto importado
   - Upload de arquivo inválido → mensagem de erro

3. **Configurar `playwright.config.ts`:**
   - Base URL: `http://localhost:5173`
   - Screenshot on failure
   - Retry: 1
   - Workers: 1 (para evitar conflito de estado)

4. **Adicionar script no `package.json`:**
   ```json
   "test:e2e": "playwright test e2e/",
   "test:e2e:ui": "playwright test e2e/ --ui"
   ```

### Critério de aceite

- 5 specs criados cobrindo os fluxos listados.
- Todos os testes passando em execução local.
- Screenshots de falha configurados corretamente.
- README do frontend atualizado com instruções de execução dos testes E2E.

### Branch sugerida

`test/e2e-playwright-fluxos-criticos`
