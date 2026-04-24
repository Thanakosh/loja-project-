---
task_id: TASK-052
title: "E2E integrado de Estoque operacional e alertas do Dashboard"
status: pendente
priority: media
agent_chat_executable: "sim"
depends_on: ["TASK-040"]
---

## Objetivo

Adicionar cobertura E2E integrada real para a tela de Estoque e para os alertas
de estoque baixo no Dashboard, usando frontend, backend e PostgreSQL reais.

## Contexto

O projeto ja possui cobertura importante relacionada a estoque:

- `backend/tests/test_estoque_v2.py` cobre as regras de transacao, consulta,
  historico, estoque insuficiente e entrada em lote.
- `frontend/e2e/produtos.integration.spec.ts` valida estoque inicial ao criar
  produto pela UI.
- `frontend/e2e/pdv.integration.spec.ts` valida baixa real de estoque apos venda.
- `frontend/e2e/orcamentos.integration.spec.ts` valida baixa ou preservacao de
  estoque ao converter/cancelar orcamento.
- `frontend/e2e/importar-nota.integration.spec.ts` valida criacao e soma de
  estoque ao importar XML.

A lacuna restante e mais especifica: nao ha um spec integrado dedicado para a
tela `/estoque`, nem um teste de Dashboard com alertas vindos do backend real.
O teste atual de Dashboard ainda usa mock de API.

## Escopo

### Frontend/E2E

1. Criar `frontend/e2e/estoque.integration.spec.ts`.
2. Usar fixtures/helpers integrados existentes sempre que possivel:
   - `createSeededUser`
   - `createSeededProduct`
   - `loginThroughUi`
   - `fetchProductStock`
3. Fluxo da tela de Estoque:
   - fazer login pela UI
   - abrir `/#/estoque`
   - localizar produto seedado na tabela de saldo atual
   - registrar movimentacao de entrada pela UI
   - validar atualizacao do saldo no backend real
   - abrir Kardex e validar a movimentacao registrada
   - registrar movimentacao de saida pela UI
   - validar novo saldo no backend real
4. Fluxo de alerta no Dashboard:
   - preparar produto com estoque abaixo do minimo
   - abrir `/#/dashboard`
   - validar card "Alertas de Estoque" com contador real
   - validar listagem "Produtos com Estoque Baixo"
   - validar acao "Ver Estoque" navegando para `/#/estoque`

### Ajustes permitidos

- Adicionar pequenos helpers em `frontend/e2e/integration-helpers.ts` se isso
  reduzir duplicacao entre specs.
- Ajustar seletores acessiveis da tela de Estoque apenas se necessario para
  tornar o fluxo E2E estavel.

## Regras para implementacao

- Nao usar mocks no spec integrado.
- Nao duplicar regra de negocio no frontend.
- O backend continua sendo a fonte da verdade para saldo, historico e alertas.
- Manter o runner integrado com `workers: 1`.
- Evitar dependencias entre testes por estado global; cada teste deve preparar
  seus dados de forma deterministica.

## Criterios de aceite

- Existe `frontend/e2e/estoque.integration.spec.ts`.
- O teste registra entrada e saida pela tela `/estoque`.
- O saldo final e validado no backend real via API.
- O Kardex exibe a movimentacao registrada.
- O Dashboard exibe alerta de estoque baixo vindo do backend real.
- O botao "Ver Estoque" no Dashboard navega corretamente para a tela de Estoque.
- `npm run test:e2e:integrated -- estoque.integration.spec.ts` passa localmente.

## Testes esperados

1. `npm run test:e2e:integrated -- estoque.integration.spec.ts`
2. Quando houver tempo de validacao maior:
   `npm run test:e2e:integrated`

## Fora de escopo

- Alterar regras de estoque no backend.
- Reescrever a tela de Estoque.
- Criar novos endpoints.
- Testar relatorios de estoque baixo em PDF.

## Branch sugerida

`test/e2e-estoque-dashboard-integrado`
