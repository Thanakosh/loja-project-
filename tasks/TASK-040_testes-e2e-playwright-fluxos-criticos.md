---
task_id: TASK-040
title: "Testes E2E Playwright para fluxos criticos do frontend"
status: concluida
priority: media
agent_chat_executable: "sim"
depends_on: ["TASK-034"]
---

## Objetivo

Expandir e estabilizar a suite E2E com Playwright para cobrir os fluxos de
negocio mais criticos do frontend, reduzindo regressao funcional em telas
centrais e consolidando a execucao no fluxo de desenvolvimento.

### Contexto

O repositorio ja possui uma base funcional de Playwright no frontend:

- `frontend/playwright.config.ts` configurado com `baseURL`, `retries`,
  screenshots em falha, video e trace no retry
- script `test:e2e` em `frontend/package.json`
- workflow opcional `Frontend E2E (Optional)` em
  `.github/workflows/frontend-e2e.yml`
- specs ativos em `frontend/e2e/` cobrindo login, dashboard, PDV e vendas
- helpers de mock em `frontend/e2e/helpers.ts`

Portanto, esta task nao trata mais de "iniciar Playwright do zero". O foco
correto passou a ser completar a cobertura dos fluxos criticos restantes,
padronizar fixtures e estabilizar a execucao dos smoke tests.

### Pre-requisitos

- Dependencias do frontend instaladas.
- Execucao local via `npm run test:e2e` em `frontend/`.
- Mocks E2E suficientes para nao depender de backend real nos fluxos smoke.
- Quando necessario, backend de apoio rodando para fluxos nao mockados.

### Estado atual

Concluido:

- fluxo de login com sucesso e erro
- fluxo basico de dashboard apos autenticacao
- fluxo feliz basico de PDV
- fluxo basico de listagem de vendas
- workflow opcional de CI para smoke E2E
- cobertura de produtos
- cobertura de orcamentos
- cobertura de importacao de nota
- consolidacao de fixtures reutilizaveis
- documentacao de execucao E2E no frontend
- decisao explicita sobre paralelismo (`workers`) e estabilidade do smoke em CI

Validado:

- fixture reutilizavel para sessao autenticada em `frontend/e2e/fixtures.ts`
- helpers padronizados de resposta/mock em `frontend/e2e/helpers.ts`
- suite completa passando localmente com `npm run test:e2e`
- 13 testes aprovados cobrindo login, dashboard, PDV, vendas, produtos,
  orcamentos e importacao de nota XML

### Acoes

1. **Consolidar infra de testes E2E:**
   - avaliar se os mocks atuais em `frontend/e2e/helpers.ts` devem ser
     extraidos para `fixtures/`
   - criar fixtures reutilizaveis para sessao autenticada e dados comuns
   - registrar um padrao claro para mocks de API por dominio

2. **Expandir cobertura dos fluxos criticos restantes:**
   - `e2e/produtos.spec.ts`
     - criar produto e validar listagem
     - editar produto e validar persistencia visual
     - desativar produto e validar comportamento esperado
   - `e2e/orcamentos.spec.ts`
     - criar orcamento com itens
     - converter orcamento em venda, se o fluxo estiver disponivel
     - validar cancelamento ou estado final equivalente
   - `e2e/importar-nota.spec.ts`
     - upload/processamento de XML valido
     - validacao de erro para arquivo invalido
     - se houver modal de duplicatas envolvido, cobrir o fluxo principal

3. **Estabilizar execucao em CI:**
   - revisar a intermitencia observada no smoke de `login` e `dashboard`
   - decidir se `workers: 1` deve ser adotado explicitamente na config
   - manter retries, screenshot, video e trace alinhados ao nivel de confianca
     desejado

4. **Documentar uso da suite E2E:**
   - atualizar `frontend/README.md` com pre-requisitos e comandos
   - descrever como rodar localmente, como abrir relatorio e como interpretar
     falhas comuns

### Criterio de aceite

- suite E2E mantida em `frontend/e2e/` com cobrertura dos fluxos:
  login, dashboard, PDV, vendas, produtos, orcamentos e importacao de nota
- comandos `test:e2e` e `test:ui` documentados e funcionais
- configuracao Playwright com evidencias de falha habilitadas
- README do frontend atualizado com instrucoes objetivas de execucao
- smoke CI executando de forma previsivel ou, no minimo, com intermitencias
  conhecidas documentadas

### Branch sugerida

`test/e2e-playwright-fluxos-criticos`
