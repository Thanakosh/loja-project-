---
task_id: TASK-040
title: "Testes E2E Playwright para fluxos criticos do frontend"
status: pendente
priority: media
agent_chat_executable: "sim"
depends_on: ["TASK-034"]
---

## Objetivo

Implementar testes end-to-end com Playwright cobrindo os fluxos de negocio
mais criticos do frontend, garantindo que regressoes sejam detectadas
automaticamente.

### Contexto

O projeto ja possui Playwright configurado (`playwright.config.ts`,
diretorio `e2e/`, reporter HTML e workflow de CI opcional).

Estado atual verificado em 2026-03-22:
- specs existentes para login, dashboard, vendas e PDV
- `npm run test:e2e` executa e passou com 5 testes locais
- a suite atual e majoritariamente smoke/UI com mocks de API
- workflow de CI foi endurecido para rodar em `push`/`pull_request`, sem
  `continue-on-error`, com upload do `playwright-report`
- `frontend/e2e/pdv.integration.spec.ts` agora cobre login real -> acesso ao
  PDV -> adicao de produto -> finalizacao de venda -> confirmacao da baixa
  de estoque no backend
- `npm run test:e2e:integrated` passou localmente com frontend e backend reais
  sobre PostgreSQL
- workflow `frontend-e2e` agora possui job integrado com backend real,
  `alembic upgrade head` e PostgreSQL 16 em CI

Lacuna remanescente:
- ainda faltam fluxos integrados e2e de produto, orcamento e importacao
  de nota
- a cobertura integrada real existe hoje apenas para o fluxo basico de PDV
- ainda faltam cenarios com regras de desconto, venda a prazo e cancelamento
  com estorno

### Pre-requisitos

- Backend rodando em `http://localhost:8000` com banco de testes.
- Frontend rodando em `http://localhost:5173` (Vite dev server).
- Usuario de teste criado (credentials definidas em fixture).

### Acoes

1. **Configurar fixtures de teste:**
   - Criar `frontend/e2e/fixtures/auth.ts` com login automatico
   - Criar `frontend/e2e/fixtures/test-data.ts` com dados de teste
     (produto, cliente, fornecedor de exemplo)

2. **Implementar testes por fluxo:**

   **Fluxo 1 - Login e Autenticacao (`e2e/auth.spec.ts`):**
   - Login valido  redireciona para dashboard
   - Login invalido  exibe mensagem de erro
   - Token expirado  refresh silencioso funciona
   - Logout  redireciona para login

   **Fluxo 2 - PDV Completo (`e2e/pdv.spec.ts`):**
   - Abrir caixa  adicionar produto  finalizar venda
   - Venda a prazo  gera contas a receber
   - Venda com desconto  respeita politica de desconto
   - Cancelar venda  estorna estoque

   **Fluxo 3 - Cadastro de Produto (`e2e/produtos.spec.ts`):**
   - Criar produto  aparece na listagem
   - Editar produto  valores atualizados
   - Desativar produto  some da listagem padrao

   **Fluxo 4 - Orcamento  Venda (`e2e/orcamentos.spec.ts`):**
   - Criar orcamento com itens  converter em venda
   - Cancelar orcamento  itens nao sao vendidos

   **Fluxo 5 - Importacao de Nota (`e2e/importar-nota.spec.ts`):**
   - Upload de XML valido  produto importado
   - Upload de arquivo invalido  mensagem de erro

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

### Proximo criterio de aceite

- 5 specs criados cobrindo os fluxos listados.
- Smoke tests e pelo menos 1 fluxo integrado real passando em execucao local.
- Gate integrado do CI passando com backend real e PostgreSQL.
- Screenshots de falha configurados corretamente.
- README do frontend atualizado com instrucoes de execucao dos testes E2E.

### Branch sugerida

`test/e2e-playwright-fluxos-criticos`
